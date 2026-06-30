/* Upload Page — drag-drop, progress, history logic */

const LANG_ICONS = { py:'🐍', js:'⚡', ts:'⚡', java:'☕', cpp:'⚙️', c:'⚙️', h:'⚙️', cc:'⚙️', txt:'📄' };

function initUploadPage() {
  if (!App.requireAuth()) return;
  document.getElementById('auth-guard').style.display = 'block';
  setupDropZone();
  loadUploadHistory();
}

function setupDropZone() {
  const zone = document.getElementById('upload-zone');
  const input = document.getElementById('file-input');
  if (!zone || !input) return;

  zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('drag-over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });

  input.addEventListener('change', (e) => {
    if (e.target.files[0]) handleFile(e.target.files[0]);
  });
}

function handleFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  const allowed = ['py','js','ts','java','cpp','c','h','cc','hpp','txt'];
  if (!allowed.includes(ext)) {
    Toast.warning('Unsupported file', `Only ${allowed.join(', ')} files are accepted`);
    return;
  }
  if (file.size > 16 * 1024 * 1024) {
    Toast.warning('File too large', 'Maximum file size is 16 MB');
    return;
  }

  window._selectedFile = file;
  const preview = document.getElementById('file-preview');
  if (preview) {
    document.getElementById('file-icon').textContent = LANG_ICONS[ext] || '📄';
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('file-meta').textContent = `${formatBytes(file.size)} • ${ext.toUpperCase()}`;
    preview.style.display = 'flex';
  }
  const btn = document.getElementById('upload-btn');
  if (btn) btn.disabled = false;
  Toast.info('File selected', file.name);
}

async function loadUploadHistory() {
  const list = document.getElementById('history-list');
  if (!list) return;

  try {
    const res = await API.get('/api/upload/history?per_page=20');
    const uploads = res?.data?.uploads || [];
    if (!uploads.length) {
      list.innerHTML = '<div style="padding:40px;text-align:center;color:var(--text-muted);">📂 No uploads yet.</div>';
      return;
    }
    list.innerHTML = uploads.map(u => `
      <div style="padding:14px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;">
        <span style="font-size:1.3rem;">${LANG_ICONS[u.language] || '📄'}</span>
        <div style="flex:1;min-width:0;">
          <div style="font-weight:600;font-size:0.875rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${u.filename}</div>
          <div style="font-size:0.75rem;color:var(--text-muted);">${u.language?.toUpperCase()} • ${formatDate(u.created_at)} • ${formatBytes(u.file_size || 0)}</div>
        </div>
        <div style="text-align:right;flex-shrink:0;">
          ${u.quality_score != null
            ? `<div style="font-weight:800;color:${getScoreColor(u.quality_score)};">${Math.round(u.quality_score)}</div><div style="font-size:0.7rem;color:var(--text-muted);">${u.issue_count} issues</div>`
            : `<span class="badge badge-medium">${u.status}</span>`}
        </div>
        ${u.status === 'completed'
          ? `<a href="/results/${u.id}" class="btn btn-secondary btn-sm" style="flex-shrink:0;">View →</a>`
          : ''}
      </div>
    `).join('');
  } catch (err) {
    list.innerHTML = `<div style="padding:20px;color:var(--danger);">Failed to load: ${err.message}</div>`;
  }
}
