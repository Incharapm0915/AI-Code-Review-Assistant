import os
from flask import Flask, jsonify
from backend.config import config
from backend.extensions import db, jwt, bcrypt, cors, mail, migrate, socketio


def create_app(config_name: str = None) -> Flask:
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    )
    app.config.from_object(config.get(config_name, config['default']))

    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _ensure_directories(app)

    with app.app_context():
        db.create_all()
        _create_default_admin(app)

    return app


def _init_extensions(app: Flask):
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r'/api/*': {'origins': app.config.get('CORS_ORIGINS', '*')}})
    mail.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins='*', async_mode='threading')


def _register_blueprints(app: Flask):
    from backend.routes.auth import auth_bp
    from backend.routes.api import api_bp
    from backend.routes.views import views_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(views_bp)


def _register_error_handlers(app: Flask):
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Resource not found', 'code': 'NOT_FOUND'}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'error': 'Internal server error', 'code': 'SERVER_ERROR'}), 500

    @app.errorhandler(413)
    def file_too_large(e):
        return jsonify({'error': 'File too large. Maximum size is 16MB.', 'code': 'FILE_TOO_LARGE'}), 413

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return jsonify({'error': 'Token has expired', 'code': 'TOKEN_EXPIRED'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token', 'code': 'INVALID_TOKEN'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Authentication required', 'code': 'UNAUTHORIZED'}), 401


def _ensure_directories(app: Flask):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)


def _create_default_admin(app: Flask):
    from backend.models.user import User
    admin_email = app.config.get('ADMIN_EMAIL', 'admin@aicodereviewer.com')
    admin_password = app.config.get('ADMIN_PASSWORD', 'Admin@123456')

    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            username='admin',
            email=admin_email,
            full_name='System Administrator',
            role='admin',
            is_active=True,
            is_verified=True
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
