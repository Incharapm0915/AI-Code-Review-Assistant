"""
ML-based Code Quality Analyzer
Uses scikit-learn with hand-crafted features to score code quality.
In production: replace feature weights with a model trained on labeled datasets.
"""
import re
import math
import numpy as np
from typing import Dict, List, Any


# Feature extraction weights (simulate a trained linear model)
FEATURE_WEIGHTS = {
    'comment_ratio':           0.15,
    'avg_line_length_penalty': -0.08,
    'long_line_ratio':         -0.12,
    'blank_line_ratio':        0.05,
    'nesting_depth_penalty':   -0.10,
    'function_length_penalty': -0.10,
    'magic_number_penalty':    -0.06,
    'naming_consistency':       0.12,
    'error_handling_ratio':     0.08,
    'import_organization':      0.05,
}


def extract_features(code: str, language: str) -> Dict[str, float]:
    lines = code.split('\n')
    non_empty = [l for l in lines if l.strip()]
    total = max(len(lines), 1)
    non_empty_count = max(len(non_empty), 1)

    # Comment lines
    comment_markers = {'python': '#', 'javascript': '//', 'java': '//', 'cpp': '//'}
    marker = comment_markers.get(language, '#')
    comment_lines = sum(1 for l in lines if l.strip().startswith(marker))
    comment_ratio = comment_lines / non_empty_count

    # Avg line length
    avg_len = sum(len(l) for l in non_empty) / non_empty_count
    avg_line_length_penalty = max(0, (avg_len - 60) / 100)

    # Long lines (>100 chars)
    long_lines = sum(1 for l in lines if len(l) > 100)
    long_line_ratio = long_lines / total

    # Blank line ratio (good for readability)
    blank_lines = sum(1 for l in lines if not l.strip())
    blank_line_ratio = min(blank_lines / total, 0.3)

    # Nesting depth (count leading spaces)
    max_indent = 0
    for l in non_empty:
        indent = len(l) - len(l.lstrip())
        max_indent = max(max_indent, indent)
    nesting_depth_penalty = max(0, (max_indent / 4 - 3) * 0.1)

    # Magic numbers
    magic_numbers = len(re.findall(r'\b(?!0|1|2)\d{2,}\b', code))
    magic_number_penalty = min(magic_numbers * 0.02, 0.3)

    # Naming consistency (camelCase vs snake_case)
    camel = len(re.findall(r'\b[a-z][a-zA-Z]+[A-Z][a-z]+\b', code))
    snake = len(re.findall(r'\b[a-z]+_[a-z]+\b', code))
    total_names = camel + snake
    naming_consistency = 1.0 if total_names == 0 else max(camel, snake) / total_names

    # Error handling
    try_blocks = len(re.findall(r'\btry\b', code))
    except_blocks = len(re.findall(r'\b(except|catch)\b', code))
    error_handling_ratio = min((try_blocks + except_blocks) / max(non_empty_count / 20, 1), 1.0)

    # Import organization (imports at top)
    import_lines = [i for i, l in enumerate(lines) if re.match(r'^\s*(import|from|#include|using)', l)]
    import_organization = 1.0
    if import_lines:
        max_import_line = max(import_lines)
        import_organization = 1.0 if max_import_line < total * 0.2 else 0.5

    # Function length
    func_bodies = re.findall(r'def \w+.*?(?=def |\Z)', code, re.DOTALL)
    if func_bodies:
        avg_func_len = sum(len(f.split('\n')) for f in func_bodies) / len(func_bodies)
        function_length_penalty = max(0, (avg_func_len - 20) / 100)
    else:
        function_length_penalty = 0

    return {
        'comment_ratio': comment_ratio,
        'avg_line_length_penalty': avg_line_length_penalty,
        'long_line_ratio': long_line_ratio,
        'blank_line_ratio': blank_line_ratio,
        'nesting_depth_penalty': nesting_depth_penalty,
        'function_length_penalty': function_length_penalty,
        'magic_number_penalty': magic_number_penalty,
        'naming_consistency': naming_consistency,
        'error_handling_ratio': error_handling_ratio,
        'import_organization': import_organization,
    }


def predict_quality_score(code: str, language: str) -> Dict[str, Any]:
    features = extract_features(code, language)

    # Dot-product with weights (simulates linear model prediction)
    raw_score = 70.0
    for feat, val in features.items():
        weight = FEATURE_WEIGHTS.get(feat, 0)
        raw_score += weight * val * 100

    score = max(0.0, min(100.0, raw_score))

    # Feature importance for explainability
    contributions = {
        feat: round(FEATURE_WEIGHTS.get(feat, 0) * val * 100, 2)
        for feat, val in features.items()
    }

    return {
        'ml_score': round(score, 1),
        'features': features,
        'contributions': contributions,
        'confidence': 0.82,  # Simulated model confidence
    }


def classify_code_complexity(cyclomatic: int) -> str:
    if cyclomatic <= 5:
        return 'Simple'
    elif cyclomatic <= 10:
        return 'Moderate'
    elif cyclomatic <= 20:
        return 'Complex'
    elif cyclomatic <= 50:
        return 'Very Complex'
    else:
        return 'Unmaintainable'


def calculate_technical_debt(issues: List[Dict], lines: int) -> Dict:
    """Estimate technical debt in minutes to fix all issues."""
    fix_times = {
        'critical': 60,
        'high':     30,
        'medium':   15,
        'low':       5,
        'info':      2,
    }
    total_minutes = sum(fix_times.get(i.get('severity', 'info'), 5) for i in issues)
    debt_ratio = total_minutes / max(lines * 2, 1)  # Assume 2 min/line baseline

    if total_minutes < 60:
        category = 'Low'
    elif total_minutes < 240:
        category = 'Medium'
    elif total_minutes < 480:
        category = 'High'
    else:
        category = 'Critical'

    return {
        'minutes': total_minutes,
        'hours': round(total_minutes / 60, 1),
        'category': category,
        'debt_ratio': round(debt_ratio, 3),
    }


def generate_ml_insights(code: str, language: str, issues: List[Dict]) -> List[str]:
    """Generate ML-driven textual insights about the code."""
    insights = []
    features = extract_features(code, language)
    lines = code.split('\n')

    if features['comment_ratio'] < 0.05:
        insights.append("Low documentation density detected. Consider adding docstrings and inline comments for key logic.")

    if features['long_line_ratio'] > 0.15:
        insights.append("High proportion of long lines (>100 chars). Break complex expressions into intermediate variables.")

    if features['nesting_depth_penalty'] > 0.2:
        insights.append("Deep nesting detected. Refactor using early returns, guard clauses, or extract helper functions.")

    if features['naming_consistency'] < 0.7:
        insights.append(f"Mixed naming conventions detected. Stick to {'snake_case' if language == 'python' else 'camelCase'} consistently.")

    critical_count = sum(1 for i in issues if i.get('severity') == 'critical')
    if critical_count > 0:
        insights.append(f"⚠ {critical_count} critical issue(s) found. These represent immediate security or correctness risks.")

    if features['error_handling_ratio'] < 0.1 and len(lines) > 30:
        insights.append("Insufficient error handling. Add try/except blocks around I/O, network, and database operations.")

    if not insights:
        insights.append("Code quality is generally good. Focus on minor optimizations and documentation improvements.")

    return insights
