import re
import ast
from typing import Dict, Any

LANGUAGE_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'javascript',
    '.java': 'java',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
    '.c': 'cpp',
    '.h': 'cpp',
    '.hpp': 'cpp',
}


def detect_language(filename: str) -> str:
    ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return LANGUAGE_MAP.get(ext, 'python')


def preprocess_code(code: str, language: str) -> Dict[str, Any]:
    lines = code.split('\n')
    tokens = tokenize_code(code, language)
    ast_info = generate_ast_info(code, language)
    stats = extract_stats(code, lines, language)

    return {
        'original': code,
        'lines': lines,
        'line_count': len(lines),
        'tokens': tokens,
        'ast_info': ast_info,
        'stats': stats,
        'language': language
    }


def tokenize_code(code: str, language: str) -> Dict:
    words = re.findall(r'\b[a-zA-Z_]\w*\b', code)
    operators = re.findall(r'[+\-*/=<>!&|%^~?:]+', code)
    strings = re.findall(r'["\'](?:[^"\'\\]|\\.)*["\']', code)
    numbers = re.findall(r'\b\d+(?:\.\d+)?\b', code)

    return {
        'word_count': len(words),
        'operator_count': len(operators),
        'string_literal_count': len(strings),
        'numeric_literal_count': len(numbers),
        'unique_identifiers': len(set(words)),
        'identifiers': list(set(words))[:50]
    }


def generate_ast_info(code: str, language: str) -> Dict:
    if language != 'python':
        return {'available': False, 'language': language}

    try:
        tree = ast.parse(code)
        functions = []
        classes = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'args': [a.arg for a in node.args.args],
                    'decorators': [ast.dump(d) for d in node.decorator_list],
                    'is_async': False
                })
            elif isinstance(node, ast.AsyncFunctionDef):
                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'args': [a.arg for a in node.args.args],
                    'decorators': [],
                    'is_async': True
                })
            elif isinstance(node, ast.ClassDef):
                classes.append({
                    'name': node.name,
                    'line': node.lineno,
                    'bases': [ast.dump(b) for b in node.bases],
                    'methods': []
                })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    imports.extend([alias.name for alias in node.names])
                else:
                    module = node.module or ''
                    imports.append(module)

        return {
            'available': True,
            'functions': functions,
            'classes': classes,
            'imports': list(set(imports)),
            'function_count': len(functions),
            'class_count': len(classes),
            'import_count': len(set(imports))
        }
    except SyntaxError as e:
        return {
            'available': False,
            'error': str(e),
            'error_line': e.lineno
        }
    except Exception as e:
        return {'available': False, 'error': str(e)}


def extract_stats(code: str, lines: list, language: str) -> Dict:
    comment_patterns = {
        'python': r'^\s*#',
        'javascript': r'^\s*//',
        'java': r'^\s*//',
        'cpp': r'^\s*//'
    }
    comment_pattern = comment_patterns.get(language, r'^\s*#')

    comment_lines = sum(1 for l in lines if re.match(comment_pattern, l))
    blank_lines = sum(1 for l in lines if not l.strip())
    code_lines = len(lines) - comment_lines - blank_lines

    return {
        'total_lines': len(lines),
        'code_lines': code_lines,
        'comment_lines': comment_lines,
        'blank_lines': blank_lines,
        'avg_line_length': sum(len(l) for l in lines) / max(len(lines), 1),
        'max_line_length': max((len(l) for l in lines), default=0),
        'char_count': len(code)
    }


def validate_file_extension(filename: str, allowed: set) -> bool:
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed


def sanitize_code(code: str, max_length: int = 500000) -> str:
    if len(code) > max_length:
        code = code[:max_length]
    code = code.replace('\r\n', '\n').replace('\r', '\n')
    return code
