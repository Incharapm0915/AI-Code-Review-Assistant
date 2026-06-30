/* Dashboard Page Logic */

let activityChart, languageChart, qualityChart;

async function loadDashboard() {
  if (!App.requireAuth()) return;

  try {
    const [statsRes, activityRes] = await Promise.all([
      API.get('/api/dashboard/stats'),
      API.get('/api/dashboard/activity?days=7')
    ]);

    if (statsRes?.data) renderStats(statsRes.data);
    if (activityRes?.data) renderActivity(activityRes.data);

  } catch (err) {
    Toast.error('Failed to load dashboard data', err.message);
  }
}

function renderStats(data) {
  const fields = {
    'total-reviews': data.total_reviews,
    'avg-score': Math.round(data.avg_quality_score),
    'total-vulnerabilities': data.total_vulnerabilities,
    'critical-issues': data.critical_issues,
    'total-uploads': data.total_uploads,
    'total-pastes': data.total_pastes,
  };

  Object.entries(fields).forEach(([id, val]) => {
    const el = document.getElementById(id);
    if (el) animateCount(el, val || 0);
  });

  const recentEl = document.getElementById('recent-reports');
  if (recentEl && data.recent_reports?.length) {
    recentEl.innerHTML = data.recent_reports.map(r => `
      <tr>
        <td>
          <div style="font-weight:600;font-size:0.875rem;">${r.source_type === 'upload' ? '📁' : r.source_type === 'github' ? '🐙' : '📝'} ${r.language.charAt(0).toUpperCase() + r.language.slice(1)}</div>
          <div style="font-size:0.75rem;color:var(--text-muted);">${formatDateTime(r.created_at)}</div>
        </td>
        <td>
          <div style="display:flex;align-items:center;gap:8px;">
            <div class="progress" style="width:80px;"><div class="progress-bar" style="width:${r.quality_score}%;background:${getScoreColor(r.quality_score)};"></div></div>
            <span style="font-weight:700;color:${getScoreColor(r.quality_score)};">${Math.round(r.quality_score)}</span>
          </div>
        </td>
        <td>${createBadge(r.critical_issues > 0 ? 'critical' : r.warnings > 0 ? 'medium' : 'success')}</td>
        <td>
          <a href="/results/${r.id}" class="btn btn-sm btn-outline">View →</a>
        </td>
      </tr>
    `).join('');
  } else if (recentEl) {
    recentEl.innerHTML = `<tr><td colspan="4" style="text-align:center;padding:32px;color:var(--text-muted);">No analysis history yet. <a href="/upload">Upload your first file</a></td></tr>`;
  }

  // Render score rings
  const scoreRingEl = document.getElementById('avg-score-ring');
  if (scoreRingEl) {
    scoreRingEl.innerHTML = createScoreRing(data.avg_quality_score, 100, 8);
  }
}

function renderActivity(data) {
  const activity = data.activity || [];

  // Group by date
  const byDate = {};
  activity.forEach(a => {
    if (!byDate[a.date]) byDate[a.date] = [];
    byDate[a.date].push(a.score);
  });

  const dates = Object.keys(byDate).sort().slice(-7);
  const scores = dates.map(d => {
    const arr = byDate[d];
    return Math.round(arr.reduce((a, b) => a + b, 0) / arr.length);
  });

  const ctx = document.getElementById('activity-chart');
  if (!ctx) return;

  if (activityChart) activityChart.destroy();

  activityChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: dates.map(d => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
      datasets: [{
        label: 'Avg Quality Score',
        data: scores,
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#6366f1',
        pointRadius: 5,
        pointHoverRadius: 8,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(15,23,42,0.95)',
          borderColor: 'rgba(99,102,241,0.3)',
          borderWidth: 1,
          titleColor: '#f1f5f9',
          bodyColor: '#94a3b8',
          padding: 12,
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(148,163,184,0.08)' },
          ticks: { color: '#64748b' }
        },
        y: {
          min: 0,
          max: 100,
          grid: { color: 'rgba(148,163,184,0.08)' },
          ticks: { color: '#64748b' }
        }
      }
    }
  });

  // Language distribution chart
  const langCtx = document.getElementById('language-chart');
  if (langCtx) {
    const langCount = {};
    activity.forEach(a => { langCount[a.type] = (langCount[a.type] || 0) + 1; });

    if (languageChart) languageChart.destroy();
    languageChart = new Chart(langCtx, {
      type: 'doughnut',
      data: {
        labels: Object.keys(langCount),
        datasets: [{
          data: Object.values(langCount),
          backgroundColor: ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b'],
          borderWidth: 0,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '70%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#94a3b8', padding: 16, font: { size: 12 } }
          }
        }
      }
    });
  }
}

document.addEventListener('DOMContentLoaded', loadDashboard);
