from flask import Blueprint, render_template, redirect, url_for

views_bp = Blueprint('views', __name__)


@views_bp.route('/')
def index():
    return render_template('index.html')


@views_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@views_bp.route('/upload')
def upload():
    return render_template('upload.html')


@views_bp.route('/editor')
def editor():
    return render_template('editor.html')


@views_bp.route('/results/<int:report_id>')
def results(report_id):
    return render_template('results.html', report_id=report_id)


@views_bp.route('/github')
def github():
    return render_template('github.html')


@views_bp.route('/admin')
def admin():
    return render_template('admin/panel.html')


@views_bp.route('/profile')
def profile():
    return render_template('profile.html')


@views_bp.route('/reports')
def reports():
    return render_template('reports/list.html')
