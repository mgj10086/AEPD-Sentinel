"""Export Service - SAE report export to Word/PDF/JSON"""
import json
from io import BytesIO
from datetime import datetime
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


def export_to_docx(report: dict) -> BytesIO:
    doc = Document()
    title = doc.add_heading('CIOMS-I 严重不良事件报告', level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"报告编号: {report.get('report_id', '')}")
    doc.add_paragraph(f"研究编号: {report.get('cioms_fields', {}).get('study_number', '')}")
    doc.add_paragraph(f"生成日期: {datetime.now().strftime('%Y-%m-%d')}")
    doc.add_paragraph(f"报告状态: {report.get('report_status', 'draft')}")
    doc.add_paragraph("")
    cioms = report.get('cioms_fields', {})
    sections = [
        ("患者信息", [("患者编号", cioms.get("patient_initials", "")), ("性别", cioms.get("patient_gender", "")), ("出生日期", cioms.get("patient_dob", ""))]),
        ("不良事件信息", [("AE描述", cioms.get("ae_description", "")), ("开始日期", cioms.get("ae_start_date", "")), ("结束日期", cioms.get("ae_end_date", "")), ("是否严重", "是" if cioms.get("ae_serious") else "否"), ("转归", cioms.get("ae_outcome", ""))]),
        ("可疑药物信息", [("药物名称", cioms.get("suspect_drug_name", "")), ("剂量", cioms.get("suspect_drug_dose", "")), ("用药日期", cioms.get("suspect_drug_dates", ""))]),
        ("因果关系评估", [("评估方法", cioms.get("causality_method", "")), ("评估结果", report.get('causality_assessment', '')), ("去激发", cioms.get("dechallenge", "")), ("再激发", cioms.get("rechallenge", ""))]),
        ("报告人信息", [("资质", cioms.get("reporter_qualification", ""))]),
    ]
    for section_title, fields in sections:
        doc.add_heading(section_title, level=2)
        for label, value in fields:
            p = doc.add_paragraph()
            run_label = p.add_run(f"{label}: ")
            run_label.bold = True
            run_label.font.size = Pt(11)
            run_value = p.add_run(str(value))
            run_value.font.size = Pt(11)
    doc.add_heading("事件叙述", level=2)
    doc.add_paragraph(cioms.get("narrative", ""))
    doc.add_heading("同类药物安全性信息", level=2)
    doc.add_paragraph(report.get('similar_drug_safety', ''))
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def export_to_json(report: dict) -> BytesIO:
    buffer = BytesIO()
    json_bytes = json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8')
    buffer.write(json_bytes)
    buffer.seek(0)
    return buffer


def export_to_pdf(report: dict) -> BytesIO:
    doc = Document()
    doc.add_heading('CIOMS-I SAE Report', level=1)
    cioms = report.get('cioms_fields', {})
    for key, value in cioms.items():
        doc.add_paragraph(f"{key}: {value}")
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer