import re
import ast
import math
from typing import Dict, List, Any
from backend.services.static_analysis import StaticAnalyzer
from backend.services.security_scanner import SecurityScanner


OPTIMIZATION_PATTERNS = {
    'python': [
        {
            'pattern': r'for\s+\w+\s+in\s+range\s*\(\s*len\s*\(',
            'suggestion': 'Use enumerate() instead of range(len())',
            'example': 'for i, item in enumerate(items):',
            'impact': 'performance'
        },
        {
            'pattern': r'\[\s*\w+\s+for\s+\w+\s+in\s+\w+\s+if\s+',
            'suggestion': 'Good use of list comprehension with filter - consider if generator expression is better for large datasets',
            'example': '(x for x in items if condition)  # Use generator for large data',
            'impact': 'performance'
        },
        {
            'pattern': r'str\s*\+\s*str|\s*\+=\s*["\']',
            'suggestion': 'Use str.join() instead of string concatenation in loops for better performance',
            'example': "result = ''.join(parts)",
            'impact': 'performance'
        },
        {
            'pattern': r'\.append\s*\(.*\)\s*\n.*\.append',
            'suggestion': 'Consider using list comprehension instead of multiple append() calls',
            'example': 'items = [process(x) for x in data]',
            'impact': 'readability'
        },
        {
            'pattern': r'if\s+\w+\s+in\s+\[',
            'suggestion': 'Use set for membership testing instead of list for O(1) lookup',
            'example': 'if item in {1, 2, 3}:  # O(1) vs O(n)',
            'impact': 'performance'
        },
        {
            'pattern': r'dict\(\)',
            'suggestion': 'Use {} literal instead of dict() constructor for better performance',
            'example': 'my_dict = {}',
            'impact': 'performance'
        },
        {
            'pattern': r'try:\s*\n.*\nexcept.*:\s*\n\s*pass',
            'suggestion': 'Empty except block or pass-only handler silently swallows exceptions',
            'example': 'except ValueError as e:\n    logger.warning(f"Expected error: {e}")',
            'impact': 'reliability'
        },
        {
            'pattern': r'open\s*\([^)]+\)(?!\s*as)',
            'suggestion': 'Use context manager (with statement) for file operations',
            'example': 'with open("file.txt") as f:\n    data = f.read()',
            'impact': 'reliability'
        },
    ],
    'javascript': [
        {
            'pattern': r'for\s*\(\s*var\s+\w+\s*=\s*0\s*;\s*\w+\s*<\s*\w+\.length',
            'suggestion': 'Use for...of or Array methods (map, filter, forEach) instead of traditional for loops',
            'example': 'for (const item of items) { ... }',
            'impact': 'readability'
        },
        {
            'pattern': r'\.then\s*\(.*\)\.then\s*\(',
            'suggestion': 'Consider using async/await instead of chained .then() for better readability',
            'example': 'const result = await fetchData();',
            'impact': 'readability'
        },
        {
            'pattern': r'var\s+\w+',
            'suggestion': 'Use const or let instead of var for proper block scoping',
            'example': 'const value = 42; // or let for reassignable',
            'impact': 'maintainability'
        },
        {
            'pattern': r'==\s*null\b|==\s*undefined\b',
            'suggestion': 'Use nullish coalescing (??) or optional chaining (?.) for null checks',
            'example': 'const value = data?.property ?? defaultValue;',
            'impact': 'readability'
        },
    ],
    'java': [
        {
            'pattern': r'String\s+\w+\s*=\s*["\'].*["\'].*\+',
            'suggestion': 'Use StringBuilder for string concatenation in loops',
            'example': 'StringBuilder sb = new StringBuilder();\nsb.append(str);',
            'impact': 'performance'
        },
        {
            'pattern': r'new\s+ArrayList\s*<>\s*\(\)',
            'suggestion': 'Specify initial capacity if size is known: new ArrayList<>(expectedSize)',
            'example': 'new ArrayList<>(100)',
            'impact': 'performance'
        },
    ],
    'cpp': [
        {
            'pattern': r'std::endl',
            'suggestion': 'Use "\\n" instead of std::endl to avoid unnecessary buffer flushes',
            'example': 'std::cout << "text\\n";',
            'impact': 'performance'
        },
        {
            'pattern': r'pass\s+by\s+value|void\s+\w+\s*\(\s*(?:string|vector|map)\s+\w+\s*\)',
            'suggestion': 'Pass large objects by const reference to avoid unnecessary copying',
            'example': 'void func(const std::string& str)',
            'impact': 'performance'
        },
    ]
}

BEST_PRACTICES = {
    'python': [
        'Use type hints for function parameters and return values',
        'Follow PEP 8 style guidelines',
        'Write unit tests using pytest',
        'Use virtual environments for dependency isolation',
        'Apply the DRY (Don\'t Repeat Yourself) principle',
        'Use dataclasses or Pydantic for data validation',
        'Implement proper logging instead of print statements',
        'Use pathlib for file path operations',
        'Apply SOLID principles in class design',
        'Use context managers for resource management',
    ],
    'javascript': [
        'Use TypeScript for better type safety',
        'Apply ESLint and Prettier for code quality',
        'Use async/await instead of callbacks or promise chains',
        'Implement proper error boundaries in React',
        'Use const by default, let when needed, never var',
        'Write unit tests with Jest',
        'Use destructuring for cleaner code',
        'Implement proper event listener cleanup',
        'Use optional chaining and nullish coalescing',
        'Follow the module pattern for code organization',
    ],
    'java': [
        'Follow SOLID principles',
        'Use Optional instead of null returns',
        'Implement the Builder pattern for complex objects',
        'Use streams for collection operations',
        'Apply proper exception hierarchy',
        'Write unit tests with JUnit 5',
        'Use dependency injection (Spring)',
        'Apply immutability where possible',
        'Use interfaces for abstraction',
        'Log with SLF4J/Logback',
    ],
    'cpp': [
        'Use RAII (Resource Acquisition Is Initialization)',
        'Prefer smart pointers over raw pointers',
        'Use std::string over C-style strings',
        'Apply const correctness',
        'Use STL algorithms instead of manual loops',
        'Write unit tests with Google Test',
        'Apply the Rule of Five/Zero',
        'Use move semantics for performance',
        'Apply namespace organization',
        'Use static analysis tools (cppcheck, clang-tidy)',
    ]
}


class AIAnalyzer:

    def __init__(self):
        self.static_analyzer = StaticAnalyzer()
        self.security_scanner = SecurityScanner()

    def analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        static_results = self.static_analyzer.analyze(code, language)
        security_results = self.security_scanner.scan(code, language)
        optimizations = self._find_optimizations(code, language)
        best_practices = self._get_best_practices(code, language)
        metrics = self._calculate_metrics(code, language, static_results)
        scores = self._calculate_scores(static_results, security_results, metrics)

        all_issues = static_results.get('issues', [])
        severity_map = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        all_issues.sort(key=lambda x: severity_map.get(x.get('severity', 'info'), 5))

        return {
            'issues': all_issues,
            'vulnerabilities': security_results.get('vulnerabilities', []),
            'optimizations': optimizations,
            'best_practices': best_practices,
            'metrics': metrics,
            'scores': scores,
            'summary': self._generate_summary(all_issues, security_results, scores, language),
            'complexity': static_results.get('complexity', {}),
            'line_stats': {
                'total': static_results.get('total_lines', 0),
                'blank': static_results.get('blank_lines', 0),
                'comments': static_results.get('comment_lines', 0),
                'code': static_results.get('total_lines', 0) - static_results.get('blank_lines', 0) - static_results.get('comment_lines', 0)
            }
        }

    def _find_optimizations(self, code: str, language: str) -> List[Dict]:
        optimizations = []
        patterns = OPTIMIZATION_PATTERNS.get(language, [])
        lines = code.split('\n')

        for opt in patterns:
            for i, line in enumerate(lines, 1):
                if re.search(opt['pattern'], line):
                    optimizations.append({
                        'line': i,
                        'suggestion': opt['suggestion'],
                        'example': opt['example'],
                        'impact': opt['impact'],
                        'code_snippet': line.strip()
                    })
                    break

        return optimizations

    def _get_best_practices(self, code: str, language: str) -> List[str]:
        practices = BEST_PRACTICES.get(language, [])
        relevant = []

        relevance_checks = {
            'Use type hints': lambda c: 'def ' in c and ':' not in c.split('def ')[1].split('(')[1] if 'def ' in c else False,
            'Write unit tests': lambda c: 'import pytest' not in c and 'import unittest' not in c,
            'Implement proper logging': lambda c: 'print(' in c,
            'Use context managers': lambda c: 'open(' in c and 'with ' not in c,
        }

        for practice in practices:
            for key, check in relevance_checks.items():
                if key.lower() in practice.lower():
                    try:
                        if check(code):
                            relevant.append(practice)
                    except Exception:
                        pass
                    break
            else:
                relevant.append(practice)

        return relevant[:8]

    def _calculate_metrics(self, code: str, language: str, static_results: Dict) -> Dict:
        lines = code.split('\n')
        total_lines = len(lines)
        blank_lines = sum(1 for l in lines if not l.strip())
        comment_lines = static_results.get('comment_lines', 0)
        code_lines = total_lines - blank_lines - comment_lines

        comment_ratio = (comment_lines / max(code_lines, 1)) * 100
        complexity = static_results.get('complexity', {})

        # Halstead-inspired metrics
        operators = len(re.findall(r'[+\-*/=<>!&|%^~]', code))
        operands = len(re.findall(r'\b[a-zA-Z_]\w*\b', code))
        vocabulary = max(operators + operands, 1)
        length = operators + operands
        volume = length * math.log2(vocabulary) if vocabulary > 1 else 0

        maintainability = max(0, min(100, 171 - 5.2 * math.log(max(volume, 1)) - 0.23 * complexity.get('cyclomatic', 1) - 16.2 * math.log(max(code_lines, 1))))

        return {
            'total_lines': total_lines,
            'code_lines': code_lines,
            'blank_lines': blank_lines,
            'comment_lines': comment_lines,
            'comment_ratio': round(comment_ratio, 1),
            'cyclomatic_complexity': complexity.get('cyclomatic', 1),
            'function_count': complexity.get('functions', 0),
            'class_count': complexity.get('classes', 0),
            'maintainability_index': round(maintainability, 1),
            'halstead_volume': round(volume, 1),
            'avg_function_complexity': round(
                complexity.get('cyclomatic', 1) / max(complexity.get('functions', 1), 1), 2
            )
        }

    def _calculate_scores(self, static_results: Dict, security_results: Dict, metrics: Dict) -> Dict:
        issues = static_results.get('issues', [])

        severity_weights = {'critical': 20, 'high': 12, 'medium': 6, 'low': 3, 'info': 1}
        penalty = sum(severity_weights.get(issue.get('severity', 'info'), 1) for issue in issues)
        quality_score = max(0, min(100, 100 - penalty))

        security_score = security_results.get('security_score', 100)

        cyclomatic = metrics.get('cyclomatic_complexity', 1)
        if cyclomatic <= 10:
            complexity_score = 100
        elif cyclomatic <= 20:
            complexity_score = 80
        elif cyclomatic <= 40:
            complexity_score = 60
        elif cyclomatic <= 60:
            complexity_score = 40
        else:
            complexity_score = 20

        maintainability_score = metrics.get('maintainability_index', 70)

        overall = (quality_score * 0.35 + security_score * 0.30 + complexity_score * 0.20 + maintainability_score * 0.15)

        return {
            'quality': round(quality_score, 1),
            'security': round(security_score, 1),
            'complexity': round(complexity_score, 1),
            'maintainability': round(maintainability_score, 1),
            'overall': round(overall, 1),
            'grade': self._get_grade(overall)
        }

    def _get_grade(self, score: float) -> str:
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def _generate_summary(self, issues: List, security_results: Dict, scores: Dict, language: str) -> Dict:
        critical_count = sum(1 for i in issues if i.get('severity') == 'critical')
        high_count = sum(1 for i in issues if i.get('severity') == 'high')
        medium_count = sum(1 for i in issues if i.get('severity') == 'medium')
        vuln_count = security_results.get('total', 0)

        if scores['overall'] >= 85:
            verdict = 'Excellent'
            description = f'This {language} code is well-written with minor issues to address.'
        elif scores['overall'] >= 70:
            verdict = 'Good'
            description = f'This {language} code is generally good but has some areas that need attention.'
        elif scores['overall'] >= 55:
            verdict = 'Fair'
            description = f'This {language} code needs significant improvements before production use.'
        else:
            verdict = 'Poor'
            description = f'This {language} code has critical issues that must be resolved immediately.'

        return {
            'verdict': verdict,
            'description': description,
            'critical_issues': critical_count,
            'high_issues': high_count,
            'medium_issues': medium_count,
            'vulnerabilities': vuln_count,
            'overall_score': scores['overall'],
            'grade': scores['grade'],
            'top_concern': issues[0]['message'] if issues else 'No major issues found'
        }
