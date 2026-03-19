/**
 * profile.js — User profile: info, submission history, score trends
 * Supports viewing own profile and other members' profiles via ?user=username
 */

let scoreTrendChart = null;

document.addEventListener('DOMContentLoaded', async () => {
  await APP.init();

  if (!APP.isLoggedIn()) {
    window.location.href = 'index.html';
    return;
  }

  // Determine which user to display
  const params = new URLSearchParams(window.location.search);
  const targetUser = params.get('user') || APP.getUsername();
  const isOwnProfile = targetUser === APP.getUsername();

  // Load member list for switcher
  await loadMemberSwitcher(targetUser);

  // Load profile
  await loadProfile(targetUser, isOwnProfile);
});

// ── Member Switcher ──

async function loadMemberSwitcher(currentUser) {
  const select = document.getElementById('member-select');
  try {
    const content = await APP.getFileContent('platform/config/members.yaml');
    const matches = content.match(/username:\s*"?([^"\n]+)"?/g) || [];
    const members = matches.map(m => m.replace(/username:\s*"?/, '').replace(/"$/, ''));

    select.innerHTML = members.map(m =>
      `<option value="${m}" ${m === currentUser ? 'selected' : ''}>@${m}</option>`
    ).join('');
  } catch {
    select.innerHTML = `<option value="${currentUser}">@${currentUser}</option>`;
  }
}

function switchMember(username) {
  if (username) {
    window.location.href = `profile.html?user=${encodeURIComponent(username)}`;
  }
}

// ── Profile Loading ──

async function loadProfile(username, isOwnProfile) {
  const loading = document.getElementById('profile-loading');

  try {
    // Set user info
    document.getElementById('page-title').textContent = isOwnProfile ? 'My Profile' : `@${username}'s Profile`;
    document.getElementById('profile-avatar').textContent = username.charAt(0).toUpperCase();
    document.getElementById('profile-name').textContent = `@${username}`;
    document.getElementById('profile-github').innerHTML += ` <a href="https://github.com/${username}" target="_blank" style="color:var(--text-secondary);">github.com/${username}</a>`;

    if (isOwnProfile) {
      const roleBadge = document.getElementById('profile-role');
      if (APP.isAdmin()) {
        roleBadge.textContent = 'Admin';
        roleBadge.style.display = '';
      }
    }

    // Gather all data concurrently
    const [submissions, scores, assignments] = await Promise.all([
      gatherSubmissions(username),
      gatherScores(username),
      gatherAssignments(username),
    ]);

    // Compute stats
    const weeksParticipated = new Set([...submissions.map(s => s.week), ...assignments.map(a => a.week)]).size;
    const totalSubmissions = submissions.length;
    const avgScore = scores.length > 0
      ? Math.round(scores.reduce((sum, s) => sum + s.percentage, 0) / scores.length)
      : null;
    const bestRank = scores.length > 0
      ? Math.min(...scores.map(s => s.rank).filter(r => r > 0))
      : null;

    document.getElementById('stat-weeks').textContent = weeksParticipated;
    document.getElementById('stat-submitted').textContent = totalSubmissions;
    document.getElementById('stat-avg-score').textContent = avgScore !== null ? `${avgScore}%` : '-';
    document.getElementById('stat-best-rank').textContent = bestRank !== null && bestRank < Infinity ? `#${bestRank}` : '-';

    // Joined date (from first assignment)
    if (assignments.length > 0) {
      document.getElementById('profile-joined').innerHTML += ` Week ${Math.min(...assignments.map(a => a.week))}~`;
    }

    // Render score trend chart
    renderScoreTrend(scores);

    // Render submission history table
    renderSubmissionHistory(submissions, scores, assignments, username);

    // Render per-week score details
    renderWeekDetails(scores, username);

    document.getElementById('submission-count-badge').textContent = `${totalSubmissions} submissions`;

    loading.style.display = 'none';
    document.getElementById('profile-content').style.display = 'block';
  } catch (e) {
    loading.innerHTML = `
      <div class="alert alert-error">Failed to load profile: ${escapeHtml(e.message)}</div>
    `;
  }
}

// ── Data Gathering ──

async function gatherSubmissions(username) {
  const submissions = [];
  for (let week = 1; week <= 8; week++) {
    const weekStr = `week-${String(week).padStart(2, '0')}`;
    try {
      const files = await APP.listDir(`members/${username}/submissions/${weekStr}`);
      if (files && files.length > 0) {
        for (const f of files) {
          if (f.name.endsWith('.json')) {
            submissions.push({
              week,
              scenario: f.name.replace('.json', ''),
              filename: f.name,
              fileCount: 1,
            });
          }
        }
      }
    } catch { /* no submissions for this week */ }
  }
  return submissions;
}

async function gatherScores(username) {
  const scores = [];
  for (let week = 1; week <= 8; week++) {
    const weekStr = `week-${String(week).padStart(2, '0')}`;
    try {
      const data = await APP.getJSON(`scores/${weekStr}/${username}.json`);
      // Get rank from summary
      let rank = 0;
      try {
        const summary = await APP.getJSON(`scores/${weekStr}/summary.json`);
        const entry = (summary.leaderboard || []).find(e => e.username === username);
        if (entry) rank = entry.rank;
      } catch {}

      scores.push({
        week,
        total: data.total || 0,
        maxTotal: data.max_total || 0,
        percentage: data.percentage || 0,
        rank,
        scenarios: data.scenarios || {},
      });
    } catch { /* no scores for this week */ }
  }
  return scores.sort((a, b) => a.week - b.week);
}

async function gatherAssignments(username) {
  const assignments = [];
  for (let week = 1; week <= 8; week++) {
    const weekStr = `week-${String(week).padStart(2, '0')}`;
    try {
      const data = await APP.getJSON(`members/${username}/problems/${weekStr}/assignment.json`);
      assignments.push({
        week,
        level: data.level,
        scenarios: data.scenarios || [],
        company: data.company,
      });
    } catch { /* no assignment for this week */ }
  }
  return assignments;
}

// ── Renderers ──

function renderScoreTrend(scores) {
  const canvas = document.getElementById('score-trend-chart');
  const ctx = canvas.getContext('2d');

  if (scoreTrendChart) scoreTrendChart.destroy();

  if (scores.length === 0) {
    ctx.font = '14px Inter';
    ctx.fillStyle = '#9098b1';
    ctx.textAlign = 'center';
    ctx.fillText('No scores yet', canvas.width / 2, canvas.height / 2);
    return;
  }

  const labels = scores.map(s => `Week ${s.week}`);
  const data = scores.map(s => s.percentage);
  const ranks = scores.map(s => s.rank);

  scoreTrendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Score %',
          data,
          borderColor: '#4c6ef5',
          backgroundColor: '#4c6ef520',
          borderWidth: 3,
          pointRadius: 6,
          pointBackgroundColor: '#fff',
          pointBorderColor: '#4c6ef5',
          pointBorderWidth: 2,
          tension: 0.3,
          fill: true,
          yAxisID: 'y',
        },
        {
          label: 'Rank',
          data: ranks,
          borderColor: '#12b886',
          backgroundColor: 'transparent',
          borderWidth: 2,
          borderDash: [6, 4],
          pointRadius: 4,
          pointBackgroundColor: '#12b886',
          tension: 0.3,
          yAxisID: 'y1',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          labels: { color: '#5f6577', font: { size: 12, family: 'Inter' }, usePointStyle: true }
        },
        tooltip: {
          callbacks: {
            label: function(ctx) {
              if (ctx.dataset.label === 'Rank') return `Rank: #${ctx.raw}`;
              return `Score: ${ctx.raw}%`;
            }
          }
        }
      },
      scales: {
        x: {
          ticks: { color: '#9098b1', font: { size: 12 } },
          grid: { color: '#eceef4' }
        },
        y: {
          position: 'left',
          min: 0,
          max: 100,
          title: { display: true, text: 'Score %', color: '#4c6ef5', font: { size: 12 } },
          ticks: { color: '#9098b1', font: { size: 11 } },
          grid: { color: '#eceef4' }
        },
        y1: {
          position: 'right',
          reverse: true,
          min: 1,
          title: { display: true, text: 'Rank', color: '#12b886', font: { size: 12 } },
          ticks: { color: '#9098b1', font: { size: 11 }, stepSize: 1 },
          grid: { drawOnChartArea: false }
        }
      }
    }
  });
}

function renderSubmissionHistory(submissions, scores, assignments, username) {
  const tbody = document.getElementById('submissions-body');

  // Build a unified list: all assigned scenarios across all weeks
  const rows = [];

  for (const assign of assignments) {
    for (const scenarioId of assign.scenarios) {
      const sub = submissions.find(s => s.week === assign.week && s.scenario === scenarioId);
      const weekScore = scores.find(s => s.week === assign.week);
      const scenarioScore = weekScore?.scenarios?.[scenarioId];

      rows.push({
        week: assign.week,
        scenario: scenarioId,
        level: assign.level,
        submitted: !!sub,
        score: scenarioScore?.total ?? null,
        maxScore: scenarioScore?.max_total ?? null,
        percentage: scenarioScore?.percentage ?? null,
      });
    }
  }

  // Also add submissions not in assignments (edge case)
  for (const sub of submissions) {
    if (!rows.find(r => r.week === sub.week && r.scenario === sub.scenario)) {
      rows.push({
        week: sub.week,
        scenario: sub.scenario,
        level: sub.scenario.split('-')[0],
        submitted: true,
        score: null,
        maxScore: null,
        percentage: null,
      });
    }
  }

  rows.sort((a, b) => b.week - a.week || a.scenario.localeCompare(b.scenario));

  if (rows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--text-muted);padding:32px;">No data yet. Problems will appear once assigned.</td></tr>`;
    return;
  }

  tbody.innerHTML = rows.map(r => {
    const statusBadge = r.submitted
      ? '<span class="badge badge-submitted">Submitted</span>'
      : '<span class="badge badge-pending">Pending</span>';

    let scoreHtml = '-';
    if (r.score !== null) {
      const pct = r.percentage || (r.maxScore > 0 ? Math.round(r.score / r.maxScore * 100) : 0);
      const color = pct >= 70 ? 'var(--green)' : pct >= 40 ? 'var(--orange)' : 'var(--red)';
      scoreHtml = `<span style="font-weight:600;color:${color};">${r.score}/${r.maxScore} (${pct}%)</span>`;
    }

    const filesHtml = r.submitted
      ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>`
      : `<span style="color:var(--text-muted);">-</span>`;

    const viewLink = r.submitted
      ? `<a href="problems.html?week=${r.week}" class="btn btn-sm btn-ghost" style="padding:4px 8px;font-size:12px;">View</a>`
      : '';

    return `
      <tr>
        <td>Week ${r.week}</td>
        <td style="font-weight:600;">${r.scenario}</td>
        <td><span class="badge badge-${r.level}">${r.level}</span></td>
        <td>${statusBadge}</td>
        <td>${scoreHtml}</td>
        <td style="text-align:center;">${filesHtml}</td>
        <td>${viewLink}</td>
      </tr>
    `;
  }).join('');
}

function renderWeekDetails(scores, username) {
  const container = document.getElementById('week-details');
  if (scores.length === 0) {
    container.innerHTML = '';
    return;
  }

  container.innerHTML = scores.map(s => {
    const scenarios = Object.entries(s.scenarios);
    if (scenarios.length === 0) return '';

    const pct = s.percentage;
    const color = pct >= 70 ? 'var(--green)' : pct >= 40 ? 'var(--orange)' : 'var(--red)';

    let scenarioHtml = '';
    for (const [sid, result] of scenarios) {
      // Support both v1 (scores.identify_problem) and v2 (breakdown.schema) formats
      const isV2 = result.breakdown && typeof result.breakdown === 'object';

      if (isV2) {
        scenarioHtml += renderV2ScoreDetail(sid, result);
      } else {
        scenarioHtml += renderV1ScoreDetail(sid, result);
      }
    }

    return `
      <div class="card" style="margin-bottom:20px;">
        <div class="card-header-bar">
          <div style="display:flex;align-items:center;gap:10px;">
            <span style="font-weight:600;">Week ${s.week}</span>
            <span class="badge" style="background:${color}15;color:${color};">${s.total}/${s.maxTotal} (${pct}%)</span>
            ${s.rank > 0 ? `<span style="font-size:13px;color:var(--text-muted);">Rank #${s.rank}</span>` : ''}
          </div>
        </div>
        <div class="card-body">${scenarioHtml}</div>
      </div>
    `;
  }).join('');
}

function renderV1ScoreDetail(scenarioId, result) {
  const scores = result.scores || {};
  const pct = result.percentage || 0;
  const color = pct >= 70 ? 'var(--green)' : pct >= 40 ? 'var(--orange)' : 'var(--red)';

  return `
    <div style="margin-bottom:20px;">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
        <span style="font-weight:600;">${scenarioId}</span>
        <span class="badge" style="background:${color}15;color:${color};">${result.total}/${result.max_total}</span>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;">
        ${scoreBar('Problem ID', scores.identify_problem || 0, 30)}
        ${scoreBar('Root Cause', scores.identify_root_cause || 0, 20)}
        ${scoreBar('Solution', scores.propose_solution || 0, 30)}
        ${scoreBar('Savings', scores.estimate_savings || 0, 20)}
      </div>
    </div>
  `;
}

function renderV2ScoreDetail(scenarioId, result) {
  const bd = result.breakdown || {};
  const pct = result.percentage || 0;
  const color = pct >= 70 ? 'var(--green)' : pct >= 40 ? 'var(--orange)' : 'var(--red)';

  const items = [
    { label: 'Schema', key: 'schema' },
    { label: 'Resource', key: 'resource' },
    { label: 'Terraform', key: 'terraform' },
    { label: 'Savings', key: 'savings' },
    { label: 'Economics', key: 'economics' },
    { label: 'Alerts', key: 'alerts' },
  ];

  const bars = items
    .filter(it => bd[it.key] && bd[it.key].max > 0 && bd[it.key].detail !== 'skipped')
    .map(it => scoreBar(it.label, bd[it.key].score || 0, bd[it.key].max || 0))
    .join('');

  return `
    <div style="margin-bottom:20px;">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
        <span style="font-weight:600;">${scenarioId}</span>
        <span class="badge" style="background:${color}15;color:${color};">${result.total}/${result.total_max} (${pct}%)</span>
        <span class="badge" style="background:var(--primary-light);color:var(--primary);font-size:11px;">v2</span>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;">
        ${bars}
      </div>
    </div>
  `;
}

function scoreBar(label, score, max) {
  const pct = max > 0 ? Math.round(score / max * 100) : 0;
  const fillClass = pct >= 70 ? 'fill-green' : pct >= 40 ? 'fill-orange' : 'fill-red';
  return `
    <div style="padding:8px 12px;background:var(--bg);border-radius:var(--radius-xs);border:1px solid var(--border-light);">
      <div style="display:flex;justify-content:space-between;margin-bottom:4px;font-size:12px;">
        <span style="color:var(--text-secondary);">${label}</span>
        <span style="font-weight:600;">${score}/${max}</span>
      </div>
      <div class="progress-bar"><div class="fill ${fillClass}" style="width:${pct}%"></div></div>
    </div>
  `;
}
