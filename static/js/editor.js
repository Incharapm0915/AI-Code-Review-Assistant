/* Monaco Editor + Real-time Analysis */

let monacoEditor = null;
let analysisTimeout = null;
let currentDecorationIds = [];
let analysisRequestId = 0;
const DEBOUNCE_MS = 1000;

function initMonaco() {
  require.config({
    paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' }
  });

  require(['vs/editor/editor.main'], function () {
    const isDark = App.theme !== 'light';

    monacoEditor = monaco.editor.create(document.getElementById('monaco-editor'), {
      value: getDefaultCode('python'),
      language: 'python',
      theme: isDark ? 'vs-dark' : 'vs',
      fontSize: 14,
      fontFamily: '"JetBrains Mono", "Fira Code", Consolas, monospace',
      fontLigatures: true,
      lineNumbers: 'on',
      minimap: { enabled: true, scale: 0.8 },
      scrollBeyondLastLine: false,
      automaticLayout: true,
      tabSize: 4,
      insertSpaces: true,
      wordWrap: 'on',
      renderWhitespace: 'selection',
      bracketPairColorization: { enabled: true },
      guides: { bracketPairs: true, indentation: true },
      suggest: { showKeywords: true, showSnippets: true },
      quickSuggestions: true,
      autoClosingBrackets: 'always',
      autoClosingQuotes: 'always',
      formatOnPaste: true,
      formatOnType: false,
      smoothScrolling: true,
      cursorBlinking: 'smooth',
      cursorSmoothCaretAnimation: 'on',
      padding: { top: 16, bottom: 16 },
    });

    // Real-time analysis debounce
    monacoEditor.onDidChangeModelContent(() => {
      clearTimeout(analysisTimeout);
      updateLineCount();
      if (document.getElementById('realtime-toggle')?.checked) {
        const code = monacoEditor.getValue();
        if (!code.trim()) {
          clearMarkers();
          setLiveStatus('Waiting for code…', 'muted');
          document.getElementById('inline-results').style.display = 'none';
          return;
        }
        setLiveStatus('Typing…', 'muted');
        analysisTimeout = setTimeout(() => analyzeCode(true), DEBOUNCE_MS);
      }
    });

    // Update editor theme on theme change
    document.getElementById('theme-toggle')?.addEventListener('click', () => {
      setTimeout(() => {
        monaco.editor.setTheme(App.theme !== 'light' ? 'vs-dark' : 'vs');
      }, 100);
    });

    updateLineCount();
  });
}

function setEditorLanguage(lang) {
  if (!monacoEditor) return;
  const langMap = { python: 'python', javascript: 'javascript', java: 'java', cpp: 'cpp' };
  const monacoLang = langMap[lang] || 'python';
  monaco.editor.setModelLanguage(monacoEditor.getModel(), monacoLang);
}

function updateLineCount() {
  if (!monacoEditor) return;
  const lines = monacoEditor.getModel().getLineCount();
  const chars = monacoEditor.getValue().length;
  const lineEl = document.getElementById('line-count');
  const charEl = document.getElementById('char-count');
  if (lineEl) lineEl.textContent = `${lines} lines`;
  if (charEl) charEl.textContent = `${chars} chars`;
}

function getDefaultCode(lang) {
  const samples = {
    python: `# Sample Python Code - Paste your code here or start typing
import os
import hashlib
import pickle

def process_user_data(username, password, data):
    """Process user login and data."""
    # WARNING: Multiple security issues in this code

    # SQL injection vulnerability
    query = "SELECT * FROM users WHERE username = '" + username + "'"

    # Weak hashing
    pwd_hash = hashlib.md5(password.encode()).hexdigest()

    # Insecure deserialization
    user_prefs = pickle.loads(data)

    # Command injection
    os.system("echo " + username)

    # Bare except
    try:
        result = dangerous_operation()
    except:
        pass

    return pwd_hash

def dangerous_operation():
    pass
`,
    javascript: `// Sample JavaScript Code
const express = require('express');
const app = express();

// Security issues example
app.get('/search', (req, res) => {
    const query = req.query.q;

    // XSS vulnerability
    res.send('<div>' + query + '</div>');

    // Using var instead of const/let
    var result = [];

    // Direct innerHTML assignment
    document.getElementById('output').innerHTML = query;
});

// Missing error handling
app.listen(3000);
`,
    java: `// Sample Java Code
import java.sql.*;
import java.util.Random;

public class UserService {

    private Connection conn;

    public String authenticate(String username, String password) {
        // SQL Injection vulnerability
        String query = "SELECT * FROM users WHERE username = '" + username + "'";

        // Weak random number
        Random rand = new Random();
        String token = String.valueOf(rand.nextInt());

        try {
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery(query);
        } catch (Exception e) {
            e.printStackTrace();
        }

        return token;
    }
}
`,
    cpp: `// Sample C++ Code
#include <iostream>
#include <cstring>
#include <cstdio>

void processInput(char* input) {
    char buffer[64];

    // Buffer overflow vulnerability
    strcpy(buffer, input);

    // Unsafe printf
    printf(input);

    // Gets is deprecated and unsafe
    gets(buffer);

    std::cout << "Processing: " << buffer << std::endl;
}

int main() {
    char userInput[1024];
    scanf("%s", userInput);
    processInput(userInput);
    return 0;
}
`
  };
  return samples[lang] || samples.python;
}

async function analyzeCode(isRealtime = false) {
  if (!App.requireAuth()) return;

  const code = monacoEditor?.getValue() || document.getElementById('code-textarea')?.value || '';
  const language = document.getElementById('language-select')?.value || 'python';
  const title = document.getElementById('code-title')?.value || 'Untitled Snippet';

  if (!code.trim()) {
    Toast.warning('Empty Code', 'Please enter some code to analyze');
    return;
  }

  let myRequestId;
  if (!isRealtime) {
    Loading.show('Running AI analysis...');
  } else {
    // Tag this request so a slower, now-outdated response can never overwrite
    // the result of a newer one that finished first (was the cause of stale/
    // "incorrect" live results when typing fast).
    myRequestId = ++analysisRequestId;
    setLiveStatus('Analyzing…', 'muted');
  }

  const analyzeBtn = document.getElementById('analyze-btn');
  if (!isRealtime && analyzeBtn) { analyzeBtn.disabled = true; analyzeBtn.innerHTML = '<div class="spinner" style="width:16px;height:16px;border-width:2px;"></div> Analyzing...'; }

  try {
    const res = await API.post('/api/analyze', { code, language, title });
    if (isRealtime && myRequestId !== analysisRequestId) return; // a newer request already superseded this one

    if (res?.data?.report) {
      if (!isRealtime) {
        Loading.hide();
        window.location.href = `/results/${res.data.report_id}`;
      } else {
        renderInlineResults(res.data.report);
      }
    }
  } catch (err) {
    if (isRealtime && myRequestId !== analysisRequestId) return;
    Loading.hide();
    if (isRealtime) {
      setLiveStatus('Analysis failed', 'danger');
    } else {
      Toast.error('Analysis failed', err.message);
    }
  } finally {
    if (!isRealtime) {
      if (analyzeBtn) { analyzeBtn.disabled = false; analyzeBtn.innerHTML = '🔍 Analyze Code'; }
      Loading.hide();
    }
  }
}

// Merge style/bug issues and security vulnerabilities into one line-anchored list
function combineFindings(report) {
  const issues = (report.issues || []).map(i => ({
    line: i.line || 1,
    severity: i.severity || 'info',
    title: i.message,
    detail: i.code_snippet || '',
    kind: 'issue'
  }));
  const vulns = (report.vulnerabilities_list || report.vulnerabilities_data || []).map(v => ({
    line: v.line || 1,
    severity: v.severity || 'medium',
    title: `${v.category}: ${v.description}`,
    detail: v.recommendation || '',
    kind: 'vulnerability'
  }));
  const order = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
  return [...vulns, ...issues].sort((a, b) =>
    (order[a.severity] ?? 5) - (order[b.severity] ?? 5) || a.line - b.line
  );
}

function renderInlineResults(report) {
  const panel = document.getElementById('inline-results');
  if (!panel) return;

  panel.style.display = 'block';

  document.getElementById('ir-score').textContent = Math.round(report.quality_score);
  document.getElementById('ir-issues').textContent = report.total_issues;
  document.getElementById('ir-vulns').textContent = report.vulnerabilities;
  document.getElementById('ir-grade').textContent = report.scores?.grade || 'N/A';

  const findings = combineFindings(report);

  // Mark exact lines in the editor itself: squiggly underline + gutter dot + line tint
  applyMarkers(findings);

  if (findings.length) {
    const worst = findings[0].severity;
    const level = (worst === 'critical' || worst === 'high') ? 'danger' : (worst === 'medium' ? 'warning' : 'muted');
    setLiveStatus(`Up to date · ${findings.length} finding${findings.length === 1 ? '' : 's'}`, level);
  } else {
    setLiveStatus('Up to date · no issues found', 'success');
  }

  const issuesEl = document.getElementById('ir-issue-list');
  if (issuesEl) {
    issuesEl.innerHTML = findings.length ? findings.map(f => `
      <div class="issue-item" style="cursor:pointer;" onclick="jumpToLine(${f.line})" title="Click to jump to line ${f.line}">
        <div class="issue-line-indicator ${f.severity}"></div>
        <div class="issue-content">
          <div class="issue-header">
            ${createBadge(f.severity)}
            <span class="issue-message">${escapeHtml(f.title)}</span>
            <span class="issue-line">Line ${f.line}</span>
          </div>
          ${f.detail ? `<div class="issue-snippet">${escapeHtml(f.detail)}</div>` : ''}
        </div>
      </div>
    `).join('') : `<div style="padding:16px 0;color:var(--text-muted);font-size:0.85rem;text-align:center;">✅ No issues detected.</div>`;
  }
}

// Show a short status line next to the "Real-time" pulse dot
function setLiveStatus(text, level) {
  const el = document.getElementById('ir-status-text');
  if (!el) return;
  const colors = { muted: 'var(--text-muted)', success: 'var(--success)', warning: 'var(--warning)', danger: 'var(--danger)' };
  el.textContent = text;
  el.style.color = colors[level] || colors.muted;
}

// Put real squiggly-underline error/warning markers directly in the code, at the exact line,
// plus a gutter dot and a soft line tint so the problem line is visible without hovering.
function applyMarkers(findings) {
  if (!monacoEditor || !window.monaco) return;
  const model = monacoEditor.getModel();
  if (!model) return;

  const sevToMonaco = {
    critical: monaco.MarkerSeverity.Error,
    high: monaco.MarkerSeverity.Error,
    medium: monaco.MarkerSeverity.Warning,
    low: monaco.MarkerSeverity.Info,
    info: monaco.MarkerSeverity.Hint,
  };

  const lineCount = model.getLineCount();
  const markers = findings.map(f => {
    const line = Math.min(Math.max(f.line || 1, 1), lineCount);
    return {
      severity: sevToMonaco[f.severity] || monaco.MarkerSeverity.Info,
      message: f.kind === 'vulnerability' ? `Security: ${f.title}` : f.title,
      startLineNumber: line,
      startColumn: 1,
      endLineNumber: line,
      endColumn: model.getLineMaxColumn(line),
    };
  });
  monaco.editor.setModelMarkers(model, 'ai-review', markers);

  const decorations = findings.map(f => {
    const line = Math.min(Math.max(f.line || 1, 1), lineCount);
    return {
      range: new monaco.Range(line, 1, line, 1),
      options: {
        isWholeLine: true,
        className: `issue-line-${f.severity}`,
        glyphMarginClassName: `glyph-${f.severity}`,
        glyphMarginHoverMessage: { value: f.title },
      }
    };
  });
  currentDecorationIds = monacoEditor.deltaDecorations(currentDecorationIds, decorations);
}

function clearMarkers() {
  if (!monacoEditor || !window.monaco) return;
  const model = monacoEditor.getModel();
  if (model) monaco.editor.setModelMarkers(model, 'ai-review', []);
  currentDecorationIds = monacoEditor.deltaDecorations(currentDecorationIds, []);
}

// Move the cursor to a finding's line when its card in the side panel is clicked
function jumpToLine(line) {
  if (!monacoEditor) return;
  monacoEditor.revealLineInCenter(line);
  monacoEditor.setPosition({ lineNumber: line, column: 1 });
  monacoEditor.focus();
}
window.jumpToLine = jumpToLine;

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function clearEditor() {
  if (monacoEditor) {
    monacoEditor.setValue('');
  } else {
    const ta = document.getElementById('code-textarea');
    if (ta) ta.value = '';
  }
  clearMarkers();
  const panel = document.getElementById('inline-results');
  if (panel) panel.style.display = 'none';
  document.getElementById('run-output-panel')?.classList.remove('open');
}

function copyCode() {
  const code = monacoEditor?.getValue() || document.getElementById('code-textarea')?.value || '';
  navigator.clipboard.writeText(code).then(() => Toast.success('Copied!', 'Code copied to clipboard'));
}

function loadSampleCode() {
  const lang = document.getElementById('language-select')?.value || 'python';
  const sample = getDefaultCode(lang);
  if (monacoEditor) monacoEditor.setValue(sample);
  Toast.info('Sample loaded', `${lang} sample code loaded`);
}

// Actually execute the code server-side and show real stdout/stderr — distinct
// from the static "Analyze" pass above, which never runs the code at all.
async function runCode() {
  if (!App.requireAuth()) return;

  const code = monacoEditor?.getValue() || '';
  const language = document.getElementById('language-select')?.value || 'python';
  const stdin = document.getElementById('run-stdin')?.value || '';

  if (!code.trim()) {
    Toast.warning('Empty Code', 'Please enter some code to run');
    return;
  }

  const panel = document.getElementById('run-output-panel');
  const body = document.getElementById('run-output-body');
  const status = document.getElementById('run-status-text');
  const runBtn = document.getElementById('run-btn');

  panel.classList.add('open');
  status.textContent = 'Running…';
  status.style.color = 'var(--text-muted)';
  body.innerHTML = `<div style="color:var(--text-muted);">Executing ${escapeHtml(language)} code…</div>`;
  if (runBtn) { runBtn.disabled = true; runBtn.innerHTML = '<div class="spinner" style="width:14px;height:14px;border-width:2px;"></div> Running...'; }

  try {
    const res = await API.post('/api/execute', { code, language, stdin });
    const r = res?.data;
    if (!r) return;

    const parts = [];
    if (r.stdout) parts.push(`<div class="run-output-block run-output-stdout">${escapeHtml(r.stdout)}</div>`);
    if (r.stderr) parts.push(`<div class="run-output-block run-output-stderr">${escapeHtml(r.stderr)}</div>`);
    if (!r.stdout && !r.stderr) parts.push(`<div style="color:var(--text-muted);">(no output)</div>`);
    body.innerHTML = parts.join('');

    if (r.timed_out) {
      status.textContent = `Timed out after ${Math.round(r.duration_ms / 1000)}s`;
      status.style.color = 'var(--danger)';
    } else if (r.exit_code === 0) {
      status.textContent = `Finished · exit code 0 · ${r.duration_ms}ms`;
      status.style.color = 'var(--success)';
    } else {
      const stage = r.stage === 'compile' ? 'Compile error' : 'Runtime error';
      status.textContent = `${stage} · exit code ${r.exit_code} · ${r.duration_ms}ms`;
      status.style.color = 'var(--danger)';
    }
  } catch (err) {
    body.innerHTML = `<div class="run-output-block run-output-stderr">${escapeHtml(err.message)}</div>`;
    status.textContent = 'Could not run';
    status.style.color = 'var(--danger)';
  } finally {
    if (runBtn) { runBtn.disabled = false; runBtn.innerHTML = '▶ Run'; }
  }
}

// Language change handler
document.addEventListener('DOMContentLoaded', () => {
  const langSelect = document.getElementById('language-select');
  if (langSelect) {
    langSelect.addEventListener('change', (e) => {
      setEditorLanguage(e.target.value);
    });
  }

  const analyzeBtn = document.getElementById('analyze-btn');
  if (analyzeBtn) analyzeBtn.addEventListener('click', () => analyzeCode());

  const clearBtn = document.getElementById('clear-btn');
  if (clearBtn) clearBtn.addEventListener('click', clearEditor);

  const copyBtn = document.getElementById('copy-btn');
  if (copyBtn) copyBtn.addEventListener('click', copyCode);

  const sampleBtn = document.getElementById('sample-btn');
  if (sampleBtn) sampleBtn.addEventListener('click', loadSampleCode);

  const runBtn = document.getElementById('run-btn');
  if (runBtn) runBtn.addEventListener('click', runCode);

  const runCloseBtn = document.getElementById('run-output-close');
  if (runCloseBtn) runCloseBtn.addEventListener('click', () => {
    document.getElementById('run-output-panel').classList.remove('open');
  });

  const runStdinToggle = document.getElementById('run-stdin-toggle');
  if (runStdinToggle) runStdinToggle.addEventListener('click', () => {
    const row = document.getElementById('run-stdin-row');
    row.style.display = row.style.display === 'none' ? 'flex' : 'none';
  });

  // Init Monaco if editor div exists
  if (document.getElementById('monaco-editor') && typeof require !== 'undefined') {
    initMonaco();
  }
});
