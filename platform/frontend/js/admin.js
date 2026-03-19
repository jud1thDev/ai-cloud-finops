/**
 * admin.js — Admin dashboard logic
 */

document.addEventListener('DOMContentLoaded', async () => {
  await APP.init();

  if (!APP.isLoggedIn()) {
    showLoginModal();
    return;
  }

  if (!APP.isAdmin()) {
    document.getElementById('admin-denied').style.display = 'block';
    return;
  }

  document.getElementById('admin-content').style.display = 'block';

  // Set default reveal date to next Monday
  const today = new Date();
  const nextMonday = new Date(today);
  nextMonday.setDate(today.getDate() + ((8 - today.getDay()) % 7 || 7));
  document.getElementById('gen-reveal').value = nextMonday.toISOString().split('T')[0];

  await Promise.allSettled([loadMembers(), loadSubmissionStatus()]);
});

async function loadMembers() {
  const el = document.getElementById('members-list');
  try {
    const content = await APP.getFileContent('platform/config/members.yaml');
    const lines = content.split('\n');
    const members = [];
    let current = null;

    for (const line of lines) {
      const usernameMatch = line.match(/username:\s*(\S+)/);
      const nameMatch = line.match(/name:\s*"?([^"]+)"?/);

      if (usernameMatch) {
        current = { username: usernameMatch[1] };
        members.push(current);
      } else if (nameMatch && current) {
        current.name = nameMatch[1];
      }
    }

    if (members.length === 0) {
      el.innerHTML = '<p style="color:var(--text-muted);">No members registered.</p>';
      return;
    }

    el.innerHTML = `
      <table>
        <thead><tr><th>Username</th><th>Name</th></tr></thead>
        <tbody>
          ${members.map(m => `
            <tr>
              <td>@${escapeHtml(m.username)}</td>
              <td>${escapeHtml(m.name || '-')}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (e) {
    el.innerHTML = `<p style="color:var(--text-muted);">Could not load members: ${escapeHtml(e.message)}</p>`;
  }
}

async function loadSubmissionStatus() {
  const el = document.getElementById('submissions-status');
  try {
    const dirs = await APP.listDir('submissions');
    if (!dirs.length) {
      el.innerHTML = '<p style="color:var(--text-muted);">No submissions yet.</p>';
      return;
    }

    let html = '<table><thead><tr><th>Week</th><th>Submissions</th></tr></thead><tbody>';
    for (const dir of dirs) {
      if (dir.type !== 'dir') continue;
      const memberDirs = await APP.listDir(`submissions/${dir.name}`);
      let count = 0;
      for (const md of memberDirs) {
        if (md.type === 'dir') {
          const files = await APP.listDir(`submissions/${dir.name}/${md.name}`);
          count += files.filter(f => f.name.endsWith('.json')).length;
        }
      }
      html += `<tr><td>${dir.name}</td><td>${count}</td></tr>`;
    }
    html += '</tbody></table>';
    el.innerHTML = html;
  } catch {
    el.innerHTML = '<p style="color:var(--text-muted);">Could not load submission status.</p>';
  }
}

async function triggerGenerate() {
  const btn = document.getElementById('gen-btn');
  const resultEl = document.getElementById('gen-result');
  btn.disabled = true;
  btn.textContent = 'Triggering...';
  resultEl.style.display = 'none';

  try {
    const inputs = {
      week_number: document.getElementById('gen-week').value,
      level: document.getElementById('gen-level').value,
      num_problems: document.getElementById('gen-num').value,
      category: document.getElementById('gen-category').value,
      reveal_date: document.getElementById('gen-reveal').value,
    };

    await APP.triggerWorkflow('generate-weekly.yaml', inputs);

    resultEl.className = 'alert alert-success';
    resultEl.textContent = 'Workflow triggered! Check Actions tab for progress.';
    resultEl.style.display = 'block';
  } catch (e) {
    resultEl.className = 'alert alert-error';
    resultEl.textContent = `Failed: ${e.message}`;
    resultEl.style.display = 'block';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate';
  }
}

async function triggerReveal() {
  const resultEl = document.getElementById('action-result');
  try {
    await APP.triggerWorkflow('reveal-answers.yaml', {});
    resultEl.className = 'alert alert-success';
    resultEl.textContent = 'Reveal workflow triggered!';
    resultEl.style.display = 'block';
  } catch (e) {
    resultEl.className = 'alert alert-error';
    resultEl.textContent = `Failed: ${e.message}`;
    resultEl.style.display = 'block';
  }
}

async function triggerScore() {
  const week = document.getElementById('gen-week').value;
  const resultEl = document.getElementById('action-result');
  try {
    await APP.triggerWorkflow('score-week.yaml', { week_number: week });
    resultEl.className = 'alert alert-success';
    resultEl.textContent = `Score workflow triggered for week ${week}!`;
    resultEl.style.display = 'block';
  } catch (e) {
    resultEl.className = 'alert alert-error';
    resultEl.textContent = `Failed: ${e.message}`;
    resultEl.style.display = 'block';
  }
}
