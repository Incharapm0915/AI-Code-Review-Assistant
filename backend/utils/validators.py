import re
from typing import Tuple


def validate_email(email: str) -> Tuple[bool, str]:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email or not re.match(pattern, email.strip()):
        return False, 'Invalid email address format'
    return True, ''


def validate_password(password: str) -> Tuple[bool, str]:
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter'
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter'
    if not re.search(r'\d', password):
        return False, 'Password must contain at least one number'
    return True, ''


def validate_username(username: str) -> Tuple[bool, str]:
    if len(username) < 3:
        return False, 'Username must be at least 3 characters long'
    if len(username) > 30:
        return False, 'Username must be at most 30 characters long'
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        return False, 'Username can only contain letters, numbers, underscores, dots, and hyphens'
    return True, ''


def validate_code_input(code: str, language: str) -> Tuple[bool, str]:
    supported_languages = ['python', 'javascript', 'java', 'cpp']
    if not code or not code.strip():
        return False, 'Code cannot be empty'
    if language not in supported_languages:
        return False, f'Unsupported language. Supported: {", ".join(supported_languages)}'
    if len(code) > 500000:
        return False, 'Code exceeds maximum size limit (500KB)'
    return True, ''


def sanitize_filename(filename: str) -> str:
    filename = re.sub(r'[^\w\s.-]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    return filename[:255]
