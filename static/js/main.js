/* ═══════════════════════════════════════════════════════════════════
   AI Code Review Assistant — Core JavaScript
═══════════════════════════════════════════════════════════════════ */

// ── State ──────────────────────────────────────────────────────────
const App = {
  token: localStorage.getItem('access_token'),
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  theme: localStorage.getItem('theme') || 'dark',
};

// ── API Client ─────────────────────────────────────────────────────
const API = {
  base: '',

  async request(method, url, data = null, isFormData = false) {
    const headers = {};
    if (App.token) headers['Authorization'] = `Bearer ${App.token}`;
    if (!isFormData) headers['Content-Type'] = 'application/json';

    const options = { method, headers };
    if (data) options.body = isFormData ? data : JSON.stringify(data);

    try {
      const res = await fetch(url, options);

      if (res.status === 401) {
        App.logout();
        return null;
      }

      const json = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(json.error || `HTTP ${res.status}`);
      }
      return json;
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error(`API Error [${method} ${url}]:`, err.message);
      }
      throw err;
    }
  },

  get: (url) => API.request('GET', url),
  post: (url, data) => API.request('POST', url, data),
  put: (url, data) => API.request('PUT', url, data),
  delete: (url) => API.request('DELETE', url),
  upload: (url, formData) => API.request('POST', url, formData, true),
};

// ── Auth ───────────────────────────────────────────────────────────
App.setAuth = function (user, token) {
  App.token = token;
  App.user = user;
  localStorage.setItem('access_token', token);
  localStorage.setItem('user', JSON.stringify(user));
};

App.logout = function () {
  App.token = null;
  App.user = null;
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  window.location.href = '/login';
};

App.isAuthenticated = function () {
  return !!App.token && !!App.user;
};

App.requireAuth = function () {
  if (!App.isAuthenticated()) {
    window.location.href = '/login';
    return false;
  }
  return true;
};

App.isAdmin = function () {
  return App.user && App.user.role === 'admin';
};

// ── Toast Notifications ────────────────────────────────────────────
const Toast = {
  container: null,

  init() {
    this.container = document.getElementById('toast-container');
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      document.body.appendChild(this.container);
    }
  },

  show(title, message = '', type = 'info', duration = 4000) {
    if (!this.container) this.init();

    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    };

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
      <div class="toast-body">
        <div class="toast-title">${title}</div>
        ${message ? `<div class="toast-message">${message}</div>` : ''}
      </div>
      <span class="toast-close" onclick="this.parentElement.remove()">×</span>
    `;

    this.container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(30px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  success: (t, m) => Toast.show(t, m, 'success'),
  error: (t, m) => Toast.show(t, m, 'error'),
  warning: (t, m) => Toast.show(t, m, 'warning'),
  info: (t, m) => Toast.show(t, m, 'info'),
};

// ── Loading Overlay ────────────────────────────────────────────────
const Loading = {
  overlay: null,

  show(message = 'Analyzing code...') {
    this.overlay = document.getElementById('loading-overlay');
    if (!this.overlay) {
      this.overlay = document.createElement('div');
      this.overlay.id = 'loading-overlay';
      this.overlay.className = 'loading-overlay';
      this.overlay.innerHTML = `
        <div class="loading-spinner"></div>
        <p id="loading-message" style="color:var(--text-secondary);font-weight:600;">${message}</p>
        <p style="color:var(--text-muted);font-size:0.85rem;margin-top:8px;">Please wait while AI analyzes your code...</p>
      `;
      document.body.appendChild(this.overlay);
    } else {
      document.getElementById('loading-message').textContent = message;
      this.overlay.style.display = 'flex';
    }
  },

  hide() {
    if (this.overlay) this.overlay.style.display = 'none';
  }
};

// ── Theme ──────────────────────────────────────────────────────────
const Theme = {
  apply(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    App.theme = theme;
    localStorage.setItem('theme', theme);

    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
      toggle.classList.toggle('light', theme === 'light');
    }
  },

  toggle() {
    const newTheme = App.theme === 'dark' ? 'light' : 'dark';
    Theme.apply(newTheme);
  },

  init() {
    Theme.apply(App.theme);
  }
};

// ── Sidebar ────────────────────────────────────────────────────────
const Sidebar = {
  isOpen: false,

  toggle() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    this.isOpen = !this.isOpen;
    sidebar.classList.toggle('open', this.isOpen);
  },

  setActive(path) {
    document.querySelectorAll('.nav-item').forEach(item => {
      const href = item.getAttribute('href') || '';
      item.classList.toggle('active', href === path || window.location.pathname === href);
    });
  },

  init() {
    this.setActive(window.location.pathname);
  }
};

// ── UI Helpers ─────────────────────────────────────────────────────
function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatDateTime(iso) {
  const d = new Date(iso);
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

function getScoreColor(score) {
  if (score >= 85) return '#10b981';
  if (score >= 70) return '#3b82f6';
  if (score >= 55) return '#f59e0b';
  if (score >= 40) return '#ef4444';
  return '#dc2626';
}

function getSeverityClass(severity) {
  const map = { critical: 'critical', high: 'high', medium: 'medium', low: 'low', info: 'info' };
  return map[severity] || 'info';
}

function animateCount(el, target, duration = 1500) {
  const start = 0;
  const startTime = performance.now();

  const update = (currentTime) => {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + (target - start) * eased);
    if (progress < 1) requestAnimationFrame(update);
  };

  requestAnimationFrame(update);
}

function createScoreRing(score, size = 80, strokeWidth = 6) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = getScoreColor(score);

  return `
    <div class="score-ring" style="width:${size}px;height:${size}px;">
      <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
        <circle class="track" cx="${size/2}" cy="${size/2}" r="${radius}" stroke-width="${strokeWidth}"/>
        <circle class="progress" cx="${size/2}" cy="${size/2}" r="${radius}"
          stroke="${color}" stroke-width="${strokeWidth}"
          stroke-dasharray="${circumference}"
          stroke-dashoffset="${offset}"/>
      </svg>
      <div class="score-text">
        <span style="color:${color}">${Math.round(score)}</span>
        <span class="score-label">Score</span>
      </div>
    </div>
  `;
}

function createBadge(severity) {
  const labels = { critical: 'Critical', high: 'High', medium: 'Medium', low: 'Low', info: 'Info' };
  return `<span class="badge badge-${severity}">${labels[severity] || severity}</span>`;
}

// ── Modal ──────────────────────────────────────────────────────────
const Modal = {
  show(content, title = '') {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
      <div class="modal">
        <div class="modal-header">
          <h3 class="modal-title">${title}</h3>
          <span class="modal-close" onclick="Modal.close()">×</span>
        </div>
        <div class="modal-body">${content}</div>
      </div>
    `;
    overlay.addEventListener('click', (e) => { if (e.target === overlay) Modal.close(); });
    document.body.appendChild(overlay);
    document.body.style.overflow = 'hidden';
  },

  close() {
    const overlay = document.querySelector('.modal-overlay');
    if (overlay) {
      overlay.style.animation = 'fadeIn 0.2s ease reverse';
      setTimeout(() => overlay.remove(), 200);
    }
    document.body.style.overflow = '';
  }
};

// ── User UI ────────────────────────────────────────────────────────
function updateUserUI() {
  if (!App.user) return;

  const nameEls = document.querySelectorAll('[data-user-name]');
  const avatarEls = document.querySelectorAll('[data-user-avatar]');
  const roleEls = document.querySelectorAll('[data-user-role]');

  const initials = (App.user.full_name || App.user.username || 'U').charAt(0).toUpperCase();

  nameEls.forEach(el => { el.textContent = App.user.full_name || App.user.username; });
  avatarEls.forEach(el => { el.textContent = initials; });
  roleEls.forEach(el => { el.textContent = App.user.role === 'admin' ? '⚡ Admin' : '👤 Developer'; });

  const adminLinks = document.querySelectorAll('[data-admin-only]');
  adminLinks.forEach(el => { el.style.display = App.isAdmin() ? '' : 'none'; });
}

// ── Initialize ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  Toast.init();
  Theme.init();
  Sidebar.init();
  updateUserUI();

  // Mobile menu toggle
  const menuToggle = document.getElementById('menu-toggle');
  if (menuToggle) menuToggle.addEventListener('click', Sidebar.toggle.bind(Sidebar));

  // Theme toggle
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) themeToggle.addEventListener('click', Theme.toggle.bind(Theme));

  // Logout button
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      try { await API.post('/api/auth/logout'); } catch (_) {}
      App.logout();
    });
  }

  // Close sidebar on outside click (mobile)
  document.addEventListener('click', (e) => {
    const sidebar = document.querySelector('.sidebar');
    const toggle = document.getElementById('menu-toggle');
    if (sidebar && Sidebar.isOpen && !sidebar.contains(e.target) && !toggle?.contains(e.target)) {
      Sidebar.toggle();
    }
  });

  // Animate numbers on page load
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseInt(el.dataset.count, 10);
    if (!isNaN(target)) animateCount(el, target);
  });

  // Intersection observer for animations
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-fade-up');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('[data-animate]').forEach(el => observer.observe(el));
});

// ── Export Globals ─────────────────────────────────────────────────
window.App = App;
window.API = API;
window.Toast = Toast;
window.Loading = Loading;
window.Theme = Theme;
window.Modal = Modal;
window.formatDate = formatDate;
window.formatDateTime = formatDateTime;
window.formatBytes = formatBytes;
window.getScoreColor = getScoreColor;
window.getSeverityClass = getSeverityClass;
window.animateCount = animateCount;
window.createScoreRing = createScoreRing;
window.createBadge = createBadge;
