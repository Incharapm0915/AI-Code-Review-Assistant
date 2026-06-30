from datetime import datetime
from backend.extensions import db


class GitHubRepository(db.Model):
    __tablename__ = 'github_repositories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    repo_name = db.Column(db.String(200), nullable=False)
    repo_full_name = db.Column(db.String(300), nullable=False)
    repo_url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    language = db.Column(db.String(50), nullable=True)
    stars = db.Column(db.Integer, default=0)
    forks = db.Column(db.Integer, default=0)
    is_private = db.Column(db.Boolean, default=False)
    last_analyzed = db.Column(db.DateTime, nullable=True)
    analysis_count = db.Column(db.Integer, default=0)
    avg_quality_score = db.Column(db.Float, nullable=True)
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'repo_name': self.repo_name,
            'repo_full_name': self.repo_full_name,
            'repo_url': self.repo_url,
            'description': self.description,
            'language': self.language,
            'stars': self.stars,
            'forks': self.forks,
            'is_private': self.is_private,
            'last_analyzed': self.last_analyzed.isoformat() if self.last_analyzed else None,
            'analysis_count': self.analysis_count,
            'avg_quality_score': self.avg_quality_score,
            'connected_at': self.connected_at.isoformat()
        }

    def __repr__(self):
        return f'<GitHubRepository {self.repo_full_name}>'
