/**
 * materials.js — Study materials bulletin board
 *
 * Storage structure in GitHub repo:
 *   weeks/
 *     _index.json              ← master index of all posts
 *     week-01/
 *       {post-id}/
 *         meta.json            ← title, author, date, category, description
 *         study-note.md        ← uploaded file(s)
 *         diagram.png
 *     general/
 *       {post-id}/
 *         meta.json
 *         reference.pdf
 */

let materialFiles = []; // files staged for upload
let allPosts = [];       // loaded from _index.json
let currentFilter = 'all';

const ALLOWED_EXTENSIONS = ['md', 'pdf', 'py', 'tf', 'json', 'yaml', 'yml', 'png', 'jpg', 'jpeg', 'txt', 'csv', 'hcl', 'ipynb'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

const CATEGORY_LABELS = {
  note: { label: 'Study Note', color: 'var(--primary)', bg: 'var(--primary-light)' },
  reference: { label: 'Reference', color: '#087f5b', bg: 'var(--green-light)' },
  presentation: { label: 'Presentation', color: 'var(--purple)', bg: '#ede9fe' },
  code: { label: 'Code', color: '#e67700', bg: 'var(--orange-light)' },
  other: { label: 'Other', color: 'var(--text-secondary)', bg: 'var(--bg)' },
};

const FILE_ICONS = {
  md: { icon: 'M', bg: '#dbeafe', color: '#1d4ed8' },
  pdf: { icon: 'P', bg: '#fce7f3', color: '#be185d' },
  py: { icon: 'Py', bg: '#fef3c7', color: '#b45309' },
  tf: { icon: 'TF', bg: '#ede9fe', color: '#7950f2' },
  json: { icon: '{ }', bg: '#e6fcf5', color: '#087f5b' },
  yaml: { icon: 'Y', bg: '#fff9db', color: '#e67700' },
  yml: { icon: 'Y', bg: '#fff9db', color: '#e67700' },
  png: { icon: 'IMG', bg: '#fce7f3', color: '#be185d' },
  jpg: { icon: 'IMG', bg: '#fce7f3', color: '#be185d' },
  jpeg: { icon: 'IMG', bg: '#fce7f3', color: '#be185d' },
  txt: { icon: 'T', bg: '#f5f6fa', color: '#5f6577' },
  csv: { icon: 'CSV', bg: '#e6fcf5', color: '#087f5b' },
  hcl: { icon: 'HCL', bg: '#ede9fe', color: '#7950f2' },
  ipynb: { icon: 'NB', bg: '#fef3c7', color: '#b45309' },
};

// ══════════════════════════════════════
// Init
// ══════════════════════════════════════

document.addEventListener('DOMContentLoaded', async () => {
  await APP.init();

  if (!APP.isLoggedIn()) {
    window.location.href = 'index.html';
    return;
  }

  setupDropZone();
  await loadMaterials();
});

async function loadMaterials() {
  try {
    allPosts = await loadIndex();
    buildWeekTabs();
    renderPosts();

    document.getElementById('materials-loading').style.display = 'none';
    document.getElementById('materials-content').style.display = 'block';
  } catch (e) {
    document.getElementById('materials-loading').innerHTML = `
      <div class="empty-state">
        <h3>No materials yet</h3>
        <p>Be the first to upload study materials!</p>
        <button onclick="showUploadModal()" class="btn btn-primary" style="margin-top:16px;">Upload Material</button>
      </div>
    `;
  }
}

async function loadIndex() {
  try {
    return await APP.getJSON('weeks/_index.json');
  } catch {
    return [];
  }
}

// ══════════════════════════════════════
// Rendering
// ══════════════════════════════════════

function buildWeekTabs() {
  const weeks = [...new Set(allPosts.map(p => p.week))].sort((a, b) => {
    if (a === 'general') return 1;
    if (b === 'general') return -1;
    return parseInt(a) - parseInt(b);
  });

  const tabsEl = document.getElementById('week-filter-tabs');
  let html = `
    <div class="tab active" data-week="all" onclick="filterWeek('all', this)">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
      All <span class="tab-count">(${allPosts.length})</span>
    </div>
  `;

  for (const w of weeks) {
    const count = allPosts.filter(p => p.week === w).length;
    const label = w === 'general' ? 'General' : `Week ${w}`;
    html += `
      <div class="tab" data-week="${w}" onclick="filterWeek('${w}', this)">
        ${label} <span class="tab-count">(${count})</span>
      </div>
    `;
  }

  tabsEl.innerHTML = html;
}

function filterWeek(week, tabEl) {
  currentFilter = week;
  document.querySelectorAll('#week-filter-tabs .tab').forEach(t => t.classList.remove('active'));
  if (tabEl) tabEl.classList.add('active');
  renderPosts();
}

function renderPosts() {
  const listEl = document.getElementById('materials-list');
  const emptyEl = document.getElementById('materials-empty');

  const filtered = currentFilter === 'all'
    ? allPosts
    : allPosts.filter(p => String(p.week) === String(currentFilter));

  if (filtered.length === 0) {
    listEl.innerHTML = '';
    emptyEl.style.display = 'block';
    return;
  }

  emptyEl.style.display = 'none';

  // Sort by date descending
  const sorted = [...filtered].sort((a, b) => (b.date || '').localeCompare(a.date || ''));

  listEl.innerHTML = sorted.map(post => {
    const cat = CATEGORY_LABELS[post.category] || CATEGORY_LABELS.other;
    const weekLabel = post.week === 'general' ? 'General' : `Week ${post.week}`;
    const fileCount = (post.files || []).length;
    const dateStr = post.date ? new Date(post.date).toLocaleDateString('ko-KR') : '';

    const fileChips = (post.files || []).slice(0, 4).map(f => {
      const ext = f.split('.').pop().toLowerCase();
      const fi = FILE_ICONS[ext] || { icon: '?', bg: '#f5f6fa', color: '#5f6577' };
      return `<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 8px;background:${fi.bg};color:${fi.color};border-radius:4px;font-size:11px;font-weight:600;">${fi.icon} ${escapeHtml(f)}</span>`;
    }).join(' ');
    const moreFiles = fileCount > 4 ? `<span style="font-size:12px;color:var(--text-muted);">+${fileCount - 4} more</span>` : '';

    return `
      <div class="card" style="margin-bottom:12px;cursor:pointer;" onclick="viewPost('${post.id}')">
        <div class="card-body" style="display:flex;gap:16px;align-items:flex-start;">
          <div style="flex:1;min-width:0;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap;">
              <span style="font-weight:700;font-size:16px;">${escapeHtml(post.title)}</span>
              <span class="badge" style="background:${cat.bg};color:${cat.color};">${cat.label}</span>
              <span class="badge badge-${post.week === 'general' ? 'admin' : 'L1'}">${weekLabel}</span>
            </div>
            ${post.description ? `<p style="font-size:14px;color:var(--text-secondary);margin-bottom:8px;line-height:1.5;">${escapeHtml(post.description)}</p>` : ''}
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
              ${fileChips} ${moreFiles}
            </div>
          </div>
          <div style="text-align:right;flex-shrink:0;min-width:100px;">
            <div style="font-size:13px;font-weight:600;color:var(--text);">@${escapeHtml(post.author)}</div>
            <div style="font-size:12px;color:var(--text-muted);margin-top:2px;">${dateStr}</div>
            <div style="font-size:12px;color:var(--text-muted);margin-top:2px;">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:middle;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg>
              ${fileCount} file${fileCount !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// ══════════════════════════════════════
// View Post
// ══════════════════════════════════════

async function viewPost(postId) {
  const post = allPosts.find(p => p.id === postId);
  if (!post) return;

  const weekDir = post.week === 'general' ? 'general' : `week-${String(post.week).padStart(2, '0')}`;
  const basePath = `weeks/${weekDir}/${postId}`;

  const cat = CATEGORY_LABELS[post.category] || CATEGORY_LABELS.other;
  const dateStr = post.date ? new Date(post.date).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' }) : '';

  let contentHtml = `
    <div style="margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid var(--border-light);">
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px;">
        <span class="badge" style="background:${cat.bg};color:${cat.color};">${cat.label}</span>
        <span style="font-size:13px;color:var(--text-muted);">by <strong>@${escapeHtml(post.author)}</strong></span>
        <span style="font-size:13px;color:var(--text-muted);">${dateStr}</span>
      </div>
      ${post.description ? `<p style="color:var(--text-secondary);line-height:1.6;">${escapeHtml(post.description)}</p>` : ''}
    </div>
  `;

  // Render each file
  for (const filename of (post.files || [])) {
    const ext = filename.split('.').pop().toLowerCase();
    const filePath = `${basePath}/${filename}`;
    const fi = FILE_ICONS[ext] || { icon: '?', bg: '#f5f6fa', color: '#5f6577' };

    contentHtml += `<div style="margin-bottom:16px;">`;
    contentHtml += `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
        <span style="display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:6px;background:${fi.bg};color:${fi.color};font-size:11px;font-weight:700;">${fi.icon}</span>
        <span style="font-weight:600;font-size:14px;">${escapeHtml(filename)}</span>
        <a href="#" onclick="downloadFile('${filePath}', '${filename}'); return false;" style="font-size:12px;margin-left:auto;">Download</a>
      </div>
    `;

    // Try to preview content
    if (['md', 'txt', 'py', 'tf', 'json', 'yaml', 'yml', 'csv', 'hcl'].includes(ext)) {
      try {
        const text = await APP.getFileContent(filePath);
        if (ext === 'md') {
          contentHtml += `<div style="padding:16px;background:var(--bg);border:1px solid var(--border-light);border-radius:var(--radius-sm);line-height:1.8;">${markdownToHtml(text)}</div>`;
        } else {
          contentHtml += `<pre style="max-height:400px;overflow:auto;font-size:13px;"><code>${escapeHtml(text)}</code></pre>`;
        }
      } catch {
        contentHtml += `<p style="color:var(--text-muted);font-size:13px;">Preview not available</p>`;
      }
    } else if (['png', 'jpg', 'jpeg'].includes(ext)) {
      if (APP.LOCAL) {
        contentHtml += `<img src="../${filePath}" style="max-width:100%;border-radius:var(--radius-sm);border:1px solid var(--border);" alt="${escapeHtml(filename)}">`;
      } else {
        contentHtml += `<p style="color:var(--text-muted);font-size:13px;">Image preview — <a href="#" onclick="downloadFile('${filePath}', '${filename}'); return false;">download to view</a></p>`;
      }
    } else {
      contentHtml += `<p style="color:var(--text-muted);font-size:13px;">Binary file — download to view</p>`;
    }

    contentHtml += `</div>`;
  }

  // Edit/Delete buttons (author or admin only)
  const username = APP.getUsername();
  if (post.author === username || APP.isAdmin()) {
    contentHtml += `
      <div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--border-light);display:flex;gap:8px;justify-content:flex-end;">
        <button onclick="editPost('${postId}')" class="btn btn-sm">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          Edit
        </button>
        <button onclick="deletePost('${postId}')" class="btn btn-sm" style="color:var(--red);border-color:var(--red);">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          Delete
        </button>
      </div>
    `;
  }

  document.getElementById('viewer-title').textContent = post.title;
  document.getElementById('viewer-content').innerHTML = contentHtml;
  document.getElementById('viewer-modal').classList.add('active');
}

async function downloadFile(path, filename) {
  try {
    if (APP.LOCAL) {
      window.open(`../${path}`, '_blank');
      return;
    }
    const data = await APP.api(`/repos/${APP.OWNER}/${APP.REPO}/contents/${path}`);

    // For large files (>1MB), GitHub returns download_url instead of content
    if (data.download_url) {
      const resp = await fetch(data.download_url);
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } else if (data.content) {
      // Small files: base64 decode
      const raw = atob(data.content.replace(/\n/g, ''));
      const blob = new Blob([Uint8Array.from(raw, c => c.charCodeAt(0))]);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    }
  } catch (e) {
    alert('Download failed: ' + e.message);
  }
}

function hideViewerModal() {
  document.getElementById('viewer-modal').classList.remove('active');
}

// ══════════════════════════════════════
// Edit / Delete
// ══════════════════════════════════════

async function editPost(postId) {
  const post = allPosts.find(p => p.id === postId);
  if (!post) return;

  hideViewerModal();

  // Pre-fill the upload modal with existing data
  materialFiles = [];
  document.getElementById('mat-title').value = post.title || '';
  document.getElementById('mat-week').value = post.week || 'general';
  document.getElementById('mat-category').value = post.category || 'note';
  document.getElementById('mat-description').value = post.description || '';
  document.getElementById('mat-file-list').innerHTML = '';
  document.getElementById('upload-error').textContent = '';

  // Change button to "Save Changes"
  const btn = document.getElementById('upload-btn');
  btn.disabled = false;
  btn.innerHTML = `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
    Save Changes
  `;

  // Store edit state
  window._editingPostId = postId;

  document.getElementById('upload-modal').classList.add('active');
}

async function deletePost(postId) {
  const post = allPosts.find(p => p.id === postId);
  if (!post) return;

  if (!confirm(`"${post.title}" 을(를) 삭제하시겠습니까?`)) return;

  try {
    const weekDir = post.week === 'general' ? 'general' : `week-${String(post.week).padStart(2, '0')}`;
    const basePath = `weeks/${weekDir}/${postId}`;

    if (!APP.LOCAL) {
      // Delete all files in the post directory
      const allFiles = [...(post.files || []), 'meta.json'];
      for (const filename of allFiles) {
        try {
          const fileData = await APP.api(`/repos/${APP.OWNER}/${APP.REPO}/contents/${basePath}/${filename}`);
          await APP.api(`/repos/${APP.OWNER}/${APP.REPO}/contents/${basePath}/${filename}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message: `[weeks] Delete "${post.title}" — ${filename}`,
              sha: fileData.sha,
            }),
          });
        } catch {}
      }

      // Update index
      const idxResp = await APP.api(`/repos/${APP.OWNER}/${APP.REPO}/contents/weeks/_index.json`);
      const index = JSON.parse(decodeURIComponent(escape(atob(idxResp.content))));
      const newIndex = index.filter(p => p.id !== postId);

      await APP.api(`/repos/${APP.OWNER}/${APP.REPO}/contents/weeks/_index.json`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: `[weeks] Delete "${post.title}" from index`,
          content: btoa(unescape(encodeURIComponent(JSON.stringify(newIndex, null, 2)))),
          sha: idxResp.sha,
        }),
      });
    }

    // Update local state
    allPosts = allPosts.filter(p => p.id !== postId);
    buildWeekTabs();
    renderPosts();
    hideViewerModal();
    alert('Deleted.');

  } catch (e) {
    alert('Delete failed: ' + e.message);
  }
}

// ══════════════════════════════════════
// Upload
// ══════════════════════════════════════

function showUploadModal() {
  materialFiles = [];
  document.getElementById('mat-title').value = '';
  document.getElementById('mat-week').value = 'general';
  document.getElementById('mat-category').value = 'note';
  document.getElementById('mat-description').value = '';
  document.getElementById('mat-file-list').innerHTML = '';
  document.getElementById('upload-error').textContent = '';
  document.getElementById('upload-btn').disabled = false;
  document.getElementById('upload-btn').innerHTML = `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
    Upload
  `;
  window._editingPostId = null; // Reset edit state for new uploads
  document.getElementById('upload-modal').classList.add('active');
}

function hideUploadModal() {
  window._editingPostId = null;
  document.getElementById('upload-modal').classList.remove('active');
}

function setupDropZone() {
  const zone = document.getElementById('upload-drop-zone');
  if (!zone) return;

  zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => { zone.classList.remove('dragover'); });
  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('dragover');
    Array.from(e.dataTransfer.files).forEach(processMaterialFile);
  });
}

function handleMaterialFiles(input) {
  Array.from(input.files).forEach(processMaterialFile);
  input.value = '';
}

function processMaterialFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    document.getElementById('upload-error').textContent = `Unsupported file: .${ext}`;
    return;
  }
  if (file.size > MAX_FILE_SIZE) {
    document.getElementById('upload-error').textContent = `File too large: ${file.name} (max 10MB)`;
    return;
  }
  if (materialFiles.find(f => f.name === file.name)) {
    document.getElementById('upload-error').textContent = `Duplicate: ${file.name}`;
    return;
  }

  document.getElementById('upload-error').textContent = '';

  const reader = new FileReader();
  reader.onload = () => {
    // Store as base64 for GitHub API
    const base64 = reader.result.split(',')[1];
    materialFiles.push({ name: file.name, size: file.size, base64 });
    renderMaterialFileList();
  };
  reader.readAsDataURL(file);
}

function removeMaterialFile(index) {
  materialFiles.splice(index, 1);
  renderMaterialFileList();
}

function renderMaterialFileList() {
  const container = document.getElementById('mat-file-list');
  if (!materialFiles.length) { container.innerHTML = ''; return; }

  container.innerHTML = materialFiles.map((f, i) => {
    const ext = f.name.split('.').pop().toLowerCase();
    const fi = FILE_ICONS[ext] || { icon: '?', bg: '#f5f6fa', color: '#5f6577' };
    const sizeStr = f.size < 1024 ? `${f.size} B` : f.size < 1024 * 1024 ? `${(f.size / 1024).toFixed(1)} KB` : `${(f.size / (1024 * 1024)).toFixed(1)} MB`;
    return `
      <div class="file-item">
        <div class="file-icon" style="background:${fi.bg};color:${fi.color};font-size:11px;font-weight:700;">${fi.icon}</div>
        <div class="file-info">
          <div class="file-name">${escapeHtml(f.name)}</div>
          <div class="file-size">${sizeStr}</div>
        </div>
        <button class="file-remove" onclick="removeMaterialFile(${i})">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
    `;
  }).join('');
}

async function uploadMaterial() {
  const errorEl = document.getElementById('upload-error');
  const btn = document.getElementById('upload-btn');

  const title = document.getElementById('mat-title').value.trim();
  const week = document.getElementById('mat-week').value;
  const category = document.getElementById('mat-category').value;
  const description = document.getElementById('mat-description').value.trim();

  if (!title) { errorEl.textContent = 'Title is required'; return; }
  // Files are optional — text-only posts are allowed

  btn.disabled = true;
  btn.innerHTML = '<div class="spinner" style="width:16px;height:16px;margin:0;border-width:2px;"></div> Uploading...';
  errorEl.textContent = '';

  try {
    const username = APP.getUsername();
    const now = new Date().toISOString();
    const isEdit = !!window._editingPostId;
    const oldPost = isEdit ? allPosts.find(p => p.id === window._editingPostId) : null;
    const postId = isEdit ? window._editingPostId : `${Date.now()}-${username}`;
    const weekDir = isEdit && oldPost
      ? (oldPost.week === 'general' ? 'general' : `week-${String(oldPost.week).padStart(2, '0')}`)
      : (week === 'general' ? 'general' : `week-${String(parseInt(week)).padStart(2, '0')}`);
    const basePath = `weeks/${weekDir}/${postId}`;

    // If no files but has description, save description as content.md
    const fileNames = materialFiles.map(f => f.name);
    if (materialFiles.length === 0 && description) {
      fileNames.push('content.md');
    }

    // Build meta
    const meta = {
      id: postId,
      title,
      author: username,
      date: now,
      week,
      category,
      description,
      files: fileNames,
    };

    if (!APP.LOCAL) {
      const commitPrefix = isEdit ? 'Edit' : 'Add';

      // Helper: get existing file sha for updates
      async function getFileSha(path) {
        try {
          const data = await APP.api(`/repos/${APP.OWNER}/${APP.REPO}/contents/${path}`);
          return data.sha;
        } catch { return null; }
      }

      // 0. If text-only post, save description as content.md
      if (materialFiles.length === 0 && description) {
        const mdContent = btoa(unescape(encodeURIComponent(description)));
        const sha = await getFileSha(`${basePath}/content.md`);
        const payload = {
          message: `[weeks] ${commitPrefix} content.md for "${title}" by ${username}`,
          content: mdContent,
        };
        if (sha) payload.sha = sha;
        await APP.api(`/repos/${APP.OWNER}/${APP.REPO}/contents/${basePath}/content.md`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      }

      // 1. Upload each new file
      for (const file of materialFiles) {
        const sha = await getFileSha(`${basePath}/${file.name}`);
        const payload = {
          message: `[weeks] ${commitPrefix} ${file.name} by ${username}`,
          content: file.base64,
        };
        if (sha) payload.sha = sha;
        await APP.api(`/repos/${APP.OWNER}/${APP.REPO}/contents/${basePath}/${file.name}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      }

      // 2. Upload meta.json
      const metaSha = await getFileSha(`${basePath}/meta.json`);
      const metaContent = btoa(unescape(encodeURIComponent(JSON.stringify(meta, null, 2))));
      const metaPayload = {
        message: `[weeks] ${commitPrefix} "${title}" by ${username}`,
        content: metaContent,
      };
      if (metaSha) metaPayload.sha = metaSha;
      await APP.api(`/repos/${APP.OWNER}/${APP.REPO}/contents/${basePath}/meta.json`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(metaPayload),
      });

      // 3. Update _index.json
      const newIndex = isEdit
        ? allPosts.map(p => p.id === postId ? meta : p)
        : [...allPosts, meta];
      const indexContent = btoa(unescape(encodeURIComponent(JSON.stringify(newIndex, null, 2))));

      // Get existing sha if exists
      let indexSha = null;
      try {
        const existing = await APP.api(`/repos/${APP.OWNER}/${APP.REPO}/contents/weeks/_index.json`);
        indexSha = existing.sha;
      } catch {}

      const indexPayload = {
        message: `[weeks] Update index: add "${title}"`,
        content: indexContent,
      };
      if (indexSha) indexPayload.sha = indexSha;

      await APP.api(`/repos/${APP.OWNER}/${APP.REPO}/contents/weeks/_index.json`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(indexPayload),
      });
    }

    // Update local state
    if (isEdit) {
      const idx = allPosts.findIndex(p => p.id === postId);
      if (idx >= 0) allPosts[idx] = meta;
    } else {
      allPosts.push(meta);
    }
    buildWeekTabs();
    renderPosts();
    hideUploadModal();

  } catch (e) {
    errorEl.textContent = `Upload failed: ${e.message}`;
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
      Upload
    `;
  }
}

// ══════════════════════════════════════
// Utils
// ══════════════════════════════════════

function markdownToHtml(md) {
  return md
    .replace(/^### (.+)$/gm, '<h4 style="margin:16px 0 8px;font-size:15px;">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 style="margin:20px 0 10px;font-size:17px;">$1</h3>')
    .replace(/^# (.+)$/gm, '<h2 style="margin:24px 0 12px;font-size:20px;">$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/^- (.+)$/gm, '<li style="margin-left:20px;margin-bottom:4px;">$1</li>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>');
}
