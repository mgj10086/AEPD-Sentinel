"""AE Agent - 不良事件编码与严重性初筛"""
import json
import time
import random
from datetime import datetime
from typing import List, Dict, Any
from backend.core.database import get_db, execute_query, execute_insert
from backend.core.config import EXPECTED_AES, TRIAL_DRUG
from backend.agents.deviation import process_patient_visit

MEDDRA_SYNONYMS = {
    # ===== 感染及侵染类疾病 =====
    "肺炎": {"llt": "肺炎", "llt_code": "10035664", "pt": "肺炎", "pt_code": "10035664", "soc": "感染及侵染类疾病", "soc_code": "10021871"},
    "肺部感染": {"llt": "肺部感染", "llt_code": "10035670", "pt": "肺炎", "pt_code": "10035664", "soc": "感染及侵染类疾病", "soc_code": "10021871"},
    "上呼吸道感染": {"llt": "上呼吸道感染", "llt_code": "10046300", "pt": "上呼吸道感染", "pt_code": "10046300", "soc": "感染及侵染类疾病", "soc_code": "10021871"},
    "感冒": {"llt": "上呼吸道感染", "llt_code": "10046300", "pt": "上呼吸道感染", "pt_code": "10046300", "soc": "感染及侵染类疾病", "soc_code": "10021871"},
    "尿路感染": {"llt": "尿路感染", "llt_code": "10046571", "pt": "尿路感染", "pt_code": "10046571", "soc": "感染及侵染类疾病", "soc_code": "10021871"},
    "败血症": {"llt": "败血症", "llt_code": "10040053", "pt": "败血症", "pt_code": "10040053", "soc": "感染及侵染类疾病", "soc_code": "10021871"},
    "带状疱疹": {"llt": "带状疱疹", "llt_code": "10019974", "pt": "带状疱疹", "pt_code": "10019974", "soc": "感染及侵染类疾病", "soc_code": "10021871"},
    # ===== 血液及淋巴系统疾病 =====
    "贫血": {"llt": "贫血", "llt_code": "10002034", "pt": "贫血", "pt_code": "10002034", "soc": "血液及淋巴系统疾病", "soc_code": "10005329"},
    "血小板减少": {"llt": "血小板减少", "llt_code": "10043556", "pt": "血小板减少症", "pt_code": "10043556", "soc": "血液及淋巴系统疾病", "soc_code": "10005329"},
    "中性粒细胞减少": {"llt": "中性粒细胞减少", "llt_code": "10029354", "pt": "中性粒细胞减少症", "pt_code": "10029354", "soc": "血液及淋巴系统疾病", "soc_code": "10005329"},
    "白细胞减少": {"llt": "白细胞减少", "llt_code": "10047965", "pt": "白细胞减少症", "pt_code": "10047965", "soc": "血液及淋巴系统疾病", "soc_code": "10005329"},
    "发热性中性粒细胞减少": {"llt": "发热性中性粒细胞减少", "llt_code": "10016288", "pt": "发热性中性粒细胞减少症", "pt_code": "10016288", "soc": "血液及淋巴系统疾病", "soc_code": "10005329"},
    "全血细胞减少": {"llt": "全血细胞减少", "llt_code": "10033661", "pt": "全血细胞减少症", "pt_code": "10033661", "soc": "血液及淋巴系统疾病", "soc_code": "10005329"},
    "淋巴细胞减少": {"llt": "淋巴细胞减少", "llt_code": "10025239", "pt": "淋巴细胞减少症", "pt_code": "10025239", "soc": "血液及淋巴系统疾病", "soc_code": "10005329"},
    # ===== 免疫系统疾病 =====
    "过敏反应": {"llt": "过敏反应", "llt_code": "10001718", "pt": "超敏反应", "pt_code": "10023478", "soc": "免疫系统疾病", "soc_code": "10021428"},
    "过敏性休克": {"llt": "过敏性休克", "llt_code": "10002198", "pt": "过敏性休克", "pt_code": "10002198", "soc": "免疫系统疾病", "soc_code": "10021428"},
    "细胞因子释放综合征": {"llt": "CRS", "llt_code": "10062591", "pt": "细胞因子释放综合征", "pt_code": "10062591", "soc": "免疫系统疾病", "soc_code": "10021428"},
    "免疫相关不良反应": {"llt": "免疫相关AE", "llt_code": "10079393", "pt": "免疫介导不良反应", "pt_code": "10079393", "soc": "免疫系统疾病", "soc_code": "10021428"},
    # ===== 内分泌系统疾病 =====
    "甲减": {"llt": "甲状腺功能减退", "llt_code": "10020995", "pt": "甲状腺功能减退症", "pt_code": "10020995", "soc": "内分泌系统疾病", "soc_code": "10014698"},
    "甲状腺功能减退": {"llt": "甲状腺功能减退", "llt_code": "10020995", "pt": "甲状腺功能减退症", "pt_code": "10020995", "soc": "内分泌系统疾病", "soc_code": "10014698"},
    "甲亢": {"llt": "甲状腺功能亢进", "llt_code": "10020700", "pt": "甲状腺功能亢进症", "pt_code": "10020700", "soc": "内分泌系统疾病", "soc_code": "10014698"},
    "肾上腺功能不全": {"llt": "肾上腺功能不全", "llt_code": "10001364", "pt": "肾上腺功能不全", "pt_code": "10001364", "soc": "内分泌系统疾病", "soc_code": "10014698"},
    "高血糖": {"llt": "高血糖", "llt_code": "10020642", "pt": "高血糖症", "pt_code": "10020642", "soc": "代谢及营养类疾病", "soc_code": "10027433"},
    # ===== 代谢及营养类疾病 =====
    "食欲下降": {"llt": "食欲减退", "llt_code": "10003111", "pt": "食欲减退", "pt_code": "10003111", "soc": "代谢及营养类疾病", "soc_code": "10027433"},
    "没胃口": {"llt": "食欲减退", "llt_code": "10003111", "pt": "食欲减退", "pt_code": "10003111", "soc": "代谢及营养类疾病", "soc_code": "10027433"},
    "吃不下饭": {"llt": "食欲减退", "llt_code": "10003111", "pt": "食欲减退", "pt_code": "10003111", "soc": "代谢及营养类疾病", "soc_code": "10027433"},
    "低钾血症": {"llt": "低钾血症", "llt_code": "10021030", "pt": "低钾血症", "pt_code": "10021030", "soc": "代谢及营养类疾病", "soc_code": "10027433"},
    "低钠血症": {"llt": "低钠血症", "llt_code": "10021044", "pt": "低钠血症", "pt_code": "10021044", "soc": "代谢及营养类疾病", "soc_code": "10027433"},
    "低白蛋白血症": {"llt": "低白蛋白血症", "llt_code": "10020967", "pt": "低白蛋白血症", "pt_code": "10020967", "soc": "代谢及营养类疾病", "soc_code": "10027433"},
    "体重下降": {"llt": "体重下降", "llt_code": "10047876", "pt": "体重下降", "pt_code": "10047876", "soc": "代谢及营养类疾病", "soc_code": "10027433"},
    "消瘦": {"llt": "体重下降", "llt_code": "10047876", "pt": "体重下降", "pt_code": "10047876", "soc": "代谢及营养类疾病", "soc_code": "10027433"},
    # ===== 精神疾病 =====
    "失眠": {"llt": "失眠", "llt_code": "10022438", "pt": "失眠", "pt_code": "10022438", "soc": "精神疾病", "soc_code": "10037175"},
    "焦虑": {"llt": "焦虑", "llt_code": "10002855", "pt": "焦虑", "pt_code": "10002855", "soc": "精神疾病", "soc_code": "10037175"},
    "抑郁": {"llt": "抑郁", "llt_code": "10012394", "pt": "抑郁症", "pt_code": "10012378", "soc": "精神疾病", "soc_code": "10037175"},
    "意识模糊": {"llt": "意识模糊", "llt_code": "10010406", "pt": "意识模糊状态", "pt_code": "10010406", "soc": "精神疾病", "soc_code": "10037175"},
    # ===== 神经系统疾病 =====
    "头痛": {"llt": "头痛", "llt_code": "10019211", "pt": "头痛", "pt_code": "10019211", "soc": "神经系统疾病", "soc_code": "10029205"},
    "头疼": {"llt": "头痛", "llt_code": "10019211", "pt": "头痛", "pt_code": "10019211", "soc": "神经系统疾病", "soc_code": "10029205"},
    "头晕": {"llt": "头晕", "llt_code": "10013573", "pt": "头晕", "pt_code": "10013573", "soc": "神经系统疾病", "soc_code": "10029205"},
    "眩晕": {"llt": "眩晕", "llt_code": "10047339", "pt": "眩晕", "pt_code": "10047339", "soc": "神经系统疾病", "soc_code": "10029205"},
    "周围神经病变": {"llt": "周围神经病", "llt_code": "10034621", "pt": "周围神经病", "pt_code": "10034621", "soc": "神经系统疾病", "soc_code": "10029205"},
    "手脚麻木": {"llt": "感觉异常", "llt_code": "10033767", "pt": "感觉异常", "pt_code": "10033767", "soc": "神经系统疾病", "soc_code": "10029205"},
    "味觉障碍": {"llt": "味觉障碍", "llt_code": "10013982", "pt": "味觉障碍", "pt_code": "10013982", "soc": "神经系统疾病", "soc_code": "10029205"},
    "癫痫": {"llt": "癫痫", "llt_code": "10015038", "pt": "癫痫发作", "pt_code": "10039906", "soc": "神经系统疾病", "soc_code": "10029205"},
    # ===== 眼器官疾病 =====
    "视力模糊": {"llt": "视力模糊", "llt_code": "10047513", "pt": "视物模糊", "pt_code": "10047513", "soc": "眼器官疾病", "soc_code": "10015919"},
    "干眼": {"llt": "干眼", "llt_code": "10013774", "pt": "干眼症", "pt_code": "10013774", "soc": "眼器官疾病", "soc_code": "10015919"},
    "结膜炎": {"llt": "结膜炎", "llt_code": "10010743", "pt": "结膜炎", "pt_code": "10010743", "soc": "眼器官疾病", "soc_code": "10015919"},
    # ===== 心脏器官疾病 =====
    "心悸": {"llt": "心悸", "llt_code": "10033550", "pt": "心悸", "pt_code": "10033550", "soc": "心脏器官疾病", "soc_code": "10007541"},
    "心动过速": {"llt": "心动过速", "llt_code": "10042986", "pt": "心动过速", "pt_code": "10042986", "soc": "心脏器官疾病", "soc_code": "10007541"},
    "心肌炎": {"llt": "心肌炎", "llt_code": "10028695", "pt": "心肌炎", "pt_code": "10028695", "soc": "心脏器官疾病", "soc_code": "10007541"},
    "心房颤动": {"llt": "心房颤动", "llt_code": "10003646", "pt": "心房颤动", "pt_code": "10003646", "soc": "心脏器官疾病", "soc_code": "10007541"},
    "QT间期延长": {"llt": "QT间期延长", "llt_code": "10014387", "pt": "心电图QT间期延长", "pt_code": "10014387", "soc": "心脏器官疾病", "soc_code": "10007541"},
    # ===== 血管疾病 =====
    "高血压": {"llt": "高血压", "llt_code": "10020773", "pt": "高血压", "pt_code": "10020772", "soc": "血管疾病", "soc_code": "10047065"},
    "低血压": {"llt": "低血压", "llt_code": "10021097", "pt": "低血压", "pt_code": "10021097", "soc": "血管疾病", "soc_code": "10047065"},
    "潮热": {"llt": "潮热", "llt_code": "10020534", "pt": "潮热", "pt_code": "10020534", "soc": "血管疾病", "soc_code": "10047065"},
    "血栓栓塞": {"llt": "血栓栓塞", "llt_code": "10043606", "pt": "血栓栓塞事件", "pt_code": "10043606", "soc": "血管疾病", "soc_code": "10047065"},
    # ===== 呼吸系统疾病 =====
    "咳嗽": {"llt": "咳嗽", "llt_code": "10011224", "pt": "咳嗽", "pt_code": "10011224", "soc": "呼吸系统、胸及纵隔疾病", "soc_code": "10038738"},
    "气促": {"llt": "呼吸困难", "llt_code": "10013968", "pt": "呼吸困难", "pt_code": "10013968", "soc": "呼吸系统、胸及纵隔疾病", "soc_code": "10038738"},
    "呼吸困难": {"llt": "呼吸困难", "llt_code": "10013968", "pt": "呼吸困难", "pt_code": "10013968", "soc": "呼吸系统、胸及纵隔疾病", "soc_code": "10038738"},
    "间质性肺病": {"llt": "间质性肺病", "llt_code": "10063871", "pt": "间质性肺病", "pt_code": "10063871", "soc": "呼吸系统、胸及纵隔疾病", "soc_code": "10038738"},
    "免疫相关肺炎": {"llt": "免疫相关性肺炎", "llt_code": "10079400", "pt": "免疫相关性肺炎", "pt_code": "10079400", "soc": "呼吸系统、胸及纵隔疾病", "soc_code": "10038738"},
    "呼吸衰竭": {"llt": "呼吸衰竭", "llt_code": "10038781", "pt": "呼吸衰竭", "pt_code": "10038781", "soc": "呼吸系统、胸及纵隔疾病", "soc_code": "10038738"},
    "胸腔积液": {"llt": "胸腔积液", "llt_code": "10035659", "pt": "胸腔积液", "pt_code": "10035659", "soc": "呼吸系统、胸及纵隔疾病", "soc_code": "10038738"},
    "咯血": {"llt": "咯血", "llt_code": "10019183", "pt": "咯血", "pt_code": "10019183", "soc": "呼吸系统、胸及纵隔疾病", "soc_code": "10038738"},
    # ===== 胃肠系统疾病 =====
    "恶心": {"llt": "恶心", "llt_code": "10028813", "pt": "恶心", "pt_code": "10028813", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "反胃": {"llt": "恶心", "llt_code": "10028813", "pt": "恶心", "pt_code": "10028813", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "想吐": {"llt": "恶心", "llt_code": "10028813", "pt": "恶心", "pt_code": "10028813", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "呕吐": {"llt": "呕吐", "llt_code": "10047700", "pt": "呕吐", "pt_code": "10047700", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "腹泻": {"llt": "腹泻", "llt_code": "10012735", "pt": "腹泻", "pt_code": "10012735", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "拉肚子": {"llt": "腹泻", "llt_code": "10012735", "pt": "腹泻", "pt_code": "10012735", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "便秘": {"llt": "便秘", "llt_code": "10010774", "pt": "便秘", "pt_code": "10010774", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "腹痛": {"llt": "腹痛", "llt_code": "10000078", "pt": "腹痛", "pt_code": "10000078", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "口腔炎": {"llt": "口腔炎", "llt_code": "10042118", "pt": "口腔黏膜炎", "pt_code": "10028130", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "口腔溃疡": {"llt": "口腔溃疡", "llt_code": "10028033", "pt": "口腔黏膜炎", "pt_code": "10028130", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "消化不良": {"llt": "消化不良", "llt_code": "10013937", "pt": "消化不良", "pt_code": "10013937", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "结肠炎": {"llt": "结肠炎", "llt_code": "10009953", "pt": "结肠炎", "pt_code": "10009953", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    # ===== 肝胆系统疾病 =====
    "肝炎": {"llt": "肝炎", "llt_code": "10019851", "pt": "肝炎", "pt_code": "10019851", "soc": "肝胆系统疾病", "soc_code": "10019805"},
    "免疫相关肝炎": {"llt": "免疫相关性肝炎", "llt_code": "10079394", "pt": "免疫相关性肝炎", "pt_code": "10079394", "soc": "肝胆系统疾病", "soc_code": "10019805"},
    "肝功能检查异常": {"llt": "肝功能异常", "llt_code": "10020858", "pt": "肝功能异常", "pt_code": "10020858", "soc": "肝胆系统疾病", "soc_code": "10019805"},
    "转氨酶升高": {"llt": "转氨酶升高", "llt_code": "10043964", "pt": "转氨酶升高", "pt_code": "10043964", "soc": "肝胆系统疾病", "soc_code": "10019805"},
    "ALT升高": {"llt": "ALT升高", "llt_code": "10001538", "pt": "丙氨酸氨基转移酶升高", "pt_code": "10001538", "soc": "肝胆系统疾病", "soc_code": "10019805"},
    "AST升高": {"llt": "AST升高", "llt_code": "10003400", "pt": "天冬氨酸氨基转移酶升高", "pt_code": "10003400", "soc": "肝胆系统疾病", "soc_code": "10019805"},
    "黄疸": {"llt": "黄疸", "llt_code": "10023129", "pt": "黄疸", "pt_code": "10023129", "soc": "肝胆系统疾病", "soc_code": "10019805"},
    "胆红素升高": {"llt": "胆红素升高", "llt_code": "10004917", "pt": "血胆红素升高", "pt_code": "10004917", "soc": "肝胆系统疾病", "soc_code": "10019805"},
    # ===== 皮肤及皮下组织类疾病 =====
    "皮疹": {"llt": "皮疹", "llt_code": "10037844", "pt": "皮疹", "pt_code": "10037844", "soc": "皮肤及皮下组织类疾病", "soc_code": "10040785"},
    "斑丘疹": {"llt": "斑丘疹", "llt_code": "10025638", "pt": "斑丘疹", "pt_code": "10025638", "soc": "皮肤及皮下组织类疾病", "soc_code": "10040785"},
    "瘙痒": {"llt": "瘙痒", "llt_code": "10037481", "pt": "瘙痒", "pt_code": "10037481", "soc": "皮肤及皮下组织类疾病", "soc_code": "10040785"},
    "皮肤干燥": {"llt": "皮肤干燥", "llt_code": "10013758", "pt": "皮肤干燥", "pt_code": "10013758", "soc": "皮肤及皮下组织类疾病", "soc_code": "10040785"},
    "脱发": {"llt": "脱发", "llt_code": "10001760", "pt": "脱发", "pt_code": "10001760", "soc": "皮肤及皮下组织类疾病", "soc_code": "10040785"},
    "手足综合征": {"llt": "手足综合征", "llt_code": "10061298", "pt": "掌跖红肿综合征", "pt_code": "10033554", "soc": "皮肤及皮下组织类疾病", "soc_code": "10040785"},
    "Stevens-Johnson综合征": {"llt": "SJS", "llt_code": "10042043", "pt": "Stevens-Johnson综合征", "pt_code": "10042043", "soc": "皮肤及皮下组织类疾病", "soc_code": "10040785"},
    # ===== 肌肉骨骼及结缔组织疾病 =====
    "关节痛": {"llt": "关节痛", "llt_code": "10003243", "pt": "关节痛", "pt_code": "10003243", "soc": "肌肉骨骼及结缔组织疾病", "soc_code": "10028395"},
    "肌痛": {"llt": "肌痛", "llt_code": "10028411", "pt": "肌痛", "pt_code": "10028411", "soc": "肌肉骨骼及结缔组织疾病", "soc_code": "10028395"},
    "肌肉酸痛": {"llt": "肌痛", "llt_code": "10028411", "pt": "肌痛", "pt_code": "10028411", "soc": "肌肉骨骼及结缔组织疾病", "soc_code": "10028395"},
    "背痛": {"llt": "背痛", "llt_code": "10003988", "pt": "背痛", "pt_code": "10003988", "soc": "肌肉骨骼及结缔组织疾病", "soc_code": "10028395"},
    "关节炎": {"llt": "关节炎", "llt_code": "10003267", "pt": "关节炎", "pt_code": "10003267", "soc": "肌肉骨骼及结缔组织疾病", "soc_code": "10028395"},
    # ===== 肾脏及泌尿系统疾病 =====
    "蛋白尿": {"llt": "蛋白尿", "llt_code": "10037044", "pt": "蛋白尿", "pt_code": "10037044", "soc": "肾脏及泌尿系统疾病", "soc_code": "10038359"},
    "血尿": {"llt": "血尿", "llt_code": "10018935", "pt": "血尿", "pt_code": "10018935", "soc": "肾脏及泌尿系统疾病", "soc_code": "10038359"},
    "急性肾损伤": {"llt": "急性肾损伤", "llt_code": "10069352", "pt": "急性肾损伤", "pt_code": "10069352", "soc": "肾脏及泌尿系统疾病", "soc_code": "10038359"},
    "肌酐升高": {"llt": "肌酐升高", "llt_code": "10011371", "pt": "血肌酐升高", "pt_code": "10011371", "soc": "肾脏及泌尿系统疾病", "soc_code": "10038359"},
    # ===== 全身性疾病及给药部位各种反应 =====
    "发热": {"llt": "发热", "llt_code": "10016558", "pt": "发热", "pt_code": "10016558", "soc": "全身性疾病及给药部位各种反应", "soc_code": "10018065"},
    "疲乏": {"llt": "疲乏", "llt_code": "10046937", "pt": "疲乏", "pt_code": "10046937", "soc": "全身性疾病及给药部位各种反应", "soc_code": "10018065"},
    "乏力": {"llt": "乏力", "llt_code": "10003928", "pt": "乏力", "pt_code": "10003928", "soc": "全身性疾病及给药部位各种反应", "soc_code": "10018065"},
    "输液反应": {"llt": "输液反应", "llt_code": "10043657", "pt": "输液反应", "pt_code": "10043657", "soc": "全身性疾病及给药部位各种反应", "soc_code": "10018065"},
    "注射部位反应": {"llt": "注射部位反应", "llt_code": "10022097", "pt": "注射部位反应", "pt_code": "10022097", "soc": "全身性疾病及给药部位各种反应", "soc_code": "10018065"},
    "疼痛": {"llt": "疼痛", "llt_code": "10033371", "pt": "疼痛", "pt_code": "10033371", "soc": "全身性疾病及给药部位各种反应", "soc_code": "10018065"},
    "寒战": {"llt": "寒战", "llt_code": "10009207", "pt": "寒战", "pt_code": "10009207", "soc": "全身性疾病及给药部位各种反应", "soc_code": "10018065"},
    "水肿": {"llt": "水肿", "llt_code": "10014438", "pt": "水肿", "pt_code": "10014438", "soc": "全身性疾病及给药部位各种反应", "soc_code": "10018065"},
    # ===== 各类检查 =====
    "体重增加": {"llt": "体重增加", "llt_code": "10047882", "pt": "体重增加", "pt_code": "10047882", "soc": "各类检查", "soc_code": "10022891"},
    "血肌酸磷酸激酶升高": {"llt": "CK升高", "llt_code": "10001124", "pt": "血肌酸磷酸激酶升高", "pt_code": "10001124", "soc": "各类检查", "soc_code": "10022891"},
    "淀粉酶升高": {"llt": "淀粉酶升高", "llt_code": "10002002", "pt": "血淀粉酶升高", "pt_code": "10002002", "soc": "各类检查", "soc_code": "10022891"},
    "脂肪酶升高": {"llt": "脂肪酶升高", "llt_code": "10024501", "pt": "脂肪酶升高", "pt_code": "10024501", "soc": "各类检查", "soc_code": "10022891"},
    # ===== 各类损伤、中毒及操作并发症 =====
    "输液外渗": {"llt": "输液外渗", "llt_code": "10022108", "pt": "输液部位外渗", "pt_code": "10022108", "soc": "各类损伤、中毒及操作并发症", "soc_code": "10022117"},
    "跌倒": {"llt": "跌倒", "llt_code": "10016173", "pt": "跌倒", "pt_code": "10016173", "soc": "各类损伤、中毒及操作并发症", "soc_code": "10022117"},
}

SEVERITY_KEYWORDS = {
    "severe": ["住院", "收治", "危及生命", "死亡", "抢救", "严重", "重度", "5x", "5倍", "ULN", "ALT", "AST", "≥5"],
    "moderate": ["影响睡眠", "影响日常", "中度", "明显", "加重", "持续", "外用"],
    "mild": ["轻度", "轻微", "自行缓解", "未予特殊", "不适"]
}

SAE_CRITERIA_KEYWORDS = {
    "死亡": ["死亡", "抢救无效", "去世"],
    "危及生命": ["危及生命", "呼吸衰竭", "休克"],
    "导致住院": ["住院", "收治入院", "收治", "入院"],
    "残疾": ["残疾", "功能丧失"],
    "先天性畸形": ["先天性", "出生缺陷", "畸形"],
    "重要医学事件": ["ALT", "AST", "肝酶", "≥5", "5倍", "5x", "ULN", "肝炎", "免疫相关肝炎"]
}


def generate_ae_id():
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"AE-{ts}-{random.randint(100, 999)}"


def match_meddra(text: str) -> List[Dict[str, Any]]:
    """
    MedDRA 编码匹配。使用排序关键词匹配（长词优先），避免子串误匹配。
    匹配策略：按关键词长度降序排列后依次匹配，短词命中已匹配长词覆盖区域时跳过。
    """
    results = []
    matched_spans = set()  # 已匹配的文本区间

    # 按关键词长度降序排列（长词优先匹配，如"免疫相关肝炎"优先于"肝炎"）
    sorted_keywords = sorted(MEDDRA_SYNONYMS.keys(), key=len, reverse=True)

    for keyword in sorted_keywords:
        mapping = MEDDRA_SYNONYMS[keyword]
        start = 0
        while True:
            pos = text.find(keyword, start)
            if pos == -1:
                break
            # 检查是否被已匹配的长词覆盖
            overlap = any(ms <= pos < me or ms <= pos + len(keyword) <= me
                          for ms, me in matched_spans)
            if not overlap:
                matched_spans.add((pos, pos + len(keyword)))
                confidence = 0.95 if keyword == mapping["llt"] else 0.88
                results.append({
                    "llt_code": mapping["llt_code"], "llt_name": mapping["llt"],
                    "pt_code": mapping["pt_code"], "pt_name": mapping["pt"],
                    "soc_code": mapping["soc_code"], "soc_name": mapping["soc"],
                    "confidence": confidence
                })
            start = pos + 1

    # 去重(按pt_name)
    seen = set()
    unique = []
    for r in results:
        if r["pt_name"] not in seen:
            seen.add(r["pt_name"])
            unique.append(r)
    return unique


def assess_severity(text: str) -> str:
    if any(kw in text for kw in SAE_CRITERIA_KEYWORDS.get("重要医学事件", [])):
        if "ALT" in text or "AST" in text:
            return "severe"
    if any(kw in text for kw in SAE_CRITERIA_KEYWORDS.get("死亡", [])):
        return "severe"
    if any(kw in text for kw in SAE_CRITERIA_KEYWORDS.get("导致住院", [])):
        return "severe"
    if any(kw in text for kw in SAE_CRITERIA_KEYWORDS.get("危及生命", [])):
        return "severe"
    if any(kw in text for kw in SEVERITY_KEYWORDS["severe"]):
        return "severe"
    if any(kw in text for kw in SEVERITY_KEYWORDS["moderate"]):
        return "moderate"
    if any(kw in text for kw in SEVERITY_KEYWORDS["mild"]):
        return "mild"
    return "mild"


def assess_sae(text: str) -> tuple:
    criteria = []
    for criterion, keywords in SAE_CRITERIA_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            criteria.append(criterion)
    return (len(criteria) > 0, criteria)


def check_expected(pt_name: str) -> bool:
    for expected in EXPECTED_AES:
        if expected in pt_name or pt_name in expected:
            return True
    return False


def assess_causality(text: str, drug_name: str, sae_flag: bool, expected_flag: bool) -> str:
    """
    WHO-UMC 因果关系评估（6级）
    certain > probable > possible > unlikely > conditional/unclassified > unassessable
    """
    # certain: 事件发生在用药后的合理时间范围内，不能用疾病或其他药物解释，
    #          去激发阳性，再激发阳性（如有）
    if "再激发" in text and ("阳性" in text or "复发" in text or "再次" in text):
        return "certain"
    if sae_flag and ("免疫相关" in text or "药物相关" in text or "过敏" in text):
        if "停药后缓解" in text or "停药后好转" in text or "去激发" in text:
            return "certain"
    # probable: 时间关系合理，不能用疾病解释，去激发阳性，无需再激发
    if sae_flag and ("停药后" in text or "恢复" in text or "缓解" in text):
        return "probable"
    if "药物相关" in text or "考虑与" in text:
        return "probable"
    # possible: 时间关系合理，但也可用疾病或其他药物解释
    if "可能" in text or "不排除" in text or "怀疑" in text:
        return "possible"
    # unlikely: 时间关系不太合理，更可能用疾病解释
    if "不太可能" in text or "无关" in text or "排除" in text:
        return "unlikely"
    # conditional/unclassified: 需要更多数据
    if expected_flag or drug_name.lower() in text.lower():
        return "possible"
    # unassessable: 无法评估
    return "unassessable"


def process_ae(req) -> Dict[str, Any]:
    start = time.time()
    codes = match_meddra(req.ae_text)
    if not codes:
        codes = [{
            "llt_code": "99999999", "llt_name": "其他症状",
            "pt_code": "99999999", "pt_name": "其他症状",
            "soc_code": "99999999", "soc_name": "各种检查", "confidence": 0.60
        }]
    severity = assess_severity(req.ae_text)
    sae_flag, sae_criteria = assess_sae(req.ae_text)
    expected_flag = any(check_expected(c["pt_name"]) for c in codes)
    causality = assess_causality(req.ae_text, req.drug_name, sae_flag, expected_flag)
    citations = []
    if expected_flag:
        citations.append(f"IB Section 4.8 - {TRIAL_DRUG}")
    citations.append("MedDRA v26.0")
    processing_time = int((time.time() - start) * 1000)
    ae_id = generate_ae_id()
    try:
        with get_db() as conn:
            execute_insert(conn, """
                INSERT INTO ae_results (ae_id, patient_id, visit_id, visit_date, ae_text, drug_name,
                    onset_date, end_date, reporter, patient_gender, patient_dob,
                    meddra_codes, severity, sae_flag, sae_criteria,
                    expected_flag, causality_tentative, citations, processing_time_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                ae_id, req.patient_id, getattr(req, 'visit_id', None), req.visit_date,
                req.ae_text, req.drug_name, getattr(req, 'onset_date', None),
                getattr(req, 'end_date', None), getattr(req, 'reporter', None),
                getattr(req, 'patient_gender', ''), getattr(req, 'patient_dob', ''),
                json.dumps(codes, ensure_ascii=False), severity, sae_flag,
                json.dumps(sae_criteria, ensure_ascii=False), expected_flag,
                causality, json.dumps(citations, ensure_ascii=False), processing_time
            ))
    except Exception as e:
        print(f"DB save error: {e}")

    # Auto-detect deviations for this patient visit
    try:
        visit_date = getattr(req, 'visit_date', None)
        drug_name = getattr(req, 'drug_name', '')
        patient_id = req.patient_id
        if patient_id and visit_date:
            deviations = process_patient_visit(patient_id, visit_date, drug_name)
            if deviations:
                print(f"Detected {len(deviations)} deviation(s) for patient {patient_id}")
    except Exception as e:
        print(f"Deviation check error: {e}")

    return {
        "ae_id": ae_id, "meddra_codes": codes, "severity": severity,
        "sae_flag": sae_flag, "sae_criteria": sae_criteria,
        "expected_flag": expected_flag, "causality_tentative": causality,
        "citations": citations, "processing_time_ms": processing_time
    }
