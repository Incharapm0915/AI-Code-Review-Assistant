from datetime import datetime
import json
from backend.extensions import db


class ReviewReport(db.Model):
    __tablename__ = 'review_reports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_file_id = db.Column(db.Integer, db.ForeignKey('uploaded_files.id'), nullable=True)
    pasted_code_id = db.Column(db.Integer, db.ForeignKey('pasted_code_history.id'), nullable=True)
    source_type = db.Column(db.String(20), nullable=False)  # 'upload', 'paste', 'github'
    language = db.Column(db.String(50), nullable=False)
    quality_score = db.Column(db.Float, default=0.0)
    complexity_score = db.Column(db.Float, default=0.0)
    security_score = db.Column(db.Float, default=0.0)
    maintainability_score = db.Column(db.Float, default=0.0)
    total_issues = db.Column(db.Integer, default=0)
    critical_issues = db.Column(db.Integer, default=0)
    warnings = db.Column(db.Integer, default=0)
    suggestions = db.Column(db.Integer, default=0)
    vulnerabilities = db.Column(db.Integer, default=0)
    lines_analyzed = db.Column(db.Integer, default=0)
    issues_data = db.Column(db.Text, nullable=True)  # JSON
    suggestions_data = db.Column(db.Text, nullable=True)  # JSON
    vulnerabilities_data = db.Column(db.Text, nullable=True)  # JSON
    metrics_data = db.Column(db.Text, nullable=True)  # JSON
    report_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    vulnerability_logs = db.relationship('VulnerabilityLog', backref='report', lazy=True, cascade='all, delete-orphan')

    def get_issues(self):
        return json.loads(self.issues_data) if self.issues_data else []

    def get_suggestions(self):
        return json.loads(self.suggestions_data) if self.suggestions_data else []

    def get_vulnerabilities(self):
        return json.loads(self.vulnerabilities_data) if self.vulnerabilities_data else []

    def get_metrics(self):
        return json.loads(self.metrics_data) if self.metrics_data else {}

    def set_issues(self, data):
        self.issues_data = json.dumps(data)

    def set_suggestions(self, data):
        self.suggestions_data = json.dumps(data)

    def set_vulnerabilities(self, data):
        self.vulnerabilities_data = json.dumps(data)

    def set_metrics(self, data):
        self.metrics_data = json.dumps(data)

    @staticmethod
    def _get_grade(score):
        if score >= 90: return 'A'
        if score >= 80: return 'B'
        if score >= 70: return 'C'
        if score >= 60: return 'D'
        return 'F'

    @staticmethod
    def _get_verdict(score):
        if score >= 85:
            return 'Excellent', 'This code is well-written with only minor issues to address.'
        if score >= 70:
            return 'Good', 'This code is generally good but has some areas that need attention.'
        if score >= 55:
            return 'Fair', 'This code needs significant improvements before production use.'
        return 'Poor', 'This code has critical issues that must be resolved immediately.'

    def to_dict(self):
        overall = round(
            self.quality_score * 0.35 +
            self.security_score * 0.30 +
            self.complexity_score * 0.20 +
            self.maintainability_score * 0.15, 1
        )
        grade = self._get_grade(overall)
        verdict, description = self._get_verdict(overall)
        issues = self.get_issues()
        raw_metrics = self.get_metrics()
        best_practices = raw_metrics.pop('best_practices', [])

        return {
            'id': self.id,
            'source_type': self.source_type,
            'language': self.language,
            'quality_score': round(self.quality_score, 1),
            'complexity_score': round(self.complexity_score, 1),
            'security_score': round(self.security_score, 1),
            'maintainability_score': round(self.maintainability_score, 1),
            'total_issues': self.total_issues,
            'critical_issues': self.critical_issues,
            'warnings': self.warnings,
            'suggestions': self.suggestions,
            'vulnerabilities': self.vulnerabilities,
            'lines_analyzed': self.lines_analyzed,
            'issues': issues,
            'suggestions_list': self.get_suggestions(),
            'vulnerabilities_list': self.get_vulnerabilities(),
            'metrics': raw_metrics,
            'best_practices': best_practices,
            'created_at': self.created_at.isoformat(),
            'scores': {
                'quality': round(self.quality_score, 1),
                'security': round(self.security_score, 1),
                'complexity': round(self.complexity_score, 1),
                'maintainability': round(self.maintainability_score, 1),
                'overall': overall,
                'grade': grade,
            },
            'summary': {
                'verdict': verdict,
                'description': description,
                'overall_score': overall,
                'grade': grade,
                'critical_issues': sum(1 for i in issues if i.get('severity') == 'critical'),
                'high_issues': sum(1 for i in issues if i.get('severity') == 'high'),
                'vulnerabilities': self.vulnerabilities,
            },
        }

    def __repr__(self):
        return f'<ReviewReport {self.id} score={self.quality_score}>'
