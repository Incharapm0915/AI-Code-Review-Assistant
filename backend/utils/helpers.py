import os
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from backend.extensions import db


def generate_unique_filename(original_filename: str) -> str:
    ext = original_filename.rsplit('.', 1)[-1] if '.' in original_filename else 'txt'
    unique_id = uuid.uuid4().hex
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'{timestamp}_{unique_id}.{ext}'


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


def get_file_size_str(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f'{size_bytes} B'
    elif size_bytes < 1024 ** 2:
        return f'{size_bytes / 1024:.1f} KB'
    else:
        return f'{size_bytes / (1024 ** 2):.1f} MB'


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            from backend.models.user import User
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user or user.role != 'admin':
                return jsonify({'error': 'Admin access required', 'code': 'FORBIDDEN'}), 403
            g.current_user = user
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication failed', 'code': 'UNAUTHORIZED'}), 401
    return decorated_function


def log_admin_action(admin_id: int, action: str, target_type: str = None,
                     target_id: int = None, details: str = None):
    from backend.models.vulnerability_log import AdminLog
    log = AdminLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=request.remote_addr if request else None
    )
    db.session.add(log)
    db.session.commit()


def paginate_query(query, page: int = 1, per_page: int = 20):
    return query.paginate(page=page, per_page=per_page, error_out=False)


def success_response(data=None, message='Success', status_code=200):
    response = {'success': True, 'message': message}
    if data is not None:
        response['data'] = data
    return jsonify(response), status_code


def error_response(message='An error occurred', code='ERROR', status_code=400):
    return jsonify({'success': False, 'error': message, 'code': code}), status_code


def get_client_ip():
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
    return request.remote_addr
