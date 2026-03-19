/**
 * submit.js — Answer submission with Terraform code + file uploads
 */

let uploadedFiles = []; // { name, size, type, content (base64 or text) }

document.addEventListener('DOMContentLoaded', async () => {
  await APP.init();

  if (!APP.isLoggedIn()) {
    showLoginModal();
    return;
  }

  // Pre-fill from URL params
  const params = new URLSearchParams(window.location.search);
  if (params.get('week')) document.getElementById('sub-week').value = params.get('week');
  if (params.get('scenario')) document.getElementById('sub-scenario').value = params.get('scenario');

  // Setup drag & drop
  setupDropZone();
  updateSummary();
});

// ── Step Navigation ──

function showStep(step) {
  document.querySelectorAll('.step-panel').forEach(p => p.style.display = 'none');
  document.querySelectorAll('#step-tabs .tab').forEach(t => t.classList.remove('active'));

  document.getElementById(`step-${step}`).style.display = 'block';
  // Find and activate the correct tab
  document.querySelectorAll('#step-tabs .tab').forEach(t => {
    if (t.textContent.toLowerCase().includes(step.substring(0, 4))) t.classList.add('active');
  });
}

// ── File Upload ──

function setupDropZone() {
  const zone = document.getElementById('drop-zone');
  if (!zone) return;

  zone.addEventListener('dragover', (e) => {
    e.preventDefault();
    zone.classList.add('dragover');
  });

  zone.addEventListener('dragleave', () => {
    zone.classList.remove('dragover');
  });

  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('dragover');
    const files = Array.from(e.dataTransfer.files);
    files.forEach(processFile);
  });
}

function handleFileSelect(input) {
  const files = Array.from(input.files);
  files.forEach(processFile);
  input.value = '';
}

function processFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  const allowed = ['md', 'markdown', 'pdf'];

  if (!allowed.includes(ext)) {
    showError(`Unsupported file type: .${ext}. Only .md and .pdf are allowed.`);
    return;
  }

  if (file.size > 5 * 1024 * 1024) {
    showError(`File too large: ${file.name} (max 5MB)`);
    return;
  }

  const reader = new FileReader();

  if (ext === 'pdf') {
    reader.onload = () => {
      const base64 = reader.result.split(',')[1];
      uploadedFiles.push({
        name: file.name,
        size: file.size,
        type: 'pdf',
        content: base64,
        encoding: 'base64',
      });
      renderFileList();
      updateSummary();
    };
    reader.readAsDataURL(file);
  } else {
    reader.onload = () => {
      uploadedFiles.push({
        name: file.name,
        size: file.size,
        type: 'markdown',
        content: reader.result,
        encoding: 'utf-8',
      });
      renderFileList();
      updateSummary();
    };
    reader.readAsText(file);
  }
}

function removeFile(index) {
  uploadedFiles.splice(index, 1);
  renderFileList();
  updateSummary();
}

function renderFileList() {
  const container = document.getElementById('file-list');
  if (!uploadedFiles.length) {
    container.innerHTML = '';
    return;
  }

  container.innerHTML = uploadedFiles.map((f, i) => {
    const iconClass = f.type === 'pdf' ? 'file-icon-pdf' : 'file-icon-md';
    const sizeStr = f.size < 1024 ? `${f.size} B` :
                    f.size < 1024 * 1024 ? `${(f.size / 1024).toFixed(1)} KB` :
                    `${(f.size / (1024 * 1024)).toFixed(1)} MB`;
    return `
      <div class="file-item">
        <div class="file-icon ${iconClass}">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        </div>
        <div class="file-info">
          <div class="file-name">${escapeHtml(f.name)}</div>
          <div class="file-size">${sizeStr} &bull; ${f.type.toUpperCase()}</div>
        </div>
        <button class="file-remove" onclick="removeFile(${i})" title="Remove">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
    `;
  }).join('');
}

function updateSummary() {
  const el = document.getElementById('submit-summary');
  if (!el) return;

  const tf = document.getElementById('sub-terraform')?.value.trim();
  const parts = [];
  parts.push('Analysis: <strong>required</strong>');
  parts.push(`Terraform: ${tf ? '<strong style="color:var(--green);">attached</strong>' : 'optional'}`);
  parts.push(`Report: ${uploadedFiles.length ? `<strong style="color:var(--green);">${uploadedFiles.length} file(s)</strong>` : 'optional'}`);
  el.innerHTML = parts.join(' &bull; ');
}

// ── Form Data ──

function getFormData() {
  return {
    week: document.getElementById('sub-week').value.trim(),
    scenario: document.getElementById('sub-scenario').value.trim().toUpperCase(),
    problem: document.getElementById('sub-problem').value.trim(),
    cause: document.getElementById('sub-cause').value.trim(),
    solution: document.getElementById('sub-solution').value.trim(),
    savings: document.getElementById('sub-savings').value.trim(),
    terraform: document.getElementById('sub-terraform')?.value.trim() || '',
  };
}

function buildIssueBody(data) {
  let body = `### Week
${data.week}

### Scenario ID
${data.scenario}

### Problem Identification
${data.problem}

### Root Cause
${data.cause}

### Proposed Solution
${data.solution}

### Estimated Monthly Savings (USD)
${data.savings}`;

  if (data.terraform) {
    body += `

### Optimized Terraform
\`\`\`hcl
${data.terraform}
\`\`\``;
  }

  if (uploadedFiles.length > 0) {
    const names = uploadedFiles.map(f => f.name).join(', ');
    body += `

### Attached Reports
${names}
_(Files committed to submissions/ directory)_`;
  }

  return body;
}

function validateForm(data) {
  const errors = [];
  if (!data.week) errors.push('Week is required');
  if (!data.scenario) errors.push('Scenario ID is required');
  if (!data.problem) errors.push('Problem Identification is required');
  if (!data.cause) errors.push('Root Cause is required');
  if (!data.solution) errors.push('Proposed Solution is required');
  if (!data.savings) errors.push('Estimated Savings is required');
  return errors;
}

function previewSubmission() {
  const data = getFormData();
  const body = buildIssueBody(data);
  document.getElementById('preview-body').textContent = body;
  document.getElementById('preview-card').style.display = 'block';
  document.getElementById('preview-card').scrollIntoView({ behavior: 'smooth' });
}

function showError(msg) {
  const el = document.getElementById('submit-error');
  el.textContent = msg;
  el.style.display = 'flex';
}

// ── Submit ──

async function submitAnswer() {
  const errorEl = document.getElementById('submit-error');
  const successEl = document.getElementById('submit-success');
  errorEl.style.display = 'none';
  successEl.style.display = 'none';

  const data = getFormData();
  const errors = validateForm(data);

  if (errors.length > 0) {
    showError(errors.join(', '));
    return;
  }

  const btn = document.getElementById('submit-btn');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner" style="width:16px;height:16px;margin:0;border-width:2px;"></div> Submitting...';

  try {
    const weekStr = `week-${String(parseInt(data.week)).padStart(2, '0')}`;
    const username = APP.getUsername();
    const basePath = `members/${username}/submissions/${weekStr}`;

    // 1. Upload attached files to repo (if any, and not in local mode)
    if (uploadedFiles.length > 0 && !APP.LOCAL) {
      for (const file of uploadedFiles) {
        const filePath = `${basePath}/${data.scenario}/${file.name}`;
        const content = file.encoding === 'base64' ? file.content : btoa(unescape(encodeURIComponent(file.content)));

        await APP.api(`/repos/${APP.OWNER}/${APP.REPO}/contents/${filePath}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: `Upload report: ${file.name} (${username}, ${data.scenario})`,
            content: content,
          }),
        });
      }
    }

    // 2. Upload terraform code as file (if provided, and not in local mode)
    if (data.terraform && !APP.LOCAL) {
      const tfPath = `${basePath}/${data.scenario}/solution.tf`;
      const tfContent = btoa(unescape(encodeURIComponent(data.terraform)));

      await APP.api(`/repos/${APP.OWNER}/${APP.REPO}/contents/${tfPath}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: `Upload solution.tf (${username}, ${data.scenario})`,
          content: tfContent,
        }),
      });
    }

    // 3. Create issue
    const title = `[Week ${data.week}] ${data.scenario} 답안 제출`;
    const body = buildIssueBody(data);

    let issueHtml = '#';
    if (!APP.LOCAL) {
      const issue = await APP.createIssue(title, body, ['submission']);
      issueHtml = issue.html_url;
    }

    successEl.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
      <div>
        답안이 제출되었습니다!
        ${uploadedFiles.length ? `(${uploadedFiles.length}개 파일 업로드 완료)` : ''}
        ${data.terraform ? '(Terraform 코드 포함)' : ''}
        ${APP.LOCAL ? '' : `<a href="${issueHtml}" target="_blank" style="margin-left:8px;">Issue 보기 &rarr;</a>`}
      </div>
    `;
    successEl.style.display = 'flex';

    document.querySelectorAll('#step-analysis input, #step-analysis textarea, #step-terraform textarea').forEach(el => el.disabled = true);
    btn.textContent = 'Submitted';
  } catch (e) {
    showError(`제출 실패: ${e.message}`);
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
      Submit All
    `;
  }
}

// Listen for terraform changes to update summary
document.addEventListener('input', (e) => {
  if (e.target.id === 'sub-terraform') updateSummary();
});
