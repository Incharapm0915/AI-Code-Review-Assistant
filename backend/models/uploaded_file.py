from datetime import datetime
from backend.extensions import db


class UploadedFile(db.Model):
    __tablename__ = 'uploaded_files'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    language = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    quality_score = db.Column(db.Float, nullable=True)
    issue_count = db.Column(db.Integer, default=0)
    vulnerability_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    report = db.relationship('ReviewReport', backref='uploaded_file', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.original_filename,
            'language': self.language,
            'status': self.status,
            'quality_score': self.quality_score,
            'issue_count': self.issue_count,
            'vulnerability_count': self.vulnerability_count,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<UploadedFile {self.original_filename}>'
