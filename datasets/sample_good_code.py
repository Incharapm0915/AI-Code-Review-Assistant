"""
Sample Good Python Code — Used for testing and ML training baseline.
Demonstrates best practices: proper structure, security, documentation.
"""
import os
import secrets
import hashlib
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Use environment variables for configuration — never hardcode secrets
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
MAX_UPLOAD_SIZE = int(os.environ.get('MAX_UPLOAD_SIZE', 16 * 1024 * 1024))


class UserService:
    """Service layer for user-related operations.

    Follows the single-responsibility principle and separates
    business logic from data access.
    """

    ALLOWED_ROLES = frozenset({'user', 'admin', 'moderator'})
    MIN_PASSWORD_LENGTH = 12

    def __init__(self, db_session):
        """Initialize UserService with a database session.

        Args:
            db_session: SQLAlchemy database session.
        """
        self._db = db_session

    def create_user(self, username: str, email: str, password: str, role: str = 'user') -> Dict[str, Any]:
        """Create a new user with proper validation and password hashing.

        Args:
            username: Unique username (3-50 chars, alphanumeric).
            email:    Valid email address.
            password: Plain-text password (min 12 chars).
            role:     User role, must be in ALLOWED_ROLES.

        Returns:
            Dictionary with created user's public data.

        Raises:
            ValueError: If any input fails validation.
        """
        self._validate_username(username)
        self._validate_email(email)
        self._validate_password(password)

        if role not in self.ALLOWED_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(self.ALLOWED_ROLES)}")

        # Use parameterized query to prevent SQL injection
        existing = self._db.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email)
        ).fetchone()

        if existing:
            raise ValueError("Username or email already registered")

        # Use strong hashing — bcrypt or Argon2 preferred; SHA-256 for demo
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

        user_id = self._db.execute(
            "INSERT INTO users (username, email, password_hash, salt, role) VALUES (?, ?, ?, ?, ?)",
            (username, email.lower(), pwd_hash, salt, role)
        ).lastrowid
        self._db.commit()

        logger.info("User created: %s (id=%d)", username, user_id)
        return {'id': user_id, 'username': username, 'email': email, 'role': role}

    def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user and return their profile if credentials are valid.

        Uses constant-time comparison to prevent timing attacks.

        Args:
            email:    User's email address.
            password: Plain-text password to verify.

        Returns:
            User dict on success, None on failure (never reveals which field was wrong).
        """
        # Sanitize input
        email = email.strip().lower()

        # Use parameterized query
        row = self._db.execute(
            "SELECT id, username, email, password_hash, salt, role, is_active "
            "FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if row is None:
            # Still compute hash to prevent timing attacks
            secrets.compare_digest('dummy', 'hash')
            return None

        if not row['is_active']:
            return None

        candidate_hash = hashlib.sha256(f"{row['salt']}{password}".encode()).hexdigest()

        # Constant-time comparison — prevents timing attacks
        if not secrets.compare_digest(candidate_hash, row['password_hash']):
            logger.warning("Failed login attempt for email: %s", email)
            return None

        logger.info("Successful login: %s", email)
        return {
            'id': row['id'],
            'username': row['username'],
            'email': row['email'],
            'role': row['role'],
        }

    def get_users(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Retrieve a paginated list of users.

        Args:
            page:     Page number (1-indexed).
            per_page: Results per page (max 100).

        Returns:
            Dict with 'users' list and pagination metadata.
        """
        per_page = min(per_page, 100)  # Hard cap to prevent abuse
        offset = (page - 1) * per_page

        rows = self._db.execute(
            "SELECT id, username, email, role, created_at FROM users "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (per_page, offset)
        ).fetchall()

        total = self._db.execute("SELECT COUNT(*) FROM users").fetchone()[0]

        return {
            'users': [dict(r) for r in rows],
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
        }

    # ── Private validation helpers ─────────────────────────────────

    @staticmethod
    def _validate_username(username: str) -> None:
        import re
        if not (3 <= len(username) <= 50):
            raise ValueError("Username must be 3–50 characters")
        if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
            raise ValueError("Username contains invalid characters")

    @staticmethod
    def _validate_email(email: str) -> None:
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email.strip()):
            raise ValueError("Invalid email address")

    def _validate_password(self, password: str) -> None:
        import re
        if len(password) < self.MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters")
        if not re.search(r'[A-Z]', password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[0-9]', password):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Password must contain at least one special character")


def safe_file_upload(file_stream, filename: str, upload_dir: str) -> Path:
    """Safely handle file upload with path traversal prevention.

    Args:
        file_stream: File-like object to read from.
        filename:    Original filename from the client.
        upload_dir:  Directory where the file should be saved.

    Returns:
        Path to the saved file.

    Raises:
        ValueError: If filename is unsafe or file too large.
    """
    # Sanitize filename — prevent path traversal
    safe_name = Path(filename).name  # Strips directory components
    if not safe_name or safe_name.startswith('.'):
        raise ValueError("Invalid filename")

    # Generate a unique name to prevent overwrites
    unique_name = f"{secrets.token_hex(8)}_{safe_name}"
    dest = Path(upload_dir).resolve() / unique_name

    # Verify the resolved path is within the upload directory
    if not str(dest).startswith(str(Path(upload_dir).resolve())):
        raise ValueError("Path traversal attempt detected")

    # Read in chunks to limit memory usage and enforce size limit
    total = 0
    with open(dest, 'wb') as f:
        for chunk in iter(lambda: file_stream.read(8192), b''):
            total += len(chunk)
            if total > MAX_UPLOAD_SIZE:
                dest.unlink(missing_ok=True)
                raise ValueError(f"File exceeds maximum size ({MAX_UPLOAD_SIZE} bytes)")
            f.write(chunk)

    logger.info("File saved: %s (%d bytes)", dest.name, total)
    return dest


def require_role(*roles: str):
    """Decorator that enforces role-based access control.

    Usage:
        @require_role('admin')
        def admin_view(): ...
    """
    allowed = frozenset(roles)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import g, abort
            if not hasattr(g, 'current_user') or g.current_user is None:
                abort(401)
            if g.current_user.get('role') not in allowed:
                logger.warning(
                    "Unauthorized access attempt by user %s to %s",
                    g.current_user.get('id'), func.__name__
                )
                abort(403)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ── Example usage ──────────────────────────────────────────────────

def process_items(items: List[Dict]) -> List[Dict]:
    """Process a list of items with proper iteration and error handling.

    Args:
        items: List of dicts, each with 'id' and 'value' keys.

    Returns:
        List of processed items with 'result' appended.
    """
    results = []
    for idx, item in enumerate(items):  # Use enumerate, not range(len())
        try:
            if 'value' not in item:
                logger.warning("Item at index %d missing 'value' key", idx)
                continue
            processed = {**item, 'result': item['value'] * 2}
            results.append(processed)
        except (TypeError, KeyError) as exc:
            logger.error("Failed to process item %d: %s", idx, exc)

    return results


if __name__ == '__main__':
    # Example — uses context manager for resource cleanup
    logging.basicConfig(level=logging.INFO)
    sample_items = [{'id': i, 'value': i * 10} for i in range(5)]
    processed = process_items(sample_items)
    logger.info("Processed %d items", len(processed))
