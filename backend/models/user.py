from datetime import datetime
from backend.extensions import db, bcrypt


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    role = db.Column(db.String(20), default='user')  # 'user', 'admin'
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    github_username = db.Column(db.String(100), nullable=True)
    github_token = db.Column(db.String(500), nullable=True)
    reset_token = db.Column(db.String(256), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    uploaded_files = db.relationship('UploadedFile', backref='user', lazy=True, cascade='all, delete-orphan')
    pasted_codes = db.relationship('PastedCode', backref='user', lazy=True, cascade='all, delete-orphan')
    review_reports = db.relationship('ReviewReport', backref='user', lazy=True, cascade='all, delete-orphan')
    github_repos = db.relationship('GitHubRepository', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'role': self.role,
            'is_active': self.is_active,
            'github_username': self.github_username,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<User {self.username}>'
