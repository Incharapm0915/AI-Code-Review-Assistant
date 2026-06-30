# 🤖 AI Code Review Assistant for Developers

> An intelligent, full-stack source code review platform powered by AI, ML, and NLP. Detect bugs, security vulnerabilities, and performance issues instantly with detailed reports.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-green?logo=flask)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)

---

## ✨ Features

| Category | Features |
|----------|----------|
| **AI Analysis** | Static analysis, NLP semantics, ML quality scoring, complexity metrics |
| **Security** | SQL injection, XSS, command injection, 50+ vulnerability patterns |
| **Languages** | Python, JavaScript, Java, C++ |
| **Editor** | Monaco Editor with real-time analysis, syntax highlighting |
| **Reports** | PDF/TXT reports with scores, issues, recommendations |
| **GitHub** | Repository connection, PR analysis, automated comments |
| **Auth** | JWT authentication, role-based access, password reset |
| **Admin** | User management, analytics, system monitoring |
| **UI/UX** | Glassmorphism, dark/light mode, responsive, animated |

---

## 🗂 Project Structure

```
ai-code-review-assistant/
├── backend/                    # Flask application
│   ├── __init__.py             # App factory
│   ├── config.py               # Configuration classes
│   ├── extensions.py           # Flask extensions
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── uploaded_file.py
│   │   ├── pasted_code.py
│   │   ├── review_report.py
│   │   ├── vulnerability_log.py
│   │   └── github_repo.py
│   ├── routes/                 # API and view routes
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── api.py              # Main REST API
│   │   └── views.py            # Page routes
│   ├── services/               # Business logic
│   │   ├── ai_service.py       # Core AI analysis engine
│   │   ├── static_analysis.py  # Pattern-based analysis
│   │   ├── security_scanner.py # Vulnerability detection
│   │   ├── report_generator.py # PDF/TXT report generation
│   │   └── github_service.py   # GitHub API integration
│   └── utils/                  # Helper utilities
│       ├── code_preprocessor.py
│       ├── validators.py
│       └── helpers.py
├── models/                     # AI/ML model implementations
│   ├── ml_analyzer.py          # Scikit-learn feature-based scoring
│   ├── nlp_analyzer.py         # NLTK documentation analysis
│   ├── vulnerability_detector.py # Deep vulnerability patterns
│   └── code_complexity.py      # Halstead & cyclomatic metrics
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Base layout with sidebar
│   ├── index.html              # Landing page
│   ├── dashboard.html          # Main dashboard
│   ├── editor.html             # Monaco code editor
│   ├── upload.html             # File upload
│   ├── results.html            # Analysis results
│   ├── github.html             # GitHub integration
│   ├── profile.html            # User profile
│   ├── auth/                   # Login, Register, Reset
│   ├── admin/                  # Admin panel
│   └── reports/                # Report views
├── static/
│   ├── css/main.css            # Premium UI stylesheet
│   └── js/                     # Frontend JavaScript
│       ├── main.js             # Core app logic, API client
│       ├── dashboard.js        # Dashboard charts
│       └── editor.js           # Monaco editor integration
├── database/
│   ├── schema.sql              # Full SQL schema
│   └── init_db.py              # DB initialization script
├── datasets/
│   ├── sample_good_code.py     # Clean code example
│   ├── sample_bad_code.py      # Vulnerable code example
│   ├── vulnerability_patterns.json
│   └── coding_standards.json
├── uploads/                    # Uploaded source files (gitignored)
├── reports/                    # Generated PDF reports (gitignored)
├── requirements.txt
├── run.py                      # Application entry point
└── .env.example                # Environment variable template
```

---

## ⚡ Quick Start

### Prerequisites

- Python 3.10+
- pip
- Git

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/ai-code-review-assistant.git
cd ai-code-review-assistant

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

Key variables to set:

```env
SECRET_KEY=your-random-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
DATABASE_URL=sqlite:///database/ai_code_review.db
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=Admin@123456
GITHUB_TOKEN=ghp_your_token  # Optional
```

### 4. Initialize Database

```bash
python database/init_db.py
```

### 5. Run the Application

```bash
python run.py
```

Open your browser at **http://localhost:5000**

---

## 🔑 Default Credentials

| Account | Email | Password |
|---------|-------|----------|
| Admin | admin@aicodereviewer.com | Admin@123456 |
| Demo  | demo@aicodereviewer.com  | Demo@123456  |

---

## 📡 REST API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, returns JWT |
| POST | `/api/auth/logout` | Logout |
| GET  | `/api/auth/me` | Get current user |
| POST | `/api/auth/forgot-password` | Request password reset |
| POST | `/api/auth/reset-password` | Reset with token |
| POST | `/api/auth/change-password` | Change password |
| PUT  | `/api/auth/update-profile` | Update profile |

### Code Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyze` | Analyze pasted code |
| POST | `/api/upload` | Upload and analyze file |
| GET  | `/api/analyze/history` | Paste analysis history |
| GET  | `/api/upload/history` | Upload history |

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports` | List all reports |
| GET | `/api/reports/<id>` | Get report by ID |
| GET | `/api/reports/<id>/download?format=pdf` | Download PDF report |
| GET | `/api/reports/<id>/download?format=txt` | Download text report |

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats` | Summary statistics |
| GET | `/api/dashboard/activity?days=7` | Activity trend |

### GitHub Integration

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/github/connect` | Connect GitHub token |
| GET  | `/api/github/repos` | List user repositories |
| POST | `/api/github/analyze` | Analyze a repo file |
| POST | `/api/github/repos/save` | Save connected repo |
| GET  | `/api/github/connected-repos` | List connected repos |

### Admin (Admin role required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/admin/stats` | Platform statistics |
| GET  | `/api/admin/users` | List all users |
| POST | `/api/admin/users/<id>/toggle` | Toggle user active status |

---

## 🧠 AI Analysis Pipeline

```
User Code Input
      │
      ▼
┌─────────────────────────────┐
│  1. Code Preprocessor       │ Tokenize, parse, sanitize, detect language
└───────────┬─────────────────┘
            │
            ▼
┌─────────────────────────────┐
│  2. Static Code Analysis    │ Pattern matching, AST parsing, style checks
└───────────┬─────────────────┘
            │
            ▼
┌─────────────────────────────┐
│  3. Security Scanner        │ 50+ vulnerability patterns, OWASP Top 10
└───────────┬─────────────────┘
            │
            ▼
┌─────────────────────────────┐
│  4. AI/ML Analysis          │ Feature extraction, complexity metrics,
│     (AIAnalyzer)            │ optimization suggestions, best practices
└───────────┬─────────────────┘
            │
            ▼
┌─────────────────────────────┐
│  5. Scoring Engine          │ Quality, Security, Complexity,
│                             │ Maintainability scores (0–100)
└───────────┬─────────────────┘
            │
            ▼
┌─────────────────────────────┐
│  6. Report Generator        │ PDF/TXT reports via ReportLab
└───────────┬─────────────────┘
            │
            ▼
     Results + Report
```

---

## 🔒 Security Architecture

- **JWT tokens** for stateless authentication (24h access, 30d refresh)
- **bcrypt** password hashing with automatic salt
- **SQLAlchemy ORM** — parameterized queries by default (no SQL injection)
- **Input validation** on all API endpoints
- **File upload** validation (extension, size, path traversal prevention)
- **CORS** configured for trusted origins only
- **Role-based access control** (user vs. admin)
- **Rate limiting** recommended via nginx/Flask-Limiter in production

---

## 📊 Scoring System

Each analysis produces five scores (0–100):

| Score | Weight | Factors |
|-------|--------|---------|
| **Quality** | 35% | Issues found, severity distribution |
| **Security** | 30% | Vulnerability count and severity |
| **Complexity** | 20% | Cyclomatic complexity, nesting depth |
| **Maintainability** | 15% | Halstead index, comment ratio |
| **Overall** | Weighted avg | Grade A–F |

---

## 🚀 Production Deployment

### Using Gunicorn + Nginx

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "backend:create_app('production')"
```

### Environment Variables for Production

```env
FLASK_ENV=production
DATABASE_URL=mysql+pymysql://user:pass@localhost/ai_code_review
SECRET_KEY=<64-char random hex>
JWT_SECRET_KEY=<64-char random hex>
```

### Docker (optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

---

## 🧪 Testing

```bash
# Run with sample bad code
python -c "
from backend import create_app
from backend.services.ai_service import AIAnalyzer
app = create_app()
with app.app_context():
    analyzer = AIAnalyzer()
    with open('datasets/sample_bad_code.py') as f:
        code = f.read()
    result = analyzer.analyze_code(code, 'python')
    print(f'Score: {result[\"scores\"][\"overall\"]}')
    print(f'Issues: {len(result[\"issues\"])}')
    print(f'Vulnerabilities: {len(result[\"vulnerabilities\"])}')
"
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10+, Flask 3.0, Flask-JWT-Extended |
| **Database** | SQLite (dev) / MySQL (prod) via SQLAlchemy ORM |
| **AI/ML** | Scikit-learn (ML scoring), NLTK (NLP), NumPy |
| **Static Analysis** | Python AST, Regex patterns, Radon |
| **Security** | Bandit patterns, OWASP Top 10 database |
| **Reports** | ReportLab (PDF), plain text |
| **Frontend** | HTML5, CSS3 (Glassmorphism), Vanilla JS |
| **Code Editor** | Monaco Editor (same as VS Code) |
| **Charts** | Chart.js 4 |
| **Auth** | JWT (Flask-JWT-Extended), bcrypt |
| **GitHub** | GitHub REST API v3 |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) file for details.

---

## 👥 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

*Built with ❤️ using Flask, Python, and AI/ML technologies*
