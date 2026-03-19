/**
 * scores.js — Scores display and leaderboard
 */

document.addEventListener('DOMContentLoaded', async () => {
  await APP.init();

  if (!APP.isLoggedIn()) {
    window.location.href = 'index.html';
    return;
  }

  try {
    const scoreDirs = await APP.listDir('scores');
    const weeks = scoreDirs
      .filter(d => d.type === 'dir' && d.name.startsWith('week-'))
      .map(d => parseInt(d.name.replace('week-', '')))
      .sort((a, b) => b - a);

    if (weeks.length === 0) {
      document.getElementById('scores-loading').innerHTML = `
        <div class="empty-state">
          <h3>No scores yet</h3>
          <p>정답이 공개되고 채점이 완료되면 여기에 표시됩니다.</p>
        </div>
      `;
      return;
    }

    const tabsEl = document.getElementById('week-tabs');
    tabsEl.innerHTML = weeks.map((w, i) => `
      <div class="tab ${i === 0 ? 'active' : ''}" data-week="${w}"
           onclick="loadWeekScores(${w}, this)">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/></svg>
        Week ${w}
      </div>
    `).join('');

    await loadWeekScores(weeks[0]);

    document.getElementById('scores-loading').style.display = 'none';
    document.getElementById('scores-content').style.display = 'block';
  } catch (e) {
    document.getElementById('scores-loading').innerHTML = `
      <div class="alert alert-error">Failed to load scores: ${escapeHtml(e.message)}</div>
    `;
  }
});

async function loadWeekScores(week, tabEl) {
  if (tabEl) {
    document.querySelectorAll('#week-tabs .tab').forEach(t => t.classList.remove('active'));
    tabEl.classList.add('active');
  }

  const weekStr = `week-${String(week).padStart(2, '0')}`;

  try {
    const summary = await APP.getJSON(`scores/${weekStr}/summary.json`);
    const leaderboard = summary.leaderboard || [];

    const tbody = document.getElementById('leaderboard-body');
    tbody.innerHTML = leaderboard.map(entry => {
      const pct = entry.percentage || 0;
      const fillClass = pct >= 70 ? 'fill-green' : pct >= 40 ? 'fill-orange' : 'fill-red';
      const rankBadge = entry.rank === 1 ? '<span style="font-size:16px;">&#129351;</span>' :
                        entry.rank === 2 ? '<span style="font-size:16px;">&#129352;</span>' :
                        entry.rank === 3 ? '<span style="font-size:16px;">&#129353;</span>' : entry.rank;
      return `
        <tr>
          <td style="text-align:center;">${rankBadge}</td>
          <td>
            <div style="display:flex;align-items:center;gap:8px;">
              <div style="width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#4c6ef5,#7950f2);display:flex;align-items:center;justify-content:center;color:#fff;font-size:11px;font-weight:600;">${entry.username.charAt(0).toUpperCase()}</div>
              <strong>@${escapeHtml(entry.username)}</strong>
            </div>
          </td>
          <td style="font-weight:600;">${entry.total}</td>
          <td style="color:var(--text-muted);">${entry.max_total}</td>
          <td style="font-weight:600;color:${pct >= 70 ? 'var(--green)' : pct >= 40 ? 'var(--orange)' : 'var(--red)'};">${pct}%</td>
          <td>
            <div class="progress-bar" style="width:120px;">
              <div class="fill ${fillClass}" style="width:${pct}%"></div>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    if (!leaderboard.length) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:32px;">No scores available</td></tr>`;
    }

    // Load current user's detailed scores
    const username = APP.getUsername();
    try {
      const myScores = await APP.getJSON(`scores/${weekStr}/${username}.json`);
      renderMyScores(myScores);
    } catch {
      document.getElementById('my-scores-card').style.display = 'none';
    }
  } catch {
    document.getElementById('leaderboard-body').innerHTML = `
      <tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:32px;">No scores available</td></tr>
    `;
  }
}

function renderMyScores(data) {
  const card = document.getElementById('my-scores-card');
  const detail = document.getElementById('my-scores-detail');
  card.style.display = 'block';

  const scenarios = data.scenarios || {};
  let html = '';

  for (const [scenarioId, result] of Object.entries(scenarios)) {
    const scores = result.scores || {};
    const pct = result.percentage || 0;
    const color = pct >= 70 ? 'var(--green)' : pct >= 40 ? 'var(--orange)' : 'var(--red)';
    html += `
      <div style="margin-bottom:24px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
          <span style="font-weight:700;font-size:15px;">${scenarioId}</span>
          <span class="badge" style="background:${color}15;color:${color};">${result.total}/${result.max_total} (${pct}%)</span>
        </div>
        <table>
          <thead><tr><th>Category</th><th>Score</th><th>Progress</th></tr></thead>
          <tbody>
            ${renderScoreRow('Problem Identification', scores.identify_problem || 0, 30)}
            ${renderScoreRow('Root Cause', scores.identify_root_cause || 0, 20)}
            ${renderScoreRow('Proposed Solution', scores.propose_solution || 0, 30)}
            ${renderScoreRow('Savings Estimate', scores.estimate_savings || 0, 20)}
          </tbody>
        </table>
      </div>
    `;
  }

  detail.innerHTML = html || '<p style="color:var(--text-muted);">No detailed scores available.</p>';
}

function renderScoreRow(label, score, max) {
  const pct = max > 0 ? (score / max * 100) : 0;
  const fillClass = pct >= 70 ? 'fill-green' : pct >= 40 ? 'fill-orange' : 'fill-red';
  return `
    <tr>
      <td>${label}</td>
      <td style="font-weight:600;">${score} / ${max}</td>
      <td><div class="progress-bar" style="width:100px;"><div class="fill ${fillClass}" style="width:${pct}%"></div></div></td>
    </tr>
  `;
}
