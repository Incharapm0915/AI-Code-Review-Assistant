from datetime import datetime
from backend.extensions import db


class PastedCode(db.Model):
    __tablename__ = 'pasted_code_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=True, default='Untitled Snippet')
    code_content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False, default='python')
    line_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')
    quality_score = db.Column(db.Float, nullable=True)
    issue_count = db.Column(db.Integer, default=0)
    vulnerability_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    report = db.relationship('ReviewReport', backref='pasted_code', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'language': self.language,
            'line_count': self.line_count,
            'status': self.status,
            'quality_score': self.quality_score,
            'issue_count': self.issue_count,
            'vulnerability_count': self.vulnerability_count,
            'code_preview': self.code_content[:200] + '...' if len(self.code_content) > 200 else self.code_content,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<PastedCode {self.id} - {self.language}>'
