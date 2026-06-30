"""
NLP-based Code Comment & Documentation Analyzer
Uses NLTK for tokenization and text quality analysis.
"""
import re
from typing import Dict, List, Any

# Try importing NLTK; fall back to lightweight regex if unavailable
try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords

    # Download required NLTK data silently
    for pkg in ('punkt', 'stopwords', 'averaged_perceptron_tagger'):
        try:
            nltk.download(pkg, quiet=True)
        except Exception:
            pass

    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


COMMENT_QUALITY_PATTERNS = {
    'good': [
        r'(?:calculates?|computes?|returns?|checks?|validates?|handles?|processes?)',
        r'(?:note|warning|important|todo|fixme|hack)',
        r'(?:because|since|due to|in order to|to ensure)',
        r'(?:algorithm|complexity|performance|security)',
    ],
    'poor': [
        r'^#\s*$',            # Empty comments
        r'#\s*end\s+\w+',     # "# end function" style
        r'#\s*\w+\s*$',       # Single word comments
        r'#\s*(?:var|temp|x|y|z|foo|bar)\s*$',  # Meaningless names
    ]
}

IDENTIFIER_QUALITY = {
    'good': [
        r'\b[a-z][a-z_]{3,}\b',        # Meaningful snake_case
        r'\b[a-z][a-zA-Z]{3,}\b',      # Meaningful camelCase
    ],
    'poor': [
        r'\b(?:x|y|z|a|b|c|tmp|temp|foo|bar|baz|data2|val2)\b',  # Generic names
        r'\b[a-z]{1,2}\d*\b',          # Single/double char vars
    ]
}


def analyze_documentation(code: str, language: str) -> Dict[str, Any]:
    lines = code.split('\n')
    comments = _extract_comments(lines, language)
    identifiers = _extract_identifiers(code)
    doc_score = _score_documentation(comments, lines)
    naming_score = _score_naming(identifiers)
    readability = _calculate_readability(code)

    return {
        'documentation_score': doc_score,
        'naming_score': naming_score,
        'readability_score': readability,
        'comment_count': len(comments),
        'identifier_count': len(identifiers),
        'suggestions': _generate_suggestions(comments, identifiers, doc_score, naming_score),
        'nlp_available': NLTK_AVAILABLE,
    }


def _extract_comments(lines: List[str], language: str) -> List[str]:
    comment_markers = {
        'python': r'#\s*(.*)',
        'javascript': r'//\s*(.*)',
        'java': r'//\s*(.*)',
        'cpp': r'//\s*(.*)',
    }
    pattern = comment_markers.get(language, r'#\s*(.*)')
    comments = []
    for line in lines:
        m = re.search(pattern, line)
        if m:
            text = m.group(1).strip()
            if text:
                comments.append(text)
    return comments


def _extract_identifiers(code: str) -> List[str]:
    # Extract function, variable, and class names
    identifiers = []

    # Function definitions
    for m in re.finditer(r'\bdef\s+(\w+)', code):
        identifiers.append(m.group(1))
    for m in re.finditer(r'\bfunction\s+(\w+)', code):
        identifiers.append(m.group(1))

    # Variable assignments
    for m in re.finditer(r'\b([a-z_][a-z0-9_]*)\s*=', code):
        name = m.group(1)
        if not re.match(r'^(self|cls|true|false|none|null|undefined)$', name, re.I):
            identifiers.append(name)

    # Class names
    for m in re.finditer(r'\bclass\s+(\w+)', code):
        identifiers.append(m.group(1))

    return list(set(identifiers))


def _score_documentation(comments: List[str], lines: List[str]) -> float:
    if not comments:
        return 20.0

    score = 50.0
    non_empty_lines = sum(1 for l in lines if l.strip())

    # Reward comment density
    density = len(comments) / max(non_empty_lines, 1)
    if density >= 0.1:
        score += 20
    elif density >= 0.05:
        score += 10

    # Reward meaningful comments
    good_count = 0
    poor_count = 0
    for comment in comments:
        c_lower = comment.lower()
        is_good = any(re.search(p, c_lower) for p in COMMENT_QUALITY_PATTERNS['good'])
        is_poor = any(re.search(p, comment) for p in COMMENT_QUALITY_PATTERNS['poor'])
        if is_good:
            good_count += 1
        if is_poor:
            poor_count += 1

    if comments:
        good_ratio = good_count / len(comments)
        score += good_ratio * 20
        score -= (poor_count / len(comments)) * 10

    # NLTK-enhanced analysis
    if NLTK_AVAILABLE:
        try:
            all_text = ' '.join(comments)
            words = word_tokenize(all_text)
            stop_words = set(stopwords.words('english'))
            meaningful = [w for w in words if w.lower() not in stop_words and len(w) > 2]
            if len(words) > 0:
                score += min((len(meaningful) / len(words)) * 15, 15)
        except Exception:
            pass

    return max(0.0, min(100.0, score))


def _score_naming(identifiers: List[str]) -> float:
    if not identifiers:
        return 60.0

    score = 60.0
    good = 0
    poor = 0

    for name in identifiers:
        if len(name) <= 1:
            poor += 1
            continue
        is_good = any(re.search(p, name) for p in IDENTIFIER_QUALITY['good'])
        is_poor = any(re.search(p, name) for p in IDENTIFIER_QUALITY['poor'])
        if is_good:
            good += 1
        if is_poor:
            poor += 1

    total = len(identifiers)
    score += (good / total) * 30
    score -= (poor / total) * 20

    return max(0.0, min(100.0, score))


def _calculate_readability(code: str) -> float:
    """Flesch-Kincaid inspired metric adapted for code."""
    lines = code.split('\n')
    non_empty = [l for l in lines if l.strip()]
    if not non_empty:
        return 50.0

    avg_len = sum(len(l) for l in non_empty) / len(non_empty)
    max_indent = max((len(l) - len(l.lstrip()) for l in non_empty), default=0)

    # Base readability
    score = 100.0
    if avg_len > 80:
        score -= (avg_len - 80) * 0.5
    if max_indent > 16:
        score -= (max_indent - 16) * 0.8

    # Penalize very long files
    if len(lines) > 500:
        score -= 10

    return max(0.0, min(100.0, score))


def _generate_suggestions(comments, identifiers, doc_score, naming_score) -> List[str]:
    suggestions = []

    if doc_score < 40:
        suggestions.append("Add more descriptive comments explaining WHY the code does what it does, not just WHAT.")
    elif doc_score < 70:
        suggestions.append("Comment quality can be improved. Explain complex logic and edge cases.")

    if naming_score < 50:
        suggestions.append("Many identifiers use generic names (x, temp, data). Use descriptive names that convey purpose.")
    elif naming_score < 75:
        suggestions.append("Some identifiers could be more descriptive. Aim for self-documenting variable names.")

    poor_comments = [c for c in comments if len(c.split()) <= 1]
    if len(poor_comments) > len(comments) * 0.3:
        suggestions.append("Several single-word comments found. Expand them into meaningful descriptions.")

    if not suggestions:
        suggestions.append("Documentation quality is good! Keep maintaining clear, meaningful comments.")

    return suggestions


def extract_code_vocabulary(code: str) -> Dict[str, int]:
    """Build a frequency map of code tokens (useful for ML training)."""
    tokens = re.findall(r'\b[a-zA-Z_]\w*\b', code)
    freq = {}
    for token in tokens:
        freq[token] = freq.get(token, 0) + 1
    return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True)[:50])


def detect_code_patterns(code: str) -> List[str]:
    """Detect high-level design patterns in code."""
    patterns_found = []

    if re.search(r'\bsingleton\b|\b_instance\b|\bget_instance\b', code, re.I):
        patterns_found.append('Singleton Pattern')
    if re.search(r'\bfactory\b|\bcreate_\w+\b', code, re.I):
        patterns_found.append('Factory Pattern')
    if re.search(r'\bobserver\b|\bsubscribe\b|\bnotify\b|\bevent\b', code, re.I):
        patterns_found.append('Observer Pattern')
    if re.search(r'\bdecorator\b|@\w+\s*\n\s*def ', code, re.I):
        patterns_found.append('Decorator Pattern')
    if re.search(r'\bstrategy\b|\bpolicy\b', code, re.I):
        patterns_found.append('Strategy Pattern')
    if re.search(r'\bmixin\b|\bbase\w*class\b', code, re.I):
        patterns_found.append('Mixin/Inheritance Pattern')

    return patterns_found
