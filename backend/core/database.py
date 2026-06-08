"""Database connection using SQLite"""
import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ae_sentinel.db")

def ensure_db_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_connection():
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def dict_from_row(row):
    if row is None:
        return None
    return dict(row)

def execute_query(conn, sql, params=None):
    cursor = conn.cursor()
    cursor.execute(sql, params or ())
    return [dict_from_row(r) for r in cursor.fetchall()]

def execute_insert(conn, sql, params=None):
    cursor = conn.cursor()
    cursor.execute(sql, params or ())
    return cursor.lastrowid

def init_db():
    """Initialize all tables"""
    ensure_db_dir()
    conn = get_connection()
    cursor = conn.cursor()

    # AE results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ae_results (
            ae_id TEXT PRIMARY KEY, patient_id TEXT NOT NULL, visit_id TEXT,
            visit_date TEXT, ae_text TEXT NOT NULL, drug_name TEXT,
            onset_date TEXT, end_date TEXT, reporter TEXT,
            meddra_codes TEXT, severity TEXT, sae_flag INTEGER DEFAULT 0,
            sae_criteria TEXT, expected_flag INTEGER DEFAULT 0,
            causality_tentative TEXT, citations TEXT, processing_time_ms INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # SAE reports
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sae_reports (
            report_id TEXT PRIMARY KEY, ae_id TEXT NOT NULL, cioms_fields TEXT,
            causality_assessment TEXT, similar_drug_safety TEXT,
            report_status TEXT DEFAULT 'draft', deadline TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (ae_id) REFERENCES ae_results(ae_id)
        )
    """)

    # Deviation rules
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deviation_rules (
            rule_id TEXT PRIMARY KEY, description TEXT, check_logic TEXT,
            severity TEXT, action TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Deviations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deviations (
            deviation_id TEXT PRIMARY KEY, patient_id TEXT NOT NULL, visit_id TEXT,
            rule_id TEXT, deviation_type TEXT, severity TEXT, description TEXT,
            action TEXT, status TEXT DEFAULT 'open', resolution TEXT,
            resolved_by TEXT, action_taken TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Signals
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            signal_id TEXT PRIMARY KEY, drug_name TEXT, signal_name TEXT,
            signal_status TEXT DEFAULT 'new', event_count INTEGER DEFAULT 0,
            incidence_rate TEXT, background_rate TEXT, statistical_test TEXT,
            related_literature TEXT, recommended_action TEXT, analysis_period TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Knowledge items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_items (
            item_id TEXT PRIMARY KEY, type TEXT, file_name TEXT, description TEXT,
            status TEXT DEFAULT 'processing', progress REAL DEFAULT 0, message TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Audit logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            log_id TEXT PRIMARY KEY, user_id TEXT, agent_type TEXT,
            action TEXT, resource_id TEXT, detail TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Insert default deviation rules
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
        cursor.execute("INSERT OR IGNORE INTO deviation_rules (rule_id, description, check_logic, severity, action) VALUES (?, ?, ?, ?, ?)", rule)

    conn.commit()
    conn.close()
    print("SQLite数据库初始化完成")
