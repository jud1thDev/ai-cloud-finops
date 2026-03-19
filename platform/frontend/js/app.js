/**
 * app.js — GitHub API client, auth, and shared utilities
 */

const APP = {
  // Will be set from group.yaml or defaults
  REPO: '',
  OWNER: '',
  API_BASE: 'https://api.github.com',

  // Local dev mode: serves files from project root instead of GitHub API
  LOCAL: location.hostname === 'localhost' || location.hostname === '127.0.0.1',
  LOCAL_BASE: '../..', // relative path from platform/frontend/ to project root

  /** Get stored GitHub token */
  getToken() {
    return localStorage.getItem('gh_token') || '';
  },

  /** Save GitHub token */
  setToken(token) {
    localStorage.setItem('gh_token', token);
  },

  /** Get current username (cached after first fetch) */
  getUsername() {
    if (this.LOCAL) return localStorage.getItem('gh_username') || 'leejiseok';
    return localStorage.getItem('gh_username') || '';
  },

  setUsername(username) {
    localStorage.setItem('gh_username', username);
  },

  /** Check if user is logged in */
  isLoggedIn() {
    if (this.LOCAL) return true; // auto-login in local mode
    return !!this.getToken() && !!this.getUsername();
  },

  /** Logout */
  logout() {
    localStorage.removeItem('gh_token');
    localStorage.removeItem('gh_username');
    localStorage.removeItem('gh_is_admin');
    window.location.href = 'index.html';
  },

  /** Check if current user is admin */
  isAdmin() {
    if (this.LOCAL) return true;
    return localStorage.getItem('gh_is_admin') === 'true';
  },

  /**
   * Make authenticated GitHub API request
   */
  async api(endpoint, options = {}) {
    const token = this.getToken();
    const headers = {
      'Accept': 'application/vnd.github.v3+json',
      ...options.headers,
    };
    if (token) {
      headers['Authorization'] = `token ${token}`;
    }

    const url = endpoint.startsWith('http') ? endpoint : `${this.API_BASE}${endpoint}`;
    const resp = await fetch(url, { ...options, headers });

    if (!resp.ok) {
      const body = await resp.text();
      throw new Error(`GitHub API ${resp.status}: ${body}`);
    }

    if (resp.status === 204) return null;
    return resp.json();
  },

  /**
   * Get file content from repo (base64 decoded)
   */
  async getFileContent(path) {
    if (this.LOCAL) {
      const resp = await fetch(`${this.LOCAL_BASE}/${path}`);
      if (!resp.ok) throw new Error(`Local file not found: ${path}`);
      return resp.text();
    }
    const data = await this.api(`/repos/${this.OWNER}/${this.REPO}/contents/${path}`);
    if (data.encoding === 'base64') {
      return decodeURIComponent(escape(atob(data.content)));
    }
    return data.content;
  },

  /**
   * Get JSON file from repo
   */
  async getJSON(path) {
    if (this.LOCAL) {
      const resp = await fetch(`${this.LOCAL_BASE}/${path}`);
      if (!resp.ok) throw new Error(`Local file not found: ${path}`);
      return resp.json();
    }
    const content = await this.getFileContent(path);
    return JSON.parse(content);
  },

  /**
   * Get YAML file from repo (simple parser for our use case)
   */
  async getYAML(path) {
    const content = await this.getFileContent(path);
    return parseSimpleYAML(content);
  },

  /**
   * List directory contents in repo
   */
  async listDir(path) {
    if (this.LOCAL) {
      // Local mode: use a pre-generated index or return known structure
      return this._localListDir(path);
    }
    try {
      return await this.api(`/repos/${this.OWNER}/${this.REPO}/contents/${path}`);
    } catch {
      return [];
    }
  },

  /**
   * Local mode directory listing (reads from _index.json files)
   */
  async _localListDir(path) {
    try {
      const resp = await fetch(`${this.LOCAL_BASE}/${path}/_index.json`);
      if (resp.ok) return resp.json();
    } catch {}
    return [];
  },

  /**
   * Verify token and fetch username
   */
  async login(token) {
    this.setToken(token);
    try {
      const user = await this.api('/user');
      this.setUsername(user.login);

      // Check admin status from group.yaml
      try {
        const groupYaml = await this.getFileContent('platform/config/group.yaml');
        const isAdmin = groupYaml.includes(user.login) &&
          groupYaml.split('admins:')[1]?.includes(user.login);
        localStorage.setItem('gh_is_admin', isAdmin ? 'true' : 'false');
      } catch {
        localStorage.setItem('gh_is_admin', 'false');
      }

      return user;
    } catch (e) {
      this.logout();
      throw e;
    }
  },

  /**
   * Create a GitHub Issue (for submissions)
   */
  async createIssue(title, body, labels = []) {
    return this.api(`/repos/${this.OWNER}/${this.REPO}/issues`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, body, labels }),
    });
  },

  /**
   * Trigger a workflow dispatch
   */
  async triggerWorkflow(workflowFile, inputs = {}) {
    return this.api(
      `/repos/${this.OWNER}/${this.REPO}/actions/workflows/${workflowFile}/dispatches`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ref: 'main', inputs }),
      }
    );
  },

  /**
   * Initialize app — load repo config
   */
  async init() {
    if (this.LOCAL) {
      console.log('[LOCAL MODE] Serving files from project root');
      this.updateAuthUI();
      return;
    }

    // Try to load from group.yaml, fall back to defaults
    try {
      const content = await this.getFileContent('platform/config/group.yaml');
      const repoMatch = content.match(/repo:\s*"?([^"\n]+)"?/);
      if (repoMatch) {
        const [owner, repo] = repoMatch[1].split('/');
        this.OWNER = owner;
        this.REPO = repo;
      }
    } catch {
      // Use defaults from URL or hardcoded
      this.OWNER = 'cloud-club';
      this.REPO = '09th-ai-cloud-finops';
    }

    this.updateAuthUI();
  },

  /** Update sidebar footer with user info */
  updateAuthUI() {
    const authArea = document.getElementById('auth-area');
    if (!authArea) return;

    if (this.isLoggedIn()) {
      const username = this.getUsername();
      const initial = username.charAt(0).toUpperCase();
      authArea.innerHTML = `
        <div class="sidebar-user">
          <div class="avatar">${initial}</div>
          <div class="user-info">
            <div class="user-name">@${escapeHtml(username)}</div>
            <div class="user-role">${this.isAdmin() ? 'Admin' : 'Member'}</div>
          </div>
          <button onclick="APP.logout()" class="btn btn-ghost btn-sm" title="Logout" style="padding:4px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          </button>
        </div>
      `;
    } else {
      authArea.innerHTML = `
        <button onclick="showLoginModal()" class="btn btn-primary" style="width:100%;">Login</button>
      `;
    }
  }
};

// ── Simple YAML parser (handles our flat configs) ──

function parseSimpleYAML(text) {
  const result = {};
  let currentKey = null;
  let currentList = null;

  for (const line of text.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;

    // List item
    if (trimmed.startsWith('- ')) {
      if (currentList !== null) {
        const val = trimmed.slice(2).trim().replace(/^["']|["']$/g, '');
        // Check if it's a key-value object
        if (val.includes(':')) {
          const obj = {};
          // Parse inline mapping
          const parts = trimmed.slice(2).trim();
          for (const part of parts.split(/,\s*/)) {
            const [k, ...v] = part.split(':');
            if (k && v.length) {
              obj[k.trim()] = v.join(':').trim().replace(/^["']|["']$/g, '');
            }
          }
          if (Object.keys(obj).length > 0) {
            result[currentKey].push(obj);
          }
        } else {
          result[currentKey].push(val);
        }
      }
      continue;
    }

    // Key: value
    const match = trimmed.match(/^(\w[\w_]*)\s*:\s*(.*)/);
    if (match) {
      const key = match[1];
      const val = match[2].trim().replace(/^["']|["']$/g, '');

      if (!val) {
        // Start of list or nested object
        result[key] = [];
        currentKey = key;
        currentList = true;
      } else {
        result[key] = val === 'null' ? null : val === 'true' ? true : val === 'false' ? false :
          /^\d+$/.test(val) ? parseInt(val) : /^\d+\.\d+$/.test(val) ? parseFloat(val) : val;
        currentList = null;
      }
    }
  }
  return result;
}

// ── Utility functions ──

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function showLoginModal() {
  const modal = document.getElementById('login-modal');
  if (modal) modal.classList.add('active');
}

function hideLoginModal() {
  const modal = document.getElementById('login-modal');
  if (modal) modal.classList.remove('active');
}

async function handleLogin() {
  const tokenInput = document.getElementById('token-input');
  const errorEl = document.getElementById('login-error');
  const token = tokenInput.value.trim();

  if (!token) {
    errorEl.textContent = 'Token을 입력하세요.';
    return;
  }

  errorEl.textContent = '';
  try {
    const user = await APP.login(token);
    hideLoginModal();
    window.location.reload();
  } catch (e) {
    errorEl.textContent = '유효하지 않은 토큰입니다.';
  }
}

/** Format date for display */
function formatDate(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' });
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => APP.init());
