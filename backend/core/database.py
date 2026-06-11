"""Database connection - supports MySQL (pymysql) and SQLite (sqlite3)"""
import sys
import os
import re

# Ensure lib/ is on sys.path for bundled dependencies
_lib_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "lib")
if os.path.exists(_lib_dir) and _lib_dir not in sys.path:
    sys.path.insert(0, _lib_dir)

from contextlib import contextmanager
from backend.core.config import DATABASE_ENGINE, DB_PATH, MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

import sqlite3

if DATABASE_ENGINE == "mysql":
    import pymysql
    from pymysql.cursors import DictCursor

_engine = DATABASE_ENGINE
print(f"数据库引擎: {_engine}")


def _to_sqlite_sql(sql: str) -> str:
    """Convert MySQL SQL to SQLite-compatible SQL."""
    # Placeholders
    sql = re.sub(r'%s', '?', sql)
    # Strip MySQL engine/charset
    sql = re.sub(r'\s+ENGINE\s*=\s*\S+', '', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\s+DEFAULT\s+CHARSET\s*=\s*\S+', '', sql, flags=re.IGNORECASE)
    # TINYINT -> INTEGER
    sql = re.sub(r'\bTINYINT\b', 'INTEGER', sql, flags=re.IGNORECASE)
    # DOUBLE -> REAL
    sql = re.sub(r'\bDOUBLE\b', 'REAL', sql, flags=re.IGNORECASE)
    # VARCHAR(N) -> TEXT
    sql = re.sub(r'\bVARCHAR\s*\(\s*\d+\s*\)', 'TEXT', sql, flags=re.IGNORECASE)
    # DATETIME DEFAULT NOW() -> TEXT DEFAULT (datetime('now','localtime'))
    sql = re.sub(r"\bDATETIME\s+DEFAULT\s+NOW\s*\(\s*\)", "TEXT DEFAULT (datetime('now','localtime'))", sql, flags=re.IGNORECASE)
    # ON UPDATE NOW() -> (dropped, SQLite doesn't support it)
    sql = re.sub(r"\s+ON\s+UPDATE\s+NOW\s*\(\s*\)", "", sql, flags=re.IGNORECASE)
    return sql


# ── MySQL ─────────────────────────────────────────

def _mysql_ensure_database():
    try:
        conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD, charset='utf8mb4')
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.close()
    except Exception as e:
        raise RuntimeError(f"MySQL连接失败，请检查MySQL服务是否启动: {e}")


def _mysql_connection():
    return pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DATABASE, charset='utf8mb4', cursorclass=DictCursor)


# ── SQLite ────────────────────────────────────────

def _sqlite_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ── Unified API ───────────────────────────────────

def _ensure_database():
    if _engine == "mysql":
        _mysql_ensure_database()


def get_connection():
    if _engine == "mysql":
        return _mysql_connection()
    else:
        return _sqlite_connection()


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def execute_query(conn, sql, params=None):
    if _engine != "mysql":
        sql = _to_sqlite_sql(sql)
    cursor = conn.cursor()
    cursor.execute(sql, params or ())
    rows = cursor.fetchall()
    if _engine != "mysql":
        rows = [dict(r) for r in rows]
    return rows


def execute_insert(conn, sql, params=None):
    if _engine != "mysql":
        sql = _to_sqlite_sql(sql)
    cursor = conn.cursor()
    cursor.execute(sql, params or ())
    return cursor.lastrowid


def init_db():
    _ensure_database()
    conn = get_connection()
    try:
        cursor = conn.cursor()

        if _engine == "mysql":
            def execute(sql):
                cursor.execute(sql)
        else:
            def execute(sql):
                cursor.execute(_to_sqlite_sql(sql))

        # AE results
        execute("""
            CREATE TABLE IF NOT EXISTS ae_results (
                ae_id VARCHAR(50) PRIMARY KEY,
                patient_id VARCHAR(50) NOT NULL,
                visit_id VARCHAR(50),
                visit_date VARCHAR(50),
                ae_text TEXT NOT NULL,
                drug_name VARCHAR(100),
                onset_date VARCHAR(50),
                end_date VARCHAR(50),
                reporter VARCHAR(100),
                patient_gender VARCHAR(10),
                patient_dob VARCHAR(50),
                meddra_codes TEXT,
                severity VARCHAR(20),
                sae_flag TINYINT DEFAULT 0,
                sae_criteria TEXT,
                expected_flag TINYINT DEFAULT 0,
                causality_tentative VARCHAR(50),
                citations TEXT,
                processing_time_ms INT,
                created_at DATETIME DEFAULT NOW(),
                updated_at DATETIME DEFAULT NOW() ON UPDATE NOW()
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # SAE reports
        execute("""
            CREATE TABLE IF NOT EXISTS sae_reports (
                report_id VARCHAR(50) PRIMARY KEY,
                ae_id VARCHAR(50) NOT NULL,
                cioms_fields TEXT,
                causality_assessment TEXT,
                similar_drug_safety TEXT,
                report_status VARCHAR(20) DEFAULT 'draft',
                deadline VARCHAR(50),
                created_at DATETIME DEFAULT NOW(),
                updated_at DATETIME DEFAULT NOW() ON UPDATE NOW(),
                FOREIGN KEY (ae_id) REFERENCES ae_results(ae_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Deviation rules
        execute("""
            CREATE TABLE IF NOT EXISTS deviation_rules (
                rule_id VARCHAR(20) PRIMARY KEY,
                description TEXT,
                check_logic TEXT,
                severity VARCHAR(20),
                action VARCHAR(50),
                created_at DATETIME DEFAULT NOW()
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Deviations
        execute("""
            CREATE TABLE IF NOT EXISTS deviations (
                deviation_id VARCHAR(50) PRIMARY KEY,
                patient_id VARCHAR(50) NOT NULL,
                visit_id VARCHAR(50),
                rule_id VARCHAR(20),
                deviation_type VARCHAR(50),
                severity VARCHAR(20),
                description TEXT,
                action VARCHAR(50),
                status VARCHAR(20) DEFAULT 'open',
                resolution TEXT,
                resolved_by VARCHAR(100),
                action_taken TEXT,
                created_at DATETIME DEFAULT NOW(),
                updated_at DATETIME DEFAULT NOW() ON UPDATE NOW()
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Signals
        execute("""
            CREATE TABLE IF NOT EXISTS signals (
                signal_id VARCHAR(50) PRIMARY KEY,
                drug_name VARCHAR(100),
                signal_name VARCHAR(200),
                signal_status VARCHAR(20) DEFAULT 'new',
                event_count INT DEFAULT 0,
                incidence_rate VARCHAR(20),
                background_rate VARCHAR(20),
                statistical_test VARCHAR(50),
                related_literature TEXT,
                recommended_action TEXT,
                analysis_period VARCHAR(50),
                created_at DATETIME DEFAULT NOW(),
                updated_at DATETIME DEFAULT NOW() ON UPDATE NOW()
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Knowledge items
        execute("""
            CREATE TABLE IF NOT EXISTS knowledge_items (
                item_id VARCHAR(50) PRIMARY KEY,
                type VARCHAR(50),
                file_name VARCHAR(200),
                description TEXT,
                status VARCHAR(20) DEFAULT 'processing',
                progress DOUBLE DEFAULT 0,
                message TEXT,
                created_at DATETIME DEFAULT NOW(),
                updated_at DATETIME DEFAULT NOW() ON UPDATE NOW()
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Audit logs
        execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id VARCHAR(50) PRIMARY KEY,
                user_id VARCHAR(100),
                agent_type VARCHAR(50),
                action VARCHAR(50),
                resource_id VARCHAR(50),
                detail TEXT,
                created_at DATETIME DEFAULT NOW()
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Users (P2: migrate from MOCK_USERS to DB-backed)
        execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(50) PRIMARY KEY,
                username VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(256) NOT NULL,
                name VARCHAR(100),
                role VARCHAR(50) DEFAULT 'cra',
                email VARCHAR(200),
                phone VARCHAR(50),
                is_active TINYINT DEFAULT 1,
                created_at DATETIME DEFAULT NOW(),
                updated_at DATETIME DEFAULT NOW() ON UPDATE NOW()
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        # Seed default users (idempotent)
        import hashlib
        _default_users = [
            ('USR-001', 'pv_user',    hashlib.sha256(b'pv123456').hexdigest(),   '张医生', 'pv_specialist'),
            ('USR-002', 'cra_user',   hashlib.sha256(b'cra123456').hexdigest(),  '李监查', 'cra'),
            ('USR-003', 'admin_user', hashlib.sha256(b'admin123456').hexdigest(), '管理员', 'admin'),
        ]
        for uid, uname, phash, name, role in _default_users:
            if _engine == "mysql":
                cursor.execute(
                    "INSERT IGNORE INTO users (user_id, username, password_hash, name, role) VALUES (%s, %s, %s, %s, %s)",
                    (uid, uname, phash, name, role))
            else:
                cursor.execute(
                    "INSERT OR IGNORE INTO users (user_id, username, password_hash, name, role) VALUES (?, ?, ?, ?, ?)",
                    (uid, uname, phash, name, role))

        # Notifications (P2: in-app notification system)
        execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id VARCHAR(50) PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                title VARCHAR(200) NOT NULL,
                message TEXT,
                notification_type VARCHAR(50) DEFAULT 'info',
                resource_type VARCHAR(50),
                resource_id VARCHAR(50),
                is_read TINYINT DEFAULT 0,
                created_at DATETIME DEFAULT NOW()
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Migration: add columns that may be missing from older databases
        _migrations = [
            ("ae_results", "patient_gender", "VARCHAR(10)"),
            ("ae_results", "patient_dob", "VARCHAR(50)"),
            ("sae_reports", "deadline", "VARCHAR(50)"),
            # P2: audit log HMAC chain columns
            ("audit_logs", "prev_log_id", "VARCHAR(50)"),
            ("audit_logs", "prev_hmac", "VARCHAR(128)"),
            ("audit_logs", "hmac", "VARCHAR(128)"),
        ]
        for table, col, col_type in _migrations:
            try:
                if _engine == "mysql":
                    execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
                else:
                    execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")
            except Exception:
                pass  # Column already exists or unsupported

        # Insert default deviation rules (idempotent)
        rules = [
            ('PD-001', '访视窗超出计划天数±3天', 'ABS(DATEDIFF(actual_visit_date, scheduled_visit_date)) > 3', 'major', 'alert_cra'),
            ('PD-002', '访视完全未做', 'actual_visit_date IS NULL AND scheduled_visit_date < CURRENT_DATE', 'major', 'alert_cra'),
            ('PD-003', '用药依从性不足', 'actual_dose < expected_dose * 0.8', 'major', 'alert_cra'),
            ('PD-004', '禁止用药使用', 'prohibited_drug IN (concomitant_drugs)', 'major', 'alert_cra'),
            ('PD-005', '计划安全性检查未完成', 'missing_tests NOT EMPTY', 'major', 'alert_cra'),
            ('PD-006', '入组标准不符合', 'inclusion_criteria_met = FALSE', 'major', 'alert_cra'),
            ('PD-007', '排除标准违反', 'exclusion_criteria_met = TRUE', 'major', 'alert_cra'),
        ]
        for rule in rules:
            if _engine == "mysql":
                cursor.execute("INSERT IGNORE INTO deviation_rules (rule_id, description, check_logic, severity, action) VALUES (%s, %s, %s, %s, %s)", rule)
            else:
                cursor.execute("INSERT OR IGNORE INTO deviation_rules (rule_id, description, check_logic, severity, action) VALUES (?, ?, ?, ?, ?)", rule)

        conn.commit()
        print(f"数据库初始化完成 (引擎: {_engine})")
    finally:
        conn.close()