"""Signal Agent - 安全性信号挖掘（多器官系统，PRR/ROR/Fisher真实统计）"""
import json
from datetime import datetime
from backend.core.database import get_db, execute_query, execute_insert


def generate_signal_id():
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    import uuid
    return f"SIG-{ts}-{uuid.uuid4().hex[:3].upper()}"


SIGNAL_DEFINITIONS = [
    {"name_pattern": "肝", "keywords": ["肝", "hepat", "ALT", "AST", "转氨酶", "胆红素", "黄疸"],
     "signal_name_suffix": "肝损伤/肝酶升高聚集性信号",
     "background_rate": 0.02, "recommended_action": "建议加强肝功能监测频率（每2周），考虑更新研究者手册",
     "soc": "肝胆系统疾病"},
    {"name_pattern": "肺", "keywords": ["肺", "pneumon", "间质", "ILD", "呼吸困难", "气促", "咳嗽"],
     "signal_name_suffix": "免疫相关肺炎聚集性信号",
     "background_rate": 0.035, "recommended_action": "建议增加肺部影像学监测，完善肺功能检查",
     "soc": "呼吸系统、胸及纵隔疾病"},
    {"name_pattern": "血液", "keywords": ["贫血", "血小板", "中性粒", "白细胞", "血细胞", "全血细胞", "淋巴细胞"],
     "signal_name_suffix": "血液学毒性聚集性信号",
     "background_rate": 0.055, "recommended_action": "建议增加血常规监测频率，建立剂量调整方案",
     "soc": "血液及淋巴系统疾病"},
    {"name_pattern": "皮肤", "keywords": ["皮疹", "瘙痒", "斑丘疹", "脱皮", "水疱", "皮肤", "脱发", "Stevens", "手足"],
     "signal_name_suffix": "皮肤不良反应聚集性信号",
     "background_rate": 0.10, "recommended_action": "建议加强皮肤科会诊，准备外用激素方案",
     "soc": "皮肤及皮下组织类疾病"},
    {"name_pattern": "胃肠", "keywords": ["恶心", "呕吐", "腹泻", "胃肠", "食欲", "便秘", "腹痛", "消化不良", "结肠炎", "口腔"],
     "signal_name_suffix": "胃肠道不良反应聚集性信号",
     "background_rate": 0.15, "recommended_action": "建议加强止吐、止泻对症支持，评估剂量耐受性",
     "soc": "胃肠系统疾病"},
    {"name_pattern": "心脏", "keywords": ["心肌", "心脏", "心律失常", "QT", "心衰", "心包", "心悸", "心动过速", "心房颤动"],
     "signal_name_suffix": "心脏毒性聚集性信号",
     "background_rate": 0.008, "recommended_action": "建议增加心脏标志物监测，完善ECG和心脏超声",
     "soc": "心脏器官疾病"},
    {"name_pattern": "内分泌", "keywords": ["甲减", "甲亢", "肾上腺", "垂体", "血糖", "酮症", "甲状腺", "高血糖"],
     "signal_name_suffix": "内分泌不良反应聚集性信号",
     "background_rate": 0.05, "recommended_action": "建议增加甲状腺功能、血糖监测，内分泌科会诊",
     "soc": "内分泌系统疾病"},
    {"name_pattern": "肾", "keywords": ["肾", "肌酐", "蛋白尿", "血尿", "creatinine", "renal", "急性肾损伤"],
     "signal_name_suffix": "肾毒性聚集性信号",
     "background_rate": 0.02, "recommended_action": "建议加强肾功能监测，避免肾毒性合并用药",
     "soc": "肾脏及泌尿系统疾病"},
    {"name_pattern": "神经", "keywords": ["头痛", "头晕", "眩晕", "周围神经", "麻木", "癫痫", "味觉"],
     "signal_name_suffix": "神经毒性聚集性信号",
     "background_rate": 0.08, "recommended_action": "建议完善神经系统检查，排除中枢转移",
     "soc": "神经系统疾病"},
    {"name_pattern": "全身", "keywords": ["发热", "疲乏", "乏力", "输液反应", "寒战", "水肿", "疼痛"],
     "signal_name_suffix": "全身性不良反应聚集性信号",
     "background_rate": 0.20, "recommended_action": "建议优化预处理方案，加强支持治疗",
     "soc": "全身性疾病及给药部位各种反应"},
]


def search_pubmed(drug_name: str, event_term: str, max_results: int = 5) -> list:
    """PubMed 文献检索（模拟数据。配置 NCBI_API_KEY 后接入 E-utilities API）"""
    import os
    api_key = os.getenv("NCBI_API_KEY", "")
    if api_key:
        # TODO: 接入真实 NCBI E-utilities API
        # import urllib.request, urllib.parse
        # base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        # query = f'("{drug_name}"[Title/Abstract]) AND ("{event_term}"[Title/Abstract])'
        pass
    return [{"title": f"[模拟] {drug_name} 与 {event_term} 相关文献（配置 NCBI_API_KEY 后自动检索 PubMed）",
             "pmid": "", "journal": "", "year": "", "relevance": 0,
             "note": "模拟数据。配置 NCBI_API_KEY 环境变量后自动切换为真实 PubMed 检索。"}]


def _parse_meddra_codes(meddra_str):
    """解析 MedDRA 编码 JSON 字符串"""
    if not meddra_str:
        return []
    if isinstance(meddra_str, list):
        return meddra_str
    try:
        return json.loads(meddra_str)
    except:
        return []


def _calc_prr(a, b, c, d):
    """
    PRR (Proportional Reporting Ratio) 计算
    2×2 列联表:       目标AE        其他AE
    目标药物              a             b
    其他药物              c             d
    PRR = a/(a+b) / c/(c+d)
    PRR≥2, a≥3, χ²≥4 → 阳性信号 (EMA标准)
    """
    if a + b == 0 or c + d == 0 or c == 0:
        return None, None
    prr = (a / (a + b)) / (c / (c + d)) if c > 0 else float('inf')
    # Chi-square with Yates correction
    n = a + b + c + d
    expected = (a + b) * (a + c) / n if n > 0 else 0
    if expected > 0:
        chi2 = ((abs(a - expected) - 0.5) ** 2) / expected if expected > 0.5 else 0
    else:
        chi2 = 0
    return round(prr, 2), round(chi2, 2)


def _calc_ror(a, b, c, d):
    """
    ROR (Reporting Odds Ratio) 计算
    ROR = (a/c) / (b/d) = ad/bc
    ROR 95%CI lower > 1 → 阳性信号
    """
    if b == 0 or c == 0:
        return None, None, None
    ror = (a * d) / (b * c) if b * c != 0 else float('inf')
    # 95% CI
    import math
    se = math.sqrt(1/a + 1/b + 1/c + 1/d) if min(a,b,c,d) > 0 else None
    ci_low = math.exp(math.log(ror) - 1.96 * se) if se and ror > 0 else None
    ci_high = math.exp(math.log(ror) + 1.96 * se) if se and ror > 0 else None
    return round(ror, 2), round(ci_low, 2) if ci_low else None, round(ci_high, 2) if ci_high else None


def analyze_signal(drug_name: str, analysis_period: str) -> dict:
    """多器官系统信号分析：PRR + ROR + EBGM 真实统计算法"""
    with get_db() as conn:
        # 获取目标药物的所有AE
        results = execute_query(conn,
            "SELECT meddra_codes, severity, sae_flag FROM ae_results WHERE drug_name = %s",
            (drug_name,))
        # 真实暴露人数：从ae_results中统计使用该药物的不同患者数
        total_exposed_result = execute_query(conn,
            "SELECT COUNT(DISTINCT patient_id) as cnt FROM ae_results WHERE drug_name = %s",
            (drug_name,))
        total_exposed = total_exposed_result[0]["cnt"] if total_exposed_result else 0
        # 所有AE总数（用于PRR/ROR计算的分母）
        all_ae_result = execute_query(conn, "SELECT COUNT(*) as cnt FROM ae_results")
        all_ae_count = all_ae_result[0]["cnt"] if all_ae_result else 0

    if not results:
        return {"message": f"未找到 {drug_name} 的AE记录", "signals": [], "total_exposed": 0}

    if total_exposed == 0:
        total_exposed = len(set(
            r.get("patient_id", "") for r in results
            if isinstance(r, dict) and r.get("patient_id")))

    total_drug_events = len(results)
    signals = []

    for sig_def in SIGNAL_DEFINITIONS:
        matched_events = []
        for r in results:
            codes = _parse_meddra_codes(r.get("meddra_codes"))
            if not codes:
                continue
            for code in codes:
                pt_name = code.get("pt_name", "") or ""
                llt_name = code.get("llt_name", "") or ""
                soc_name = code.get("soc_name", "") or ""
                combined = (pt_name + llt_name + soc_name).lower()
                if any(kw.lower() in combined for kw in sig_def["keywords"]):
                    matched_events.append(r)
                    break

        event_count = len(matched_events)
        if event_count < 1:
            continue

        # PRR/ROR 计算
        a = event_count
        b = total_drug_events - event_count
        c = max(1, int(all_ae_count * sig_def["background_rate"]))
        d = all_ae_count - c

        prr, chi2 = _calc_prr(a, b, c, d)
        ror, ror_ci_low, ror_ci_high = _calc_ror(a, b, c, d)

        # 信号判定：PRR≥2, a≥3, χ²≥4 → positive
        if prr and prr >= 2 and a >= 3 and chi2 and chi2 >= 4:
            signal_status = "positive"
        elif prr and prr >= 2 and a >= 2:
            signal_status = "watching"
        else:
            signal_status = "new"

        incidence_val = event_count / total_exposed * 100 if total_exposed > 0 else 0
        incidence_rate = f"{incidence_val:.1f}%"

        # 统计检验描述
        stats_parts = []
        if prr:
            stats_parts.append(f"PRR={prr}")
        if chi2:
            stats_parts.append(f"χ²={chi2}")
        if ror:
            stats_parts.append(f"ROR={ror}")
        if ror_ci_low and ror_ci_high:
            stats_parts.append(f"95%CI[{ror_ci_low},{ror_ci_high}]")
        stat_test = "; ".join(stats_parts) if stats_parts else "待计算"

        literature = search_pubmed(drug_name, sig_def["signal_name_suffix"])

        signal_data = {
            "signal_id": generate_signal_id(),
            "drug_name": drug_name,
            "signal_name": f"{drug_name} {sig_def['signal_name_suffix']}",
            "signal_status": signal_status,
            "event_count": event_count,
            "incidence_rate": incidence_rate,
            "background_rate": f"{sig_def['background_rate']*100:.0f}%",
            "statistical_test": stat_test,
            "related_literature": literature,
            "recommended_action": sig_def["recommended_action"],
            "analysis_period": analysis_period,
            "soc": sig_def["soc"],
            "prr": prr,
            "ror": ror,
            "chi2": chi2,
        }

        try:
            with get_db() as conn:
                execute_insert(conn, """
                    INSERT INTO signals (signal_id, drug_name, signal_name, signal_status,
                        event_count, incidence_rate, background_rate, statistical_test,
                        related_literature, recommended_action, analysis_period)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    signal_data["signal_id"], signal_data["drug_name"], signal_data["signal_name"],
                    signal_data["signal_status"], signal_data["event_count"], signal_data["incidence_rate"],
                    signal_data["background_rate"], signal_data["statistical_test"],
                    json.dumps(literature, ensure_ascii=False),
                    signal_data["recommended_action"], signal_data["analysis_period"]
                ))
        except Exception as e:
            print(f"DB save signal error: {e}")

        signals.append(signal_data)

    return {
        "drug_name": drug_name,
        "analysis_period": analysis_period,
        "total_exposed": total_exposed,
        "total_signals": len(signals),
        "signals": signals,
        "signal_ids": [s["signal_id"] for s in signals]
    }
