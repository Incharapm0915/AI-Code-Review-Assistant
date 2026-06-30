"""
Code Complexity Metrics Calculator
Implements cyclomatic complexity, Halstead metrics, and maintainability index.
"""
import re
import ast
import math
from typing import Dict, List, Any


class ComplexityCalculator:

    def calculate(self, code: str, language: str) -> Dict[str, Any]:
        lines = code.split('\n')
        halstead = self._halstead_metrics(code)
        loc = self._count_loc(lines, language)

        if language == 'python':
            cyclomatic = self._python_cyclomatic(code)
        else:
            cyclomatic = self._generic_cyclomatic(code)

        mi = self._maintainability_index(
            halstead.get('volume', 0),
            cyclomatic.get('average', 1),
            loc.get('code_lines', 1)
        )

        return {
            'cyclomatic': cyclomatic,
            'halstead': halstead,
            'loc': loc,
            'maintainability_index': round(mi, 1),
            'maintainability_label': self._mi_label(mi),
            'cognitive_complexity': self._cognitive_complexity(code, language),
        }

    def _python_cyclomatic(self, code: str) -> Dict:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {'total': 1, 'average': 1, 'functions': []}

        functions = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.For, ast.While,
                                          ast.ExceptHandler, ast.With,
                                          ast.Assert, ast.comprehension)):
                        complexity += 1
                    elif isinstance(child, ast.BoolOp):
                        complexity += len(child.values) - 1
                    elif isinstance(child, (ast.And, ast.Or)):
                        complexity += 1
                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'complexity': complexity,
                    'risk': self._complexity_risk(complexity),
                })

        total = sum(f['complexity'] for f in functions) or 1
        average = total / max(len(functions), 1)

        return {
            'total': total,
            'average': round(average, 2),
            'functions': sorted(functions, key=lambda x: x['complexity'], reverse=True),
            'max': max((f['complexity'] for f in functions), default=1),
        }

    def _generic_cyclomatic(self, code: str) -> Dict:
        decision_keywords = [
            r'\bif\b', r'\belse\b', r'\belif\b', r'\bfor\b', r'\bwhile\b',
            r'\bcase\b', r'\bcatch\b', r'\b&&\b', r'\|\|', r'\?\s',
            r'\bswitch\b', r'\bdo\b',
        ]
        count = 1
        for pattern in decision_keywords:
            count += len(re.findall(pattern, code))
        return {'total': count, 'average': count, 'functions': []}

    def _halstead_metrics(self, code: str) -> Dict:
        # Tokenize operators and operands
        operator_pattern = r'[+\-*/=<>!&|%^~?:]{1,3}|(?:\b(?:if|else|for|while|return|import|class|def|new|delete|throw|try|catch)\b)'
        operand_pattern = r'\b\d+(?:\.\d+)?\b|\b[a-zA-Z_]\w*\b|["\'](?:[^"\'\\]|\\.)*["\']'

        operators = re.findall(operator_pattern, code)
        operands = re.findall(operand_pattern, code)

        n1 = len(set(operators))   # Distinct operators
        n2 = len(set(operands))    # Distinct operands
        N1 = len(operators)        # Total operators
        N2 = len(operands)         # Total operands

        vocabulary = n1 + n2
        length = N1 + N2
        volume = length * math.log2(max(vocabulary, 1))
        difficulty = (n1 / 2) * (N2 / max(n2, 1))
        effort = difficulty * volume
        time_to_program = effort / 18  # seconds
        bugs_delivered = volume / 3000

        return {
            'distinct_operators': n1,
            'distinct_operands': n2,
            'total_operators': N1,
            'total_operands': N2,
            'vocabulary': vocabulary,
            'length': length,
            'volume': round(volume, 1),
            'difficulty': round(difficulty, 1),
            'effort': round(effort, 1),
            'time_minutes': round(time_to_program / 60, 1),
            'estimated_bugs': round(bugs_delivered, 2),
        }

    def _count_loc(self, lines: List[str], language: str) -> Dict:
        comment_markers = {'python': '#', 'javascript': '//', 'java': '//', 'cpp': '//'}
        marker = comment_markers.get(language, '#')

        total = len(lines)
        blank = sum(1 for l in lines if not l.strip())
        comments = sum(1 for l in lines if l.strip().startswith(marker))
        code_lines = total - blank - comments

        return {
            'total': total,
            'code_lines': code_lines,
            'comment_lines': comments,
            'blank_lines': blank,
            'comment_ratio': round(comments / max(code_lines, 1) * 100, 1),
        }

    def _maintainability_index(self, volume: float, cyclomatic: float, loc: int) -> float:
        v = max(volume, 1)
        cc = max(cyclomatic, 1)
        l = max(loc, 1)
        mi = 171 - 5.2 * math.log(v) - 0.23 * cc - 16.2 * math.log(l)
        # Normalize to 0-100
        return max(0.0, min(100.0, mi * 100 / 171))

    def _mi_label(self, mi: float) -> str:
        if mi >= 85:
            return 'Highly Maintainable'
        elif mi >= 65:
            return 'Maintainable'
        elif mi >= 40:
            return 'Moderately Maintainable'
        else:
            return 'Difficult to Maintain'

    def _cognitive_complexity(self, code: str, language: str) -> int:
        """Approximate cognitive complexity (Sonar method)."""
        score = 0
        nesting = 0
        nesting_keywords = {'if', 'for', 'while', 'else', 'elif', 'try', 'catch', 'switch'}

        for line in code.split('\n'):
            stripped = line.strip().lower()
            for kw in nesting_keywords:
                if re.search(r'\b' + kw + r'\b', stripped):
                    score += 1 + nesting
                    if kw in ('if', 'for', 'while', 'try', 'switch'):
                        nesting += 1
                    break
            if stripped in ('}', 'end', 'endif', 'endfor'):
                nesting = max(0, nesting - 1)
            if re.search(r'\b(break|continue|goto)\b', stripped):
                score += 1

        return score

    def _complexity_risk(self, complexity: int) -> str:
        if complexity <= 5:
            return 'Low'
        elif complexity <= 10:
            return 'Medium'
        elif complexity <= 20:
            return 'High'
        else:
            return 'Very High'


def get_complexity_recommendations(complexity_data: Dict) -> List[str]:
    recs = []
    cyclomatic = complexity_data.get('cyclomatic', {})
    mi = complexity_data.get('maintainability_index', 100)

    if cyclomatic.get('average', 0) > 10:
        recs.append("Average cyclomatic complexity is high. Break complex functions into smaller, single-purpose units.")

    # Flag top 3 most complex functions
    funcs = cyclomatic.get('functions', [])[:3]
    for f in funcs:
        if f['complexity'] > 10:
            recs.append(f"Function '{f['name']}' (line {f['line']}) has complexity {f['complexity']}. Consider refactoring.")

    if mi < 50:
        recs.append("Maintainability index is low. Simplify logic, add documentation, and reduce nesting depth.")

    halstead = complexity_data.get('halstead', {})
    if halstead.get('estimated_bugs', 0) > 1:
        recs.append(f"Halstead analysis estimates ~{halstead['estimated_bugs']} defects. Thorough testing recommended.")

    return recs
