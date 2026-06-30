/* Auth page shared utilities */

function validatePasswordStrength(password) {
  const checks = {
    length:    password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number:    /\d/.test(password),
    special:   /[^A-Za-z0-9]/.test(password),
  };
  const passed = Object.values(checks).filter(Boolean).length;
  return { checks, strength: passed, percentage: passed * 20 };
}

function getStrengthLabel(strength) {
  const labels = ['', 'Very Weak', 'Weak', 'Fair', 'Strong', 'Very Strong'];
  const colors = ['', '#ef4444', '#f59e0b', '#f59e0b', '#3b82f6', '#10b981'];
  return { label: labels[strength] || '', color: colors[strength] || '' };
}

function togglePasswordVisibility(inputId) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.type = input.type === 'password' ? 'text' : 'password';
}

function showFormError(bannerId, message) {
  const el = document.getElementById(bannerId);
  if (!el) return;
  el.textContent = message;
  el.style.display = 'block';
  el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideFormError(bannerId) {
  const el = document.getElementById(bannerId);
  if (el) el.style.display = 'none';
}

function setButtonLoading(btnId, loading, defaultText = 'Submit') {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = loading;
  btn.innerHTML = loading
    ? '<div class="spinner" style="width:18px;height:18px;border-width:2px;"></div> Please wait...'
    : defaultText;
}
