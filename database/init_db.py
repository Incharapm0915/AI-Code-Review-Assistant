"""
Database initialization script.
Run this once to set up the database with schema and seed data.
Usage: python database/init_db.py
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import create_app
from backend.extensions import db
from backend.models import User, UploadedFile, PastedCode, ReviewReport


def init_database():
    app = create_app('development')

    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✓ Tables created")

        _seed_admin(app)
        _seed_sample_data(app)

        print("\n✅ Database initialized successfully!")
        print(f"   Database: {app.config['SQLALCHEMY_DATABASE_URI']}")


def _seed_admin(app):
    admin_email = app.config.get('ADMIN_EMAIL', 'admin@aicodereviewer.com')
    if User.query.filter_by(email=admin_email).first():
        print(f"✓ Admin user already exists ({admin_email})")
        return

    admin = User(
        username='admin',
        email=admin_email,
        full_name='System Administrator',
        role='admin',
        is_active=True,
        is_verified=True
    )
    admin.set_password(app.config.get('ADMIN_PASSWORD', 'Admin@123456'))
    db.session.add(admin)
    db.session.commit()
    print(f"✓ Admin user created: {admin_email}")


def _seed_sample_data(app):
    demo_user = User.query.filter_by(username='demo').first()
    if demo_user:
        print("✓ Demo user already exists")
        return

    demo = User(
        username='demo',
        email='demo@aicodereviewer.com',
        full_name='Demo Developer',
        role='user',
        is_active=True,
        is_verified=True
    )
    demo.set_password('Demo@123456')
    db.session.add(demo)
    db.session.flush()

    print(f"✓ Demo user created: demo@aicodereviewer.com / Demo@123456")


if __name__ == '__main__':
    init_database()
