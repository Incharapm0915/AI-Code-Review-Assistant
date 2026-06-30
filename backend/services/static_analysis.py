import ast
import re
import tokenize
import io
from typing import List, Dict, Any


LANGUAGE_PATTERNS = {
    'python': {
        'bad_practices': [
            (r'\bexec\s*\(', 'Use of exec() is dangerous and should be avoided', 'high'),
            (r'\beval\s*\(', 'Use of eval() is dangerous and can execute arbitrary code', 'high'),
            (r'__import__\s*\(', 'Dynamic imports with __import__ can be a security risk', 'medium'),
            (r'input\s*\(.*\)', 'Validate and sanitize all user inputs', 'low'),
            (r'print\s*\(', 'Replace print() with proper logging in production', 'info'),
            (r'#\s*TODO|#\s*FIXME|#\s*HACK|#\s*XXX', 'Unresolved TODO/FIXME comment found', 'info'),
            (r'except\s*:', 'Bare except clause catches all exceptions including SystemExit', 'medium'),
            (r'except\s+Exception\s*:', 'Catching broad Exception masks specific errors', 'low'),
            (r'global\s+\w+', 'Global variable usage makes code harder to test and maintain', 'low'),
            (r'lambda\s+.*:.*lambda', 'Nested lambda expressions reduce readability', 'low'),
            (r'assert\s+', 'Assertions can be disabled with -O flag, use proper validation', 'info'),
            (r'time\.sleep\s*\(', 'Blocking sleep in production code may cause performance issues', 'low'),
        ],
        'security': [
            (r'pickle\.loads?\s*\(', 'pickle is vulnerable to arbitrary code execution', 'critical'),
            (r'subprocess\.call\s*\(.*shell\s*=\s*True', 'Shell injection risk with shell=True', 'critical'),
            (r'os\.system\s*\(', 'os.system() is vulnerable to command injection', 'critical'),
            (r'hashlib\.md5\s*\(', 'MD5 is cryptographically broken, use SHA-256 or better', 'high'),
            (r'hashlib\.sha1\s*\(', 'SHA-1 is cryptographically weak, use SHA-256 or better', 'high'),
            (r'random\.\w+\s*\(', 'random module is not cryptographically secure, use secrets module', 'medium'),
            (r'open\s*\(.*["\']w["\']', 'File write operation detected, ensure proper path validation', 'low'),
            (r'flask\.request\.args', 'Validate and sanitize all query parameters', 'low'),
            (r'sql\s*=\s*["\'].*%s', 'Potential SQL injection via string formatting', 'critical'),
            (r'cursor\.execute\s*\(.*%\s*\(', 'Potential SQL injection detected', 'critical'),
            (r'yaml\.load\s*\((?!.*Loader)', 'yaml.load() without Loader is unsafe, use yaml.safe_load()', 'high'),
        ],
        'style': [
            (r'\bif\s+\w+\s*==\s*True\b', 'Compare with True using "if x:" instead of "if x == True:"', 'info'),
            (r'\bif\s+\w+\s*==\s*False\b', 'Compare with False using "if not x:" instead of "if x == False:"', 'info'),
            (r'\bif\s+\w+\s*==\s*None\b', 'Use "is None" instead of "== None"', 'info'),
            (r'\t', 'Use spaces instead of tabs for indentation (PEP 8)', 'info'),
            (r'.{120,}', 'Line exceeds 120 characters (PEP 8 recommends max 79)', 'info'),
        ]
    },
    'javascript': {
        'bad_practices': [
            (r'\beval\s*\(', 'eval() is dangerous and can execute arbitrary code', 'high'),
            (r'document\.write\s*\(', 'document.write() can lead to XSS vulnerabilities', 'high'),
            (r'innerHTML\s*=\s*(?!["\'`]\s*["\'`])', 'Direct innerHTML assignment can cause XSS', 'high'),
            (r'var\s+\w+', 'Use let/const instead of var for proper scoping', 'low'),
            (r'==\s*(?![\s>])', 'Use === (strict equality) instead of == to avoid type coercion', 'low'),
            (r'console\.log\s*\(', 'Remove console.log() statements in production code', 'info'),
            (r'debugger;', 'Remove debugger statement before deployment', 'medium'),
            (r'TODO|FIXME|HACK', 'Unresolved TODO/FIXME found', 'info'),
            (r'catch\s*\(.*\)\s*\{\s*\}', 'Empty catch block silently swallows errors', 'medium'),
            (r'setTimeout\s*\(.*,\s*0\)', 'setTimeout with 0ms delay is an anti-pattern', 'info'),
        ],
        'security': [
            (r'localStorage\.setItem\s*\(.*password', 'Never store passwords in localStorage', 'critical'),
            (r'sessionStorage\.setItem\s*\(.*token', 'Storing tokens in sessionStorage may be insecure', 'medium'),
            (r'http://', 'Use HTTPS instead of HTTP for security', 'medium'),
            (r'new\s+Function\s*\(', 'new Function() is equivalent to eval() and is dangerous', 'high'),
            (r'\.src\s*=\s*(?!["\'`])', 'Dynamic src assignment can lead to XSS', 'medium'),
        ],
        'style': [
            (r'function\s+\w+\s*\([^)]*\)\s*\{(?:[^}]*\n){30,}', 'Function exceeds 30 lines, consider refactoring', 'low'),
        ]
    },
    'java': {
        'bad_practices': [
            (r'System\.out\.print', 'Use proper logging framework instead of System.out', 'info'),
            (r'e\.printStackTrace\(\)', 'Use logger instead of printStackTrace()', 'low'),
            (r'catch\s*\(\s*Exception\s+\w+\s*\)\s*\{\s*\}', 'Empty catch block detected', 'medium'),
            (r'Thread\.sleep\s*\(', 'Thread.sleep() blocks the thread and is often a code smell', 'low'),
            (r'//\s*TODO|//\s*FIXME', 'Unresolved TODO/FIXME comment', 'info'),
            (r'public\s+static\s+\w+\s+\w+\s*=', 'Public static mutable field detected', 'medium'),
        ],
        'security': [
            (r'Runtime\.getRuntime\(\)\.exec\s*\(', 'Command injection risk via Runtime.exec()', 'critical'),
            (r'MessageDigest\.getInstance\s*\(\s*"MD5"\s*\)', 'MD5 is cryptographically broken', 'high'),
            (r'MessageDigest\.getInstance\s*\(\s*"SHA-1"\s*\)', 'SHA-1 is cryptographically weak', 'high'),
            (r'new\s+Random\s*\(\)', 'java.util.Random is not cryptographically secure', 'medium'),
            (r'Statement\s+\w+\s*=.*createStatement', 'Use PreparedStatement to prevent SQL injection', 'critical'),
        ],
        'style': []
    },
    'cpp': {
        'bad_practices': [
            (r'gets\s*\(', 'gets() is unsafe and deprecated, use fgets() instead', 'critical'),
            (r'strcpy\s*\(', 'strcpy() is unsafe, use strncpy() or std::string', 'high'),
            (r'sprintf\s*\(', 'sprintf() can overflow buffer, use snprintf()', 'high'),
            (r'scanf\s*\(.*%s', 'scanf with %s can overflow buffer, specify width limit', 'high'),
            (r'malloc\s*\(', 'Ensure malloc() return value is checked for NULL', 'medium'),
            (r'free\s*\(', 'Ensure no double-free or use-after-free vulnerabilities', 'medium'),
            (r'//\s*TODO|//\s*FIXME', 'Unresolved TODO/FIXME comment', 'info'),
            (r'using namespace std;', 'Avoid "using namespace std;" in header files', 'low'),
        ],
        'security': [
            (r'system\s*\(', 'system() is vulnerable to command injection', 'critical'),
            (r'strcat\s*\(', 'strcat() can overflow buffer, use strncat()', 'high'),
            (r'printf\s*\(\s*\w+\s*\)', 'Format string vulnerability - use printf("%s", str)', 'critical'),
        ],
        'style': []
    }
}

DUPLICATE_THRESHOLD = 6  # Minimum lines to consider a duplicate block


class StaticAnalyzer:

    def analyze(self, code: str, language: str) -> Dict[str, Any]:
        issues = []
        lines = code.split('\n')

        pattern_issues = self._check_patterns(code, lines, language)
        issues.extend(pattern_issues)

        if language == 'python':
            ast_issues = self._analyze_python_ast(code)
            issues.extend(ast_issues)

        duplicate_issues = self._detect_duplicates(lines, language)
        issues.extend(duplicate_issues)

        complexity_data = self._calculate_complexity(code, language)

        style_issues = self._check_style(lines, language)
        issues.extend(style_issues)

        return {
            'issues': issues,
            'complexity': complexity_data,
            'total_lines': len(lines),
            'blank_lines': sum(1 for l in lines if not l.strip()),
            'comment_lines': self._count_comments(lines, language),
        }

    def _check_patterns(self, code: str, lines: List[str], language: str) -> List[Dict]:
        issues = []
        lang_patterns = LANGUAGE_PATTERNS.get(language, {})

        for category, patterns in lang_patterns.items():
            for pattern, message, severity in patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        issues.append({
                            'type': 'pattern',
                            'category': category,
                            'severity': severity,
                            'line': i,
                            'message': message,
                            'code_snippet': line.strip(),
                            'column': None
                        })
        return issues

    def _analyze_python_ast(self, code: str) -> List[Dict]:
        issues = []
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return [{
                'type': 'syntax_error',
                'category': 'syntax',
                'severity': 'critical',
                'line': e.lineno or 0,
                'message': f'Syntax error: {e.msg}',
                'code_snippet': e.text or '',
                'column': e.offset
            }]

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Detect functions with too many arguments
                if len(node.args.args) > 7:
                    issues.append({
                        'type': 'ast',
                        'category': 'maintainability',
                        'severity': 'medium',
                        'line': node.lineno,
                        'message': f'Function "{node.name}" has {len(node.args.args)} parameters (max recommended: 7)',
                        'code_snippet': f'def {node.name}(...)',
                        'column': None
                    })

                # Detect missing docstrings on public functions
                if not (isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)):
                    if not node.name.startswith('_'):
                        issues.append({
                            'type': 'ast',
                            'category': 'documentation',
                            'severity': 'info',
                            'line': node.lineno,
                            'message': f'Public function "{node.name}" is missing a docstring',
                            'code_snippet': f'def {node.name}(...)',
                            'column': None
                        })

                # Detect very long functions
                func_lines = (node.end_lineno or node.lineno) - node.lineno
                if func_lines > 50:
                    issues.append({
                        'type': 'ast',
                        'category': 'complexity',
                        'severity': 'medium',
                        'line': node.lineno,
                        'message': f'Function "{node.name}" is {func_lines} lines long (max recommended: 50)',
                        'code_snippet': f'def {node.name}(...)',
                        'column': None
                    })

            elif isinstance(node, ast.ClassDef):
                if not (node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)):
                    issues.append({
                        'type': 'ast',
                        'category': 'documentation',
                        'severity': 'info',
                        'line': node.lineno,
                        'message': f'Class "{node.name}" is missing a docstring',
                        'code_snippet': f'class {node.name}:',
                        'column': None
                    })

            elif isinstance(node, ast.For):
                # Detect nested loops
                for child in ast.walk(node):
                    if child is not node and isinstance(child, (ast.For, ast.While)):
                        issues.append({
                            'type': 'ast',
                            'category': 'performance',
                            'severity': 'low',
                            'line': node.lineno,
                            'message': 'Nested loop detected - consider using list comprehension or numpy operations',
                            'code_snippet': 'for ... for ...',
                            'column': None
                        })
                        break

            elif isinstance(node, ast.Try):
                for handler in node.handlers:
                    if handler.type is None:
                        issues.append({
                            'type': 'ast',
                            'category': 'error_handling',
                            'severity': 'medium',
                            'line': handler.lineno,
                            'message': 'Bare except clause - specify the exception type',
                            'code_snippet': 'except:',
                            'column': None
                        })

        return issues

    def _detect_duplicates(self, lines: List[str], language: str) -> List[Dict]:
        issues = []
        meaningful_lines = [(i + 1, l.strip()) for i, l in enumerate(lines) if l.strip() and not l.strip().startswith('#')]

        seen_blocks = {}
        for i in range(len(meaningful_lines) - DUPLICATE_THRESHOLD):
            block = tuple(l for _, l in meaningful_lines[i:i + DUPLICATE_THRESHOLD])
            key = '\n'.join(block)
            if len(key) > 50:
                if key in seen_blocks:
                    issues.append({
                        'type': 'duplicate',
                        'category': 'duplication',
                        'severity': 'medium',
                        'line': meaningful_lines[i][0],
                        'message': f'Duplicate code block detected (first seen at line {seen_blocks[key]})',
                        'code_snippet': block[0],
                        'column': None
                    })
                else:
                    seen_blocks[key] = meaningful_lines[i][0]

        return issues

    def _calculate_complexity(self, code: str, language: str) -> Dict:
        if language == 'python':
            try:
                tree = ast.parse(code)
                complexity = self._python_cyclomatic_complexity(tree)
                return complexity
            except Exception:
                pass

        decision_points = len(re.findall(
            r'\b(if|else|elif|for|while|case|catch|&&|\|\|)\b', code
        ))
        return {
            'cyclomatic': decision_points + 1,
            'functions': len(re.findall(r'\bdef\s+\w+|\bfunction\s+\w+|\bvoid\s+\w+|\bint\s+\w+\s*\(', code)),
            'classes': len(re.findall(r'\bclass\s+\w+', code)),
        }

    def _python_cyclomatic_complexity(self, tree) -> Dict:
        functions = []
        total_complexity = 1

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler,
                                          ast.With, ast.Assert, ast.comprehension)):
                        complexity += 1
                    elif isinstance(child, ast.BoolOp):
                        complexity += len(child.values) - 1
                functions.append({'name': node.name, 'complexity': complexity, 'line': node.lineno})
                total_complexity += complexity

        return {
            'cyclomatic': total_complexity,
            'functions': len(functions),
            'function_details': functions,
            'classes': sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        }

    def _check_style(self, lines: List[str], language: str) -> List[Dict]:
        issues = []
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append({
                    'type': 'style',
                    'category': 'style',
                    'severity': 'info',
                    'line': i,
                    'message': f'Line too long ({len(line)} chars, max 120)',
                    'code_snippet': line[:80] + '...',
                    'column': 120
                })
            if line.endswith(' ') or line.endswith('\t'):
                issues.append({
                    'type': 'style',
                    'category': 'style',
                    'severity': 'info',
                    'line': i,
                    'message': 'Trailing whitespace detected',
                    'code_snippet': line.rstrip(),
                    'column': None
                })
        return issues

    def _count_comments(self, lines: List[str], language: str) -> int:
        comment_chars = {'python': '#', 'javascript': '//', 'java': '//', 'cpp': '//'}
        comment_char = comment_chars.get(language, '#')
        return sum(1 for l in lines if l.strip().startswith(comment_char))
