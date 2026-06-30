import re
from typing import List, Dict, Any


VULNERABILITY_DB = {
    'sql_injection': {
        'patterns': [
            r'SELECT.*WHERE.*\+.*str',
            r'execute\s*\(\s*["\'].*%.*["\'].*%',
            r'query\s*=\s*["\'].*\+.*["\']',
            r'cursor\.execute\s*\(\s*f["\']',
            r'db\.execute\s*\(\s*f["\']',
            r'\.format\s*\(.*\)\s*(?:execute|query)',
            r'sql.*=.*%s.*%\s*\(',
            r'DELETE\s+FROM.*WHERE.*\+',
            r'INSERT\s+INTO.*VALUES.*\+',
            r'UPDATE\s+.*SET.*\+.*WHERE',
        ],
        'severity': 'critical',
        'category': 'SQL Injection',
        'cve': 'CWE-89',
        'recommendation': 'Use parameterized queries or ORM methods instead of string concatenation'
    },
    'xss': {
        'patterns': [
            r'innerHTML\s*=\s*\w+',
            r'outerHTML\s*=\s*\w+',
            r'document\.write\s*\(',
            r'eval\s*\(\s*(?:req|request|input)',
            r'\.html\s*\(\s*(?:req|request|input|data)',
            r'Markup\s*\(\s*(?!""")',
            r'jinja2.*autoescape\s*=\s*False',
        ],
        'severity': 'high',
        'category': 'Cross-Site Scripting (XSS)',
        'cve': 'CWE-79',
        'recommendation': 'Sanitize and escape all user inputs before rendering in HTML'
    },
    'command_injection': {
        'patterns': [
            r'os\.system\s*\(',
            r'subprocess\.call\s*\(.*shell\s*=\s*True',
            r'subprocess\.Popen\s*\(.*shell\s*=\s*True',
            r'os\.popen\s*\(',
            r'commands\.getoutput\s*\(',
            r'exec\s*\(\s*(?:request|input|user)',
            r'Runtime\.getRuntime\(\)\.exec',
            r'system\s*\(\s*\w+\s*\)',
        ],
        'severity': 'critical',
        'category': 'Command Injection',
        'cve': 'CWE-78',
        'recommendation': 'Avoid executing shell commands with user input. Use subprocess with list arguments instead of shell=True'
    },
    'hardcoded_secrets': {
        'patterns': [
            r'password\s*=\s*["\'][^"\']{4,}["\']',
            r'passwd\s*=\s*["\'][^"\']{4,}["\']',
            r'secret\s*=\s*["\'][^"\']{8,}["\']',
            r'api_key\s*=\s*["\'][^"\']{8,}["\']',
            r'apikey\s*=\s*["\'][^"\']{8,}["\']',
            r'token\s*=\s*["\'][^"\']{8,}["\']',
            r'private_key\s*=\s*["\']',
            r'AWS_SECRET_ACCESS_KEY\s*=\s*["\']',
            r'GITHUB_TOKEN\s*=\s*["\'][^"\']{10,}["\']',
            r'-----BEGIN\s+(RSA|EC|PRIVATE)\s+KEY-----',
        ],
        'severity': 'critical',
        'category': 'Hardcoded Credentials',
        'cve': 'CWE-798',
        'recommendation': 'Use environment variables or secrets management services (AWS Secrets Manager, HashiCorp Vault) instead of hardcoded credentials'
    },
    'insecure_deserialization': {
        'patterns': [
            r'pickle\.loads?\s*\(',
            r'pickle\.load\s*\(',
            r'yaml\.load\s*\((?!.*Loader\s*=\s*yaml\.SafeLoader)',
            r'marshal\.loads?\s*\(',
            r'shelve\.open\s*\(',
            r'jsonpickle\.decode\s*\(',
        ],
        'severity': 'critical',
        'category': 'Insecure Deserialization',
        'cve': 'CWE-502',
        'recommendation': 'Use safe alternatives: pickle -> json, yaml.load -> yaml.safe_load'
    },
    'path_traversal': {
        'patterns': [
            r'open\s*\(\s*(?:request|input|user)',
            r'os\.path\.join\s*\(\s*.*(?:request|input)',
            r'file\s*=\s*request\.',
            r'filename\s*=\s*request\.',
            r'\.\./|\.\.\\',
        ],
        'severity': 'high',
        'category': 'Path Traversal',
        'cve': 'CWE-22',
        'recommendation': 'Validate and sanitize file paths. Use os.path.realpath() and verify the path is within allowed directory'
    },
    'weak_cryptography': {
        'patterns': [
            r'hashlib\.md5\s*\(',
            r'hashlib\.sha1\s*\(',
            r'MD5\s*\(',
            r'SHA1\s*\(',
            r'DES\s*\(',
            r'RC4\s*\(',
            r'Crypto\.Cipher\.DES',
            r'MessageDigest\.getInstance\s*\(\s*"MD5"',
            r'MessageDigest\.getInstance\s*\(\s*"SHA-1"',
        ],
        'severity': 'high',
        'category': 'Weak Cryptography',
        'cve': 'CWE-327',
        'recommendation': 'Use strong cryptographic algorithms: SHA-256, SHA-3, bcrypt, or Argon2'
    },
    'insecure_random': {
        'patterns': [
            r'\brandom\.random\s*\(',
            r'\brandom\.randint\s*\(',
            r'\brandom\.choice\s*\(',
            r'new\s+Random\s*\(\)',
            r'Math\.random\s*\(',
            r'rand\s*\(',
        ],
        'severity': 'medium',
        'category': 'Insecure Randomness',
        'cve': 'CWE-338',
        'recommendation': 'Use cryptographically secure random: Python secrets module, java.security.SecureRandom, crypto.randomBytes'
    },
    'open_redirect': {
        'patterns': [
            r'redirect\s*\(\s*request\.',
            r'redirect\s*\(\s*\w*url\w*\)',
            r'window\.location\s*=\s*(?:request|input|params)',
            r'header\s*\(\s*["\']Location:',
        ],
        'severity': 'medium',
        'category': 'Open Redirect',
        'cve': 'CWE-601',
        'recommendation': 'Validate redirect URLs against an allowlist of trusted domains'
    },
    'debug_enabled': {
        'patterns': [
            r'DEBUG\s*=\s*True',
            r'debug\s*=\s*true',
            r'app\.run\s*\(.*debug\s*=\s*True',
            r'FLASK_DEBUG\s*=\s*1',
        ],
        'severity': 'medium',
        'category': 'Debug Mode Enabled',
        'cve': 'CWE-94',
        'recommendation': 'Disable debug mode in production. Use environment variables to control debug settings'
    }
}


class SecurityScanner:

    def scan(self, code: str, language: str) -> Dict[str, Any]:
        vulnerabilities = []
        lines = code.split('\n')

        for vuln_type, vuln_info in VULNERABILITY_DB.items():
            for pattern in vuln_info['patterns']:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        vulnerabilities.append({
                            'type': vuln_type,
                            'severity': vuln_info['severity'],
                            'category': vuln_info['category'],
                            'cve': vuln_info['cve'],
                            'line': i,
                            'description': f"{vuln_info['category']} vulnerability detected",
                            'code_snippet': line.strip()[:200],
                            'recommendation': vuln_info['recommendation']
                        })
                        break  # One match per vuln type per line is enough

        # Language-specific checks
        if language == 'python':
            vulnerabilities.extend(self._python_specific_checks(code, lines))
        elif language == 'javascript':
            vulnerabilities.extend(self._javascript_specific_checks(code, lines))

        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        vulnerabilities.sort(key=lambda x: severity_order.get(x['severity'], 5))

        counts = {
            'critical': sum(1 for v in vulnerabilities if v['severity'] == 'critical'),
            'high': sum(1 for v in vulnerabilities if v['severity'] == 'high'),
            'medium': sum(1 for v in vulnerabilities if v['severity'] == 'medium'),
            'low': sum(1 for v in vulnerabilities if v['severity'] == 'low'),
        }

        security_score = self._calculate_security_score(counts)

        return {
            'vulnerabilities': vulnerabilities,
            'counts': counts,
            'total': len(vulnerabilities),
            'security_score': security_score
        }

    def _python_specific_checks(self, code: str, lines: List[str]) -> List[Dict]:
        issues = []
        # Check for missing CSRF protection in Flask routes
        if 'flask' in code.lower() or 'Flask' in code:
            if '@app.route' in code and 'csrf' not in code.lower() and 'WTF_CSRF' not in code:
                issues.append({
                    'type': 'csrf',
                    'severity': 'high',
                    'category': 'CSRF Protection Missing',
                    'cve': 'CWE-352',
                    'line': 1,
                    'description': 'Flask application may lack CSRF protection',
                    'code_snippet': 'Flask app detected without explicit CSRF protection',
                    'recommendation': 'Use Flask-WTF or implement CSRF tokens for all state-changing endpoints'
                })

        # Check for unsafe Flask debug
        for i, line in enumerate(lines, 1):
            if re.search(r'app\.run\s*\(', line) and 'debug=True' in line:
                issues.append({
                    'type': 'debug_production',
                    'severity': 'high',
                    'category': 'Flask Debug Mode',
                    'cve': 'CWE-215',
                    'line': i,
                    'description': 'Flask debug mode exposes sensitive application information',
                    'code_snippet': line.strip(),
                    'recommendation': 'Set debug=False in production or use FLASK_ENV environment variable'
                })

        return issues

    def _javascript_specific_checks(self, code: str, lines: List[str]) -> List[Dict]:
        issues = []
        for i, line in enumerate(lines, 1):
            # Check for prototype pollution
            if re.search(r'__proto__\s*=|prototype\s*\[', line):
                issues.append({
                    'type': 'prototype_pollution',
                    'severity': 'high',
                    'category': 'Prototype Pollution',
                    'cve': 'CWE-1321',
                    'line': i,
                    'description': 'Potential prototype pollution vulnerability',
                    'code_snippet': line.strip(),
                    'recommendation': 'Use Object.create(null) or validate object keys before assignment'
                })
        return issues

    def _calculate_security_score(self, counts: Dict) -> float:
        score = 100.0
        score -= counts.get('critical', 0) * 25
        score -= counts.get('high', 0) * 15
        score -= counts.get('medium', 0) * 8
        score -= counts.get('low', 0) * 3
        return max(0.0, min(100.0, score))
