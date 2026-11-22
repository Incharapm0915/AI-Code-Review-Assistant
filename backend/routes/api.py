import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.extensions import db
from backend.models import User, UploadedFile, PastedCode, ReviewReport, VulnerabilityLog, GitHubRepository
from backend.services.ai_service import AIAnalyzer
from backend.services.report_generator import ReportGenerator
from backend.services.github_service import GitHubService
from backend.services.code_runner import CodeRunner
from backend.utils.helpers import generate_unique_filename, error_response, success_response
from backend.utils.validators import validate_code_input
from backend.utils.code_preprocessor import detect_language, sanitize_code, validate_file_extension

api_bp = Blueprint('api', __name__)
ai_analyzer = AIAnalyzer()
report_gen = ReportGenerator()
code_runner = CodeRunner()


# ── Dashboard ──────────────────────────────────────────────────────────────────

@api_bp.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    user_id = int(get_jwt_identity())

    total_uploads = UploadedFile.query.filter_by(user_id=user_id).count()
    total_pastes = PastedCode.query.filter_by(user_id=user_id).count()
    total_reports = ReviewReport.query.filter_by(user_id=user_id).count()

    recent_reports = ReviewReport.query.filter_by(user_id=user_id)\
        .order_by(ReviewReport.created_at.desc()).limit(5).all()

    avg_score = db.session.query(db.func.avg(ReviewReport.quality_score))\
        .filter_by(user_id=user_id).scalar() or 0

    total_vulns = db.session.query(db.func.sum(ReviewReport.vulnerabilities))\
        .filter_by(user_id=user_id).scalar() or 0

    critical_issues = db.session.query(db.func.sum(ReviewReport.critical_issues))\
        .filter_by(user_id=user_id).scalar() or 0

    return success_response(data={
        'total_uploads': total_uploads,
        'total_pastes': total_pastes,
        'total_reviews': total_reports,
        'avg_quality_score': round(float(avg_score), 1),
        'total_vulnerabilities': int(total_vulns),
        'critical_issues': int(critical_issues),
        'recent_reports': [r.to_dict() for r in recent_reports]
    })


@api_bp.route('/api/dashboard/activity', methods=['GET'])
@jwt_required()
def dashboard_activity():
    user_id = int(get_jwt_identity())
    days = int(request.args.get('days', 7))

    reports = ReviewReport.query.filter_by(user_id=user_id)\
        .order_by(ReviewReport.created_at.desc()).limit(50).all()

    activity = [{'date': r.created_at.strftime('%Y-%m-%d'), 'score': r.quality_score, 'type': r.source_type}
                for r in reports]

    return success_response(data={'activity': activity})


# ── Code Upload ────────────────────────────────────────────────────────────────

@api_bp.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_code():
    user_id = int(get_jwt_identity())

    if 'file' not in request.files:
        return error_response('No file provided', 'NO_FILE', 400)

    file = request.files['file']
    if not file.filename:
        return error_response('No file selected', 'NO_FILENAME', 400)

    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'py', 'java', 'js', 'cpp', 'c', 'h'})
    if not validate_file_extension(file.filename, allowed):
        return error_response(f'File type not supported. Allowed: {", ".join(allowed)}', 'INVALID_TYPE', 400)

    language = detect_language(file.filename)
    code_content = file.read().decode('utf-8', errors='ignore')
    code_content = sanitize_code(code_content)

    unique_filename = generate_unique_filename(file.filename)
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, unique_filename)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(code_content)

    uploaded_file = UploadedFile(
        user_id=user_id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(code_content.encode()),
        language=language,
        status='processing'
    )
    db.session.add(uploaded_file)
    db.session.flush()

    try:
        result = ai_analyzer.analyze_code(code_content, language)
        report = _create_report(user_id, result, language, 'upload', uploaded_file_id=uploaded_file.id)
        _save_vulnerability_logs(report.id, result.get('vulnerabilities', []))

        uploaded_file.status = 'completed'
        uploaded_file.quality_score = result['scores']['quality']
        uploaded_file.issue_count = len(result.get('issues', []))
        uploaded_file.vulnerability_count = len(result.get('vulnerabilities', []))
        db.session.commit()

        return success_response(
            data={'file_id': uploaded_file.id, 'report_id': report.id, 'report': report.to_dict()},
            message='File uploaded and analyzed successfully',
            status_code=201
        )
    except Exception as e:
        uploaded_file.status = 'failed'
        db.session.commit()
        return error_response(f'Analysis failed: {str(e)}', 'ANALYSIS_FAILED', 500)


@api_bp.route('/api/upload/history', methods=['GET'])
@jwt_required()
def upload_history():
    user_id = int(get_jwt_identity())
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    uploads = UploadedFile.query.filter_by(user_id=user_id)\
        .order_by(UploadedFile.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return success_response(data={
        'uploads': [u.to_dict() for u in uploads.items],
        'total': uploads.total,
        'pages': uploads.pages,
        'current_page': page
    })


# ── Code Editor (Paste) ────────────────────────────────────────────────────────

@api_bp.route('/api/analyze', methods=['POST'])
@jwt_required()
def analyze_pasted_code():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    code = data.get('code', '').strip()
    language = data.get('language', 'python').lower()
    title = data.get('title', 'Untitled Snippet')

    valid, msg = validate_code_input(code, language)
    if not valid:
        return error_response(msg, 'INVALID_INPUT', 400)

    code = sanitize_code(code)
    lines = code.split('\n')

    pasted = PastedCode(
        user_id=user_id,
        title=title,
        code_content=code,
        language=language,
        line_count=len(lines),
        status='processing'
    )
    db.session.add(pasted)
    db.session.flush()

    try:
        result = ai_analyzer.analyze_code(code, language)
        report = _create_report(user_id, result, language, 'paste', pasted_code_id=pasted.id)
        _save_vulnerability_logs(report.id, result.get('vulnerabilities', []))

        pasted.status = 'completed'
        pasted.quality_score = result['scores']['quality']
        pasted.issue_count = len(result.get('issues', []))
        pasted.vulnerability_count = len(result.get('vulnerabilities', []))
        db.session.commit()

        return success_response(
            data={'paste_id': pasted.id, 'report_id': report.id, 'report': report.to_dict()},
            status_code=201
        )
    except Exception as e:
        pasted.status = 'failed'
        db.session.commit()
        return error_response(f'Analysis failed: {str(e)}', 'ANALYSIS_FAILED', 500)


@api_bp.route('/api/analyze/history', methods=['GET'])
@jwt_required()
def paste_history():
    user_id = int(get_jwt_identity())
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    pastes = PastedCode.query.filter_by(user_id=user_id)\
        .order_by(PastedCode.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return success_response(data={
        'pastes': [p.to_dict() for p in pastes.items],
        'total': pastes.total,
        'pages': pastes.pages,
        'current_page': page
    })


# ── Code Execution ────────────────────────────────────────────────────────────

@api_bp.route('/api/execute', methods=['POST'])
@jwt_required()
def execute_code():
    data = request.get_json() or {}
    code = (data.get('code') or '').strip()
    language = (data.get('language') or 'python').lower()
    stdin_data = data.get('stdin') or ''

    valid, msg = validate_code_input(code, language)
    if not valid:
        return error_response(msg, 'INVALID_INPUT', 400)

    code = sanitize_code(code)
    stdin_data = stdin_data[:20000]

    result = code_runner.run(code, language, stdin_data)
    if not result.get('success'):
        return error_response(result.get('error', 'Execution is unavailable'), 'EXECUTION_UNAVAILABLE', 422)

    return success_response(data=result)


# ── Reports ────────────────────────────────────────────────────────────────────

@api_bp.route('/api/reports/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report(report_id):
    user_id = int(get_jwt_identity())
    report = ReviewReport.query.filter_by(id=report_id, user_id=user_id).first()
    if not report:
        return error_response('Report not found', 'NOT_FOUND', 404)
    return success_response(data={'report': report.to_dict()})


@api_bp.route('/api/reports/<int:report_id>/download', methods=['GET'])
@jwt_required()
def download_report(report_id):
    user_id = int(get_jwt_identity())
    fmt = request.args.get('format', 'pdf')

    report = ReviewReport.query.filter_by(id=report_id, user_id=user_id).first()
    if not report:
        return error_response('Report not found', 'NOT_FOUND', 404)

    user = db.session.get(User, user_id)
    reports_folder = current_app.config['REPORTS_FOLDER']
    filename = f'report_{report_id}_{datetime.now().strftime("%Y%m%d%H%M%S")}'

    report_data = report.to_dict()

    if fmt == 'txt':
        out_path = os.path.join(reports_folder, f'{filename}.txt')
        report_gen.generate_text_report(report_data, out_path)
        return send_file(out_path, as_attachment=True, download_name=f'review_report_{report_id}.txt')
    else:
        out_path = os.path.join(reports_folder, f'{filename}.pdf')
        report_gen.generate_pdf(report_data, out_path, user_info=user.to_dict())
        return send_file(out_path, as_attachment=True, download_name=f'review_report_{report_id}.pdf')


@api_bp.route('/api/reports', methods=['GET'])
@jwt_required()
def list_reports():
    user_id = int(get_jwt_identity())
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    reports = ReviewReport.query.filter_by(user_id=user_id)\
        .order_by(ReviewReport.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return success_response(data={
        'reports': [r.to_dict() for r in reports.items],
        'total': reports.total,
        'pages': reports.pages,
        'current_page': page
    })


# ── GitHub Integration ─────────────────────────────────────────────────────────

@api_bp.route('/api/github/connect', methods=['POST'])
@jwt_required()
def github_connect():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    token = data.get('token', '').strip()

    if not token:
        return error_response('GitHub token is required', 'MISSING_TOKEN', 400)

    svc = GitHubService(token)
    if not svc.validate_token():
        return error_response('Invalid GitHub token', 'INVALID_TOKEN', 401)

    gh_user = svc.get_authenticated_user()
    user = db.session.get(User, user_id)
    user.github_token = token
    user.github_username = gh_user.get('username', '')
    db.session.commit()

    return success_response(data={'github_user': gh_user}, message='GitHub connected successfully')


@api_bp.route('/api/github/repos', methods=['GET'])
@jwt_required()
def github_repos():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)

    if not user.github_token:
        return error_response('GitHub not connected', 'NOT_CONNECTED', 400)

    try:
        svc = GitHubService(user.github_token)
        repos = svc.get_user_repos()
        return success_response(data={'repos': repos})
    except Exception as e:
        return error_response(str(e), 'GITHUB_ERROR', 500)


@api_bp.route('/api/github/analyze', methods=['POST'])
@jwt_required()
def github_analyze():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    data = request.get_json()

    repo_full_name = data.get('repo', '')
    file_path = data.get('file_path', '')
    branch = data.get('branch', 'main')

    if not user.github_token:
        return error_response('GitHub not connected', 'NOT_CONNECTED', 400)

    try:
        svc = GitHubService(user.github_token)
        content = svc.get_file_content(repo_full_name, file_path, branch)

        if not content:
            return error_response('Could not fetch file content', 'FETCH_FAILED', 400)

        language = detect_language(file_path)
        result = ai_analyzer.analyze_code(content, language)
        report = _create_report(user_id, result, language, 'github')
        _save_vulnerability_logs(report.id, result.get('vulnerabilities', []))
        db.session.commit()

        return success_response(data={'report_id': report.id, 'report': report.to_dict()})
    except Exception as e:
        return error_response(str(e), 'GITHUB_ERROR', 500)


@api_bp.route('/api/github/repos/save', methods=['POST'])
@jwt_required()
def save_github_repo():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    existing = GitHubRepository.query.filter_by(
        user_id=user_id, repo_full_name=data.get('repo_full_name', '')
    ).first()

    if existing:
        return success_response(data={'repo': existing.to_dict()}, message='Repository already connected')

    repo = GitHubRepository(
        user_id=user_id,
        repo_name=data.get('repo_name', ''),
        repo_full_name=data.get('repo_full_name', ''),
        repo_url=data.get('repo_url', ''),
        description=data.get('description', ''),
        language=data.get('language', ''),
        stars=data.get('stars', 0),
        forks=data.get('forks', 0),
        is_private=data.get('is_private', False)
    )
    db.session.add(repo)
    db.session.commit()

    return success_response(data={'repo': repo.to_dict()}, status_code=201)


@api_bp.route('/api/github/connected-repos', methods=['GET'])
@jwt_required()
def connected_repos():
    user_id = int(get_jwt_identity())
    repos = GitHubRepository.query.filter_by(user_id=user_id).all()
    return success_response(data={'repos': [r.to_dict() for r in repos]})


# ── Admin ──────────────────────────────────────────────────────────────────────

@api_bp.route('/api/admin/users', methods=['GET'])
@jwt_required()
def admin_users():
    from backend.utils.helpers import admin_required
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user or user.role != 'admin':
        return error_response('Admin access required', 'FORBIDDEN', 403)

    page = int(request.args.get('page', 1))
    users = User.query.order_by(User.created_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)

    return success_response(data={
        'users': [u.to_dict() for u in users.items],
        'total': users.total,
        'pages': users.pages
    })


@api_bp.route('/api/admin/stats', methods=['GET'])
@jwt_required()
def admin_stats():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user or user.role != 'admin':
        return error_response('Admin access required', 'FORBIDDEN', 403)

    return success_response(data={
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'total_uploads': UploadedFile.query.count(),
        'total_pastes': PastedCode.query.count(),
        'total_reports': ReviewReport.query.count(),
        'total_vulnerabilities': VulnerabilityLog.query.count(),
    })


@api_bp.route('/api/admin/users/<int:uid>/toggle', methods=['POST'])
@jwt_required()
def admin_toggle_user(uid):
    user_id = int(get_jwt_identity())
    admin = db.session.get(User, user_id)
    if not admin or admin.role != 'admin':
        return error_response('Admin access required', 'FORBIDDEN', 403)

    target = db.session.get(User, uid)
    if not target:
        return error_response('User not found', 'NOT_FOUND', 404)

    target.is_active = not target.is_active
    db.session.commit()

    return success_response(data={'user': target.to_dict()}, message=f'User {"activated" if target.is_active else "deactivated"}')


# ── Helpers ────────────────────────────────────────────────────────────────────

def _create_report(user_id, result, language, source_type, uploaded_file_id=None, pasted_code_id=None):
    issues = result.get('issues', [])
    vulnerabilities = result.get('vulnerabilities', [])
    scores = result.get('scores', {})

    report = ReviewReport(
        user_id=user_id,
        uploaded_file_id=uploaded_file_id,
        pasted_code_id=pasted_code_id,
        source_type=source_type,
        language=language,
        quality_score=scores.get('quality', 0),
        complexity_score=scores.get('complexity', 0),
        security_score=scores.get('security', 0),
        maintainability_score=scores.get('maintainability', 0),
        total_issues=len(issues),
        critical_issues=sum(1 for i in issues if i.get('severity') == 'critical'),
        warnings=sum(1 for i in issues if i.get('severity') in ('high', 'medium')),
        suggestions=len(result.get('optimizations', [])),
        vulnerabilities=len(vulnerabilities),
        lines_analyzed=result.get('line_stats', {}).get('total', 0)
    )
    metrics = dict(result.get('metrics', {}))
    metrics['best_practices'] = result.get('best_practices', [])

    report.set_issues(issues)
    report.set_suggestions(result.get('optimizations', []))
    report.set_vulnerabilities(vulnerabilities)
    report.set_metrics(metrics)

    db.session.add(report)
    db.session.flush()
    return report


def _save_vulnerability_logs(report_id, vulnerabilities):
    for vuln in vulnerabilities:
        log = VulnerabilityLog(
            report_id=report_id,
            severity=vuln.get('severity', 'medium'),
            category=vuln.get('category', 'Unknown'),
            description=vuln.get('description', ''),
            line_number=vuln.get('line'),
            code_snippet=vuln.get('code_snippet', ''),
            recommendation=vuln.get('recommendation', ''),
            cve_id=vuln.get('cve', '')
        )
        db.session.add(log)
