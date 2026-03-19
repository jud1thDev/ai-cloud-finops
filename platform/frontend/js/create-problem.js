/**
 * create-problem.js — Community problem creation
 *
 * Storage in GitHub:
 *   weeks/week-XX/community/{problem-id}/
 *     meta.json         ← problem metadata + answer (author/admin only)
 *     README.md          ← problem description (visible to all)
 *     main.tf            ← terraform code (visible to all)
 *     metrics.json       ← optional additional files
 *     ...
 *
 *   weeks/_community_index.json  ← index of all community problems
 */

let problemFiles = [];

document.addEventListener('DOMContentLoaded', async () => {
  await APP.init();

  if (!APP.isLoggedIn()) {
    window.location.href = 'index.html';
    return;
  }

  setupDropZone();
});

// ── File Upload ──

function setupDropZone() {
  const zone = document.getElementById('cp-drop-zone');
  if (!zone) return;

  zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => { zone.classList.remove('dragover'); });
  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('dragover');
    Array.from(e.dataTransfer.files).forEach(addProblemFile);
  });
}

function handleProblemFiles(input) {
  Array.from(input.files).forEach(addProblemFile);
  input.value = '';
}

function addProblemFile(file) {
  const allowed = ['json', 'csv', 'yaml', 'yml', 'txt'];
  const ext = file.name.split('.').pop().toLowerCase();
  if (!allowed.includes(ext)) {
    showError(`Unsupported: .${ext}`);
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showError(`Too large: ${file.name}`);
    return;
  }
  if (problemFiles.find(f => f.name === file.name)) return;

  const reader = new FileReader();
  reader.onload = () => {
    problemFiles.push({ name: file.name, size: file.size, base64: reader.result.split(',')[1] });
    renderFileList();
  };
  reader.readAsDataURL(file);
}

function removeProblemFile(index) {
  problemFiles.splice(index, 1);
  renderFileList();
}

function renderFileList() {
  const container = document.getElementById('cp-file-list');
  if (!problemFiles.length) { container.innerHTML = ''; return; }

  container.innerHTML = problemFiles.map((f, i) => {
    const sizeStr = f.size < 1024 ? `${f.size} B` : `${(f.size / 1024).toFixed(1)} KB`;
    return `
      <div class="file-item">
        <div class="file-icon" style="background:#e6fcf5;color:#087f5b;font-size:11px;font-weight:700;">
          ${f.name.split('.').pop().toUpperCase()}
        </div>
        <div class="file-info">
          <div class="file-name">${escapeHtml(f.name)}</div>
          <div class="file-size">${sizeStr}</div>
        </div>
        <button class="file-remove" onclick="removeProblemFile(${i})">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
    `;
  }).join('');
}

// ── Publish ──

async function publishProblem() {
  const errorEl = document.getElementById('cp-error');
  const successEl = document.getElementById('cp-success');
  errorEl.style.display = 'none';
  successEl.style.display = 'none';

  // Gather form data
  const title = document.getElementById('cp-title').value.trim();
  const week = document.getElementById('cp-week').value;
  const level = document.getElementById('cp-level').value;
  const category = document.getElementById('cp-category').value;
  const services = document.getElementById('cp-services').value.trim();
  const savings = document.getElementById('cp-savings').value.trim();
  const description = document.getElementById('cp-description').value.trim();
  const terraform = document.getElementById('cp-terraform').value.trim();

  // Answer fields
  const problemSummary = document.getElementById('cp-problem-summary').value.trim();
  const rootCause = document.getElementById('cp-root-cause').value.trim();
  const recommendation = document.getElementById('cp-recommendation').value.trim();
  const severity = document.getElementById('cp-severity').value;
  const problemResources = document.getElementById('cp-problem-resources').value.trim();

  // Validate
  const errors = [];
  if (!title) errors.push('Title is required');
  if (!description) errors.push('Description is required');
  if (!terraform) errors.push('Terraform code is required');
  if (!problemSummary) errors.push('Answer: Problem Summary is required');
  if (!recommendation) errors.push('Answer: Recommendation is required');
  if (!savings) errors.push('Monthly Waste is required');

  if (errors.length > 0) {
    showError(errors.join(', '));
    return;
  }

  const btn = document.getElementById('publish-btn');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner" style="width:16px;height:16px;margin:0;border-width:2px;"></div> Publishing...';

  try {
    const username = APP.getUsername();
    const now = new Date().toISOString();
    const problemId = `${Date.now()}-${username}`;
    const weekStr = `week-${String(parseInt(week)).padStart(2, '0')}`;
    const basePath = `weeks/${weekStr}/community/${problemId}`;

    // Build meta.json (includes answer — only author/admin should view)
    const meta = {
      id: problemId,
      title,
      author: username,
      date: now,
      week,
      level,
      category,
      services: services.split(',').map(s => s.trim()).filter(Boolean),
      monthly_waste_usd: parseFloat(savings) || 0,
      answer: {
        severity,
        problem_summary: problemSummary,
        root_cause: rootCause,
        recommendation,
        problem_resources: problemResources.split(',').map(s => s.trim()).filter(Boolean),
      },
      files: ['README.md', 'main.tf', ...problemFiles.map(f => f.name)],
    };

    if (!APP.LOCAL) {
      // 1. Upload README.md
      await commitFile(`${basePath}/README.md`, description,
        `[community] Add problem "${title}" by ${username}`);

      // 2. Upload main.tf
      await commitFile(`${basePath}/main.tf`, terraform,
        `[community] Add main.tf for "${title}"`);

      // 3. Upload meta.json
      await commitFile(`${basePath}/meta.json`, JSON.stringify(meta, null, 2),
        `[community] Add meta.json for "${title}"`);

      // 4. Upload additional files
      for (const file of problemFiles) {
        await APP.api(`/repos/${APP.OWNER}/${APP.REPO}/contents/${basePath}/${file.name}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: `[community] Add ${file.name} for "${title}"`,
            content: file.base64,
          }),
        });
      }

      // 5. Update community index
      await updateCommunityIndex(meta);
    }

    successEl.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
      <div>
        Problem published!
        <a href="community-problems.html" style="margin-left:8px;">View Community Problems &rarr;</a>
      </div>
    `;
    successEl.style.display = 'flex';

    // Disable form
    document.querySelectorAll('input, textarea, select').forEach(el => el.disabled = true);
    btn.textContent = 'Published';

  } catch (e) {
    showError(`Publish failed: ${e.message}`);
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
      Publish Problem
    `;
  }
}

async function commitFile(path, content, message) {
  const encoded = btoa(unescape(encodeURIComponent(content)));
  await APP.api(`/repos/${APP.OWNER}/${APP.REPO}/contents/${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, content: encoded }),
  });
}

async function updateCommunityIndex(meta) {
  // Load existing index
  let index = [];
  let indexSha = null;
  try {
    const existing = await APP.api(`/repos/${APP.OWNER}/${APP.REPO}/contents/weeks/_community_index.json`);
    indexSha = existing.sha;
    index = JSON.parse(decodeURIComponent(escape(atob(existing.content))));
  } catch {}

  // Add new entry (without full answer — just summary info)
  index.push({
    id: meta.id,
    title: meta.title,
    author: meta.author,
    date: meta.date,
    week: meta.week,
    level: meta.level,
    category: meta.category,
    services: meta.services,
    monthly_waste_usd: meta.monthly_waste_usd,
  });

  const payload = {
    message: `[community] Update index: add "${meta.title}"`,
    content: btoa(unescape(encodeURIComponent(JSON.stringify(index, null, 2)))),
  };
  if (indexSha) payload.sha = indexSha;

  await APP.api(`/repos/${APP.OWNER}/${APP.REPO}/contents/weeks/_community_index.json`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

function showError(msg) {
  const el = document.getElementById('cp-error');
  el.textContent = msg;
  el.style.display = 'flex';
}
