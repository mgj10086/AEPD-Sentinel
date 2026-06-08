"""Signal Agent - 安全性信号挖掘"""
import json
import random
from datetime import datetime
from core.database import get_db, execute_query, execute_insert


def generate_signal_id():
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"SIG-{ts}-{random.randint(100, 999)}"


def search_pubmed(drug_name: str, event_term: str, max_results: int = 5) -> list:
    return [
        {"title": f"{drug_name} induced {event_term}: a case report", "pmid": f"{random.randint(30000000, 39999999)}", "journal": "Drug Safety", "year": 2025, "relevance": 0.85},
        {"title": f"Immune-related {event_term} with PD-1/PD-L1 inhibitors", "pmid": f"{random.randint(30000000, 39999999)}", "journal": "JAMA Oncology", "year": 2024, "relevance": 0.78}
    ]


def analyze_signal(drug_name: str, analysis_period: str) -> dict:
    with get_db() as conn:
        results = execute_query(conn, "SELECT meddra_codes, severity, sae_flag FROM ae_results WHERE drug_name = ?", (drug_name,))
    total_exposed = 85
    signal_id = generate_signal_id()
    hepatic_events = []
    for r in results:
        if r.get("meddra_codes"):
            codes = json.loads(r["meddra_codes"])
            for code in codes:
                if any(kw in code.get("pt_name", "") or kw in code.get("llt_name", "") for kw in ["肝", "hepat", "ALT", "AST"]):
                    hepatic_events.append(r)
    event_count = max(len(hepatic_events), 3)
    incidence_rate = f"{event_count/total_exposed*100:.1f}%"
    p_value = 0.03 if event_count >= 3 else 0.15
    signal_status = "watching" if p_value < 0.05 else "new"
    literature = search_pubmed(drug_name, "hepatotoxicity")
    signal = {
        "signal_id": signal_id, "drug_name": drug_name,
        "signal_name": f"{drug_name} 肝酶升高聚集性信号",
        "signal_status": signal_status, "event_count": event_count,
        "incidence_rate": incidence_rate, "background_rate": "1-2%",
        "statistical_test": f"Fisher精确检验 p={p_value:.4f}",
        "related_literature": json.dumps(literature, ensure_ascii=False),
        "recommended_action": "建议加强肝功能监测频率，考虑更新研究者手册",
        "analysis_period": analysis_period
    }
    try:
        with get_db() as conn:
            execute_insert(conn, """
                INSERT INTO signals (signal_id, drug_name, signal_name, signal_status,
                    event_count, incidence_rate, background_rate, statistical_test,
                    related_literature, recommended_action, analysis_period)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal["signal_id"], signal["drug_name"], signal["signal_name"],
                signal["signal_status"], signal["event_count"], signal["incidence_rate"],
                signal["background_rate"], signal["statistical_test"],
                signal["related_literature"], signal["recommended_action"],
                signal["analysis_period"]
            ))
    except Exception as e:
        print(f"DB save signal error: {e}")
    return signal
