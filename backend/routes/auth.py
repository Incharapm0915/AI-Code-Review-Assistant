from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, unset_jwt_cookies, set_access_cookies, set_refresh_cookies
)
from backend.extensions import db, mail
from backend.models.user import User
from backend.utils.validators import validate_email, validate_password, validate_username
from backend.utils.helpers import generate_reset_token, error_response, success_response

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('auth/register.html')


@auth_bp.route('/forgot-password', methods=['GET'])
def forgot_password_page():
    return render_template('auth/forgot_password.html')


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return error_response('Request body is required', status_code=400)

    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()

    valid, msg = validate_username(username)
    if not valid:
        return error_response(msg, 'INVALID_USERNAME', 400)

    valid, msg = validate_email(email)
    if not valid:
        return error_response(msg, 'INVALID_EMAIL', 400)

    valid, msg = validate_password(password)
    if not valid:
        return error_response(msg, 'INVALID_PASSWORD', 400)

    if User.query.filter_by(username=username).first():
        return error_response('Username already exists', 'USERNAME_TAKEN', 409)

    if User.query.filter_by(email=email).first():
        return error_response('Email already registered', 'EMAIL_TAKEN', 409)

    user = User(
        username=username,
        email=email,
        full_name=full_name or username,
        role='user',
        is_active=True,
        is_verified=True
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return success_response(
        data={
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        },
        message='Registration successful',
        status_code=201
    )


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return error_response('Request body is required', status_code=400)

    identifier = data.get('email', data.get('username', '')).strip()
    password = data.get('password', '')

    if not identifier or not password:
        return error_response('Email/username and password are required', 'MISSING_FIELDS', 400)

    user = User.query.filter(
        (User.email == identifier.lower()) | (User.username == identifier)
    ).first()

    if not user or not user.check_password(password):
        return error_response('Invalid credentials', 'INVALID_CREDENTIALS', 401)

    if not user.is_active:
        return error_response('Account is deactivated', 'ACCOUNT_DISABLED', 403)

    user.last_login = datetime.utcnow()
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return success_response(
        data={
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        },
        message='Login successful'
    )


@auth_bp.route('/api/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return success_response(data={'access_token': access_token})


@auth_bp.route('/api/auth/logout', methods=['POST'])
@jwt_required(optional=True)
def logout():
    return success_response(message='Logged out successfully')


@auth_bp.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return error_response('User not found', 'NOT_FOUND', 404)
    return success_response(data={'user': user.to_dict()})


@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email', '').strip().lower()

    user = User.query.filter_by(email=email).first()
    if user:
        token = generate_reset_token()
        user.reset_token = token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        # In production: send email with reset link

    return success_response(message='If the email exists, a reset link has been sent.')


@auth_bp.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token', '')
    new_password = data.get('password', '')

    valid, msg = validate_password(new_password)
    if not valid:
        return error_response(msg, 'INVALID_PASSWORD', 400)

    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        return error_response('Invalid or expired reset token', 'INVALID_TOKEN', 400)

    user.set_password(new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.session.commit()

    return success_response(message='Password reset successfully')


@auth_bp.route('/api/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    data = request.get_json()

    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')

    if not user.check_password(current_password):
        return error_response('Current password is incorrect', 'WRONG_PASSWORD', 400)

    valid, msg = validate_password(new_password)
    if not valid:
        return error_response(msg, 'INVALID_PASSWORD', 400)

    user.set_password(new_password)
    db.session.commit()

    return success_response(message='Password changed successfully')


@auth_bp.route('/api/auth/update-profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    data = request.get_json()

    if 'full_name' in data:
        user.full_name = data['full_name'].strip()
    if 'github_username' in data:
        user.github_username = data['github_username'].strip()

    db.session.commit()
    return success_response(data={'user': user.to_dict()}, message='Profile updated')
