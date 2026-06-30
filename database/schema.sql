-- ═══════════════════════════════════════════════════════════════════
-- AI Code Review Assistant — Database Schema
-- Compatible with SQLite and MySQL
-- ═══════════════════════════════════════════════════════════════════

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        VARCHAR(80)  NOT NULL UNIQUE,
    email           VARCHAR(120) NOT NULL UNIQUE,
    password_hash   VARCHAR(256) NOT NULL,
    full_name       VARCHAR(150),
    avatar_url      VARCHAR(500),
    role            VARCHAR(20)  NOT NULL DEFAULT 'user',
    is_active       BOOLEAN      NOT NULL DEFAULT 1,
    is_verified     BOOLEAN      NOT NULL DEFAULT 0,
    github_username VARCHAR(100),
    github_token    VARCHAR(500),
    reset_token     VARCHAR(256),
    reset_token_expiry DATETIME,
    last_login      DATETIME,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email    ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Uploaded Files Table
CREATE TABLE IF NOT EXISTS uploaded_files (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename          VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path         VARCHAR(500) NOT NULL,
    file_size         INTEGER,
    language          VARCHAR(50)  NOT NULL,
    status            VARCHAR(20)  NOT NULL DEFAULT 'pending',
    quality_score     REAL,
    issue_count       INTEGER      DEFAULT 0,
    vulnerability_count INTEGER    DEFAULT 0,
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_uploaded_files_user ON uploaded_files(user_id);

-- Pasted Code History Table
CREATE TABLE IF NOT EXISTS pasted_code_history (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title             VARCHAR(200) DEFAULT 'Untitled Snippet',
    code_content      TEXT         NOT NULL,
    language          VARCHAR(50)  NOT NULL DEFAULT 'python',
    line_count        INTEGER      DEFAULT 0,
    status            VARCHAR(20)  NOT NULL DEFAULT 'pending',
    quality_score     REAL,
    issue_count       INTEGER      DEFAULT 0,
    vulnerability_count INTEGER    DEFAULT 0,
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pasted_code_user ON pasted_code_history(user_id);

-- Review Reports Table
CREATE TABLE IF NOT EXISTS review_reports (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id              INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    uploaded_file_id     INTEGER     REFERENCES uploaded_files(id) ON DELETE SET NULL,
    pasted_code_id       INTEGER     REFERENCES pasted_code_history(id) ON DELETE SET NULL,
    source_type          VARCHAR(20) NOT NULL,
    language             VARCHAR(50) NOT NULL,
    quality_score        REAL        DEFAULT 0.0,
    complexity_score     REAL        DEFAULT 0.0,
    security_score       REAL        DEFAULT 0.0,
    maintainability_score REAL       DEFAULT 0.0,
    total_issues         INTEGER     DEFAULT 0,
    critical_issues      INTEGER     DEFAULT 0,
    warnings             INTEGER     DEFAULT 0,
    suggestions          INTEGER     DEFAULT 0,
    vulnerabilities      INTEGER     DEFAULT 0,
    lines_analyzed       INTEGER     DEFAULT 0,
    issues_data          TEXT,
    suggestions_data     TEXT,
    vulnerabilities_data TEXT,
    metrics_data         TEXT,
    report_path          VARCHAR(500),
    created_at           DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_review_reports_user ON review_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_review_reports_created ON review_reports(created_at);

-- Vulnerability Logs Table
CREATE TABLE IF NOT EXISTS vulnerability_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id       INTEGER      NOT NULL REFERENCES review_reports(id) ON DELETE CASCADE,
    severity        VARCHAR(20)  NOT NULL,
    category        VARCHAR(100) NOT NULL,
    description     TEXT         NOT NULL,
    line_number     INTEGER,
    code_snippet    TEXT,
    recommendation  TEXT,
    cve_id          VARCHAR(50),
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vuln_logs_report  ON vulnerability_logs(report_id);
CREATE INDEX IF NOT EXISTS idx_vuln_logs_severity ON vulnerability_logs(severity);

-- GitHub Repositories Table
CREATE TABLE IF NOT EXISTS github_repositories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    repo_name       VARCHAR(200) NOT NULL,
    repo_full_name  VARCHAR(300) NOT NULL,
    repo_url        VARCHAR(500) NOT NULL,
    description     TEXT,
    language        VARCHAR(50),
    stars           INTEGER      DEFAULT 0,
    forks           INTEGER      DEFAULT 0,
    is_private      BOOLEAN      DEFAULT 0,
    last_analyzed   DATETIME,
    analysis_count  INTEGER      DEFAULT 0,
    avg_quality_score REAL,
    connected_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_github_repos_user ON github_repositories(user_id);

-- Admin Logs Table
CREATE TABLE IF NOT EXISTS admin_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id    INTEGER      REFERENCES users(id) ON DELETE SET NULL,
    action      VARCHAR(200) NOT NULL,
    target_type VARCHAR(50),
    target_id   INTEGER,
    details     TEXT,
    ip_address  VARCHAR(50),
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_admin_logs_admin   ON admin_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_logs_created ON admin_logs(created_at);
