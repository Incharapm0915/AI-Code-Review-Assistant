/* Monaco Editor + Real-time Analysis */

let monacoEditor = null;
let analysisTimeout = null;
const DEBOUNCE_MS = 1500;

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

  if (!isRealtime) Loading.show('Running AI analysis...');

  const analyzeBtn = document.getElementById('analyze-btn');
  if (analyzeBtn) { analyzeBtn.disabled = true; analyzeBtn.innerHTML = '<div class="spinner" style="width:16px;height:16px;border-width:2px;"></div> Analyzing...'; }

  try {
    const res = await API.post('/api/analyze', { code, language, title });

    if (res?.data?.report) {
      if (!isRealtime) {
        Loading.hide();
        window.location.href = `/results/${res.data.report_id}`;
      } else {
        renderInlineResults(res.data.report);
      }
    }
  } catch (err) {
    Loading.hide();
    Toast.error('Analysis failed', err.message);
  } finally {
    if (analyzeBtn) { analyzeBtn.disabled = false; analyzeBtn.innerHTML = '🔍 Analyze Code'; }
    if (!isRealtime) Loading.hide();
  }
}

function renderInlineResults(report) {
  const panel = document.getElementById('inline-results');
  if (!panel) return;

  panel.style.display = 'block';

  const issues = report.issues || [];
  const critical = issues.filter(i => i.severity === 'critical').length;
  const high = issues.filter(i => i.severity === 'high').length;

  document.getElementById('ir-score').textContent = Math.round(report.quality_score);
  document.getElementById('ir-issues').textContent = report.total_issues;
  document.getElementById('ir-vulns').textContent = report.vulnerabilities;
  document.getElementById('ir-grade').textContent = report.scores?.grade || 'N/A';

  // Highlight problematic lines in editor
  if (monacoEditor && issues.length) {
    highlightIssueLines(issues);
  }

  // Show top issues
  const issuesEl = document.getElementById('ir-issue-list');
  if (issuesEl) {
    issuesEl.innerHTML = issues.slice(0, 5).map(issue => `
      <div class="issue-item">
        <div class="issue-line-indicator ${issue.severity}"></div>
        <div class="issue-content">
          <div class="issue-header">
            ${createBadge(issue.severity)}
            <span class="issue-message">${issue.message}</span>
            <span class="issue-line">Line ${issue.line}</span>
          </div>
          ${issue.code_snippet ? `<div class="issue-snippet">${escapeHtml(issue.code_snippet)}</div>` : ''}
        </div>
      </div>
    `).join('');
  }
}

function highlightIssueLines(issues) {
  if (!monacoEditor || !monaco) return;

  const decorations = issues.map(issue => ({
    range: new monaco.Range(issue.line, 1, issue.line, 1),
    options: {
      isWholeLine: true,
      className: `issue-line-${issue.severity}`,
      glyphMarginClassName: `glyph-${issue.severity}`,
      overviewRulerColor: getSeverityHex(issue.severity),
      overviewRulerLane: monaco.editor.OverviewRulerLane.Right,
      minimap: { color: getSeverityHex(issue.severity), position: 1 },
      hoverMessage: { value: `**${issue.severity.toUpperCase()}**: ${issue.message}` }
    }
  }));

  monacoEditor.deltaDecorations([], decorations);
}

function getSeverityHex(severity) {
  const colors = { critical: '#dc2626', high: '#ea580c', medium: '#d97706', low: '#3b82f6', info: '#6b7280' };
  return colors[severity] || '#6b7280';
}

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
  const panel = document.getElementById('inline-results');
  if (panel) panel.style.display = 'none';
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

  // Init Monaco if editor div exists
  if (document.getElementById('monaco-editor') && typeof require !== 'undefined') {
    initMonaco();
  }
});
