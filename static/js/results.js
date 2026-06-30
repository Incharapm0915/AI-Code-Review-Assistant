/* Results page — chart rendering helpers */

function renderScoreChart(canvasId, scores) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  return new Chart(ctx, {
    type: 'radar',
    data: {
      labels: ['Quality', 'Security', 'Complexity', 'Maintainability'],
      datasets: [{
        label: 'Code Scores',
        data: [
          scores.quality || 0,
          scores.security || 0,
          scores.complexity || 0,
          scores.maintainability || 0,
        ],
        backgroundColor: 'rgba(99, 102, 241, 0.15)',
        borderColor: '#6366f1',
        borderWidth: 2,
        pointBackgroundColor: '#6366f1',
        pointRadius: 5,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          min: 0,
          max: 100,
          ticks: { color: '#64748b', stepSize: 20 },
          grid: { color: 'rgba(148,163,184,0.1)' },
          pointLabels: { color: '#94a3b8', font: { size: 12 } },
        }
      },
      plugins: {
        legend: { display: false },
      }
    }
  });
}

function renderIssueDistribution(canvasId, issues) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const counts = { Critical: 0, High: 0, Medium: 0, Low: 0, Info: 0 };
  issues.forEach(i => {
    const sev = (i.severity || 'info').charAt(0).toUpperCase() + i.severity.slice(1);
    if (counts[sev] !== undefined) counts[sev]++;
  });

  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: Object.keys(counts),
      datasets: [{
        data: Object.values(counts),
        backgroundColor: ['#dc2626', '#ea580c', '#d97706', '#3b82f6', '#6b7280'],
        borderWidth: 0,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#94a3b8', padding: 12, font: { size: 11 } }
        }
      }
    }
  });
}
