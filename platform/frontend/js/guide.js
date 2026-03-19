/**
 * guide.js — Starter Kit viewer + downloader
 *
 * Fetches starter-kit files from GitHub repo and displays them inline.
 * Download button creates a zip-like experience (individual file downloads).
 */

const STARTER_KIT_FILES = [
  { path: 'platform/starter-kit/agent.py', name: 'agent.py', desc: 'Main agent — run this', lang: 'python' },
  { path: 'platform/starter-kit/config.py', name: 'config.py', desc: 'Model provider settings', lang: 'python' },
  { path: 'platform/starter-kit/file_reader.py', name: 'file_reader.py', desc: 'Problem file parser', lang: 'python' },
  { path: 'platform/starter-kit/output_builder.py', name: 'output_builder.py', desc: 'Output JSON builder + validator', lang: 'python' },
  { path: 'platform/starter-kit/prompts/system.md', name: 'prompts/system.md', desc: 'System prompt (FinOps expert role)', lang: 'markdown' },
  { path: 'platform/starter-kit/prompts/L1_analyze.md', name: 'prompts/L1_analyze.md', desc: 'L1 analysis instructions', lang: 'markdown' },
  { path: 'platform/starter-kit/prompts/L2_analyze.md', name: 'prompts/L2_analyze.md', desc: 'L2 analysis instructions', lang: 'markdown' },
  { path: 'platform/starter-kit/prompts/L3_analyze.md', name: 'prompts/L3_analyze.md', desc: 'L3 analysis instructions', lang: 'markdown' },
  { path: 'platform/starter-kit/requirements.txt', name: 'requirements.txt', desc: 'Dependencies (none required)', lang: 'text' },
];

let fileContents = {}; // cache

document.addEventListener('DOMContentLoaded', async () => {
  await APP.init();
  await loadKitFiles();
  hljs.highlightAll();
});

async function loadKitFiles() {
  const container = document.getElementById('kit-files');
  const loading = document.getElementById('kit-files-loading');

  let html = '';

  for (const file of STARTER_KIT_FILES) {
    const ext = file.name.split('.').pop();
    const iconBg = ext === 'py' ? '#fef3c7' : ext === 'md' ? '#dbeafe' : '#f5f6fa';
    const iconColor = ext === 'py' ? '#b45309' : ext === 'md' ? '#1d4ed8' : '#5f6577';
    const iconText = ext === 'py' ? 'PY' : ext === 'md' ? 'MD' : 'TXT';

    // Try to load content
    let content = '';
    try {
      content = await APP.getFileContent(file.path);
      fileContents[file.name] = content;
    } catch {
      content = '// Failed to load';
    }

    // Truncate for display (show first 30 lines)
    const lines = content.split('\n');
    const preview = lines.slice(0, 30).join('\n');
    const truncated = lines.length > 30;

    html += `
      <div style="margin-bottom:16px;border:1px solid var(--border-light);border-radius:var(--radius-sm);overflow:hidden;">
        <div style="display:flex;align-items:center;gap:10px;padding:12px 16px;background:var(--bg);border-bottom:1px solid var(--border-light);">
          <span style="display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:6px;background:${iconBg};color:${iconColor};font-size:10px;font-weight:700;">${iconText}</span>
          <div style="flex:1;">
            <div style="font-weight:600;font-size:14px;">${escapeHtml(file.name)}</div>
            <div style="font-size:12px;color:var(--text-muted);">${escapeHtml(file.desc)}</div>
          </div>
          <button onclick="copyFileContent('${file.name}')" class="btn btn-sm btn-ghost" title="Copy">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            Copy
          </button>
          <button onclick="downloadSingleFile('${file.name}')" class="btn btn-sm btn-ghost" title="Download">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          </button>
        </div>
        <pre style="margin:0;border-radius:0;max-height:400px;overflow:auto;font-size:12px;"><code class="language-${file.lang === 'python' ? 'python' : file.lang === 'markdown' ? 'markdown' : 'plaintext'}">${escapeHtml(preview)}${truncated ? '\n\n// ... (truncated, download for full file)' : ''}</code></pre>
      </div>
    `;
  }

  loading.style.display = 'none';
  container.innerHTML = html;
  container.style.display = 'block';
}

function copyFileContent(name) {
  const content = fileContents[name];
  if (!content) return;

  navigator.clipboard.writeText(content).then(() => {
    // Brief visual feedback
    const btn = event.target.closest('button');
    const orig = btn.innerHTML;
    btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Copied!';
    setTimeout(() => { btn.innerHTML = orig; }, 1500);
  });
}

function downloadSingleFile(name) {
  const content = fileContents[name];
  if (!content) return;

  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name.includes('/') ? name.split('/').pop() : name;
  a.click();
  URL.revokeObjectURL(url);
}

async function downloadStarterKit() {
  // Download all files as individual downloads (no zip library needed)
  // First ensure all files are loaded
  for (const file of STARTER_KIT_FILES) {
    if (!fileContents[file.name]) {
      try {
        fileContents[file.name] = await APP.getFileContent(file.path);
      } catch {}
    }
  }

  // Create a combined single file download (all-in-one script)
  // OR trigger individual downloads
  const allContent = STARTER_KIT_FILES.map(f => {
    const content = fileContents[f.name] || '';
    return `${'='.repeat(60)}\n# FILE: ${f.name}\n# ${f.desc}\n${'='.repeat(60)}\n\n${content}`;
  }).join('\n\n\n');

  // Option 1: Download as single combined text file
  const blob = new Blob([allContent], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'finops-starter-kit-all-files.txt';
  a.click();
  URL.revokeObjectURL(url);

  // Option 2: Also trigger individual file downloads with delay
  let delay = 500;
  for (const file of STARTER_KIT_FILES) {
    setTimeout(() => downloadSingleFile(file.name), delay);
    delay += 300;
  }
}
