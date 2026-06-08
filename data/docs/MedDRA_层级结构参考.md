# MedDRA 术语层级结构参考

## 来源
MedDRA (Medical Dictionary for Regulatory Activities)
官网: https://www.meddra.org
学术/非商业用途可免费获取中文版

## 五级层级结构

```
SOC (System Organ Class) - 系统器官分类（27个）
 └─ HLGT (High Level Group Term) - 高位组术语（~337个）
     └─ HLT (High Level Term) - 高位术语（~1,737个）
         └─ PT (Preferred Term) - 首选术语（~26,000+个）
             └─ LLT (Lowest Level Term) - 低位术语（~85,000+个）
```

## 主要 SOC 分类（27个）

| 序号 | SOC 中文名称 | SOC 英文名称 |
|------|-------------|-------------|
| 1 | 感染及侵染类疾病 | Infections and infestations |
| 2 | 良性、恶性及性质不明的肿瘤 | Neoplasms benign, malignant and unspecified |
| 3 | 血液及淋巴系统疾病 | Blood and lymphatic system disorders |
| 4 | 免疫系统疾病 | Immune system disorders |
| 5 | 内分泌系统疾病 | Endocrine disorders |
| 6 | 代谢及营养类疾病 | Metabolism and nutrition disorders |
| 7 | 精神病类 | Psychiatric disorders |
| 8 | 各类神经系统疾病 | Nervous system disorders |
| 9 | 眼器官疾病 | Eye disorders |
| 10 | 耳及迷路类疾病 | Ear and labyrinth disorders |
| 11 | 心脏器官疾病 | Cardiac disorders |
| 12 | 血管与淋巴管类疾病 | Vascular disorders |
| 13 | 呼吸系统、胸及纵隔疾病 | Respiratory, thoracic and mediastinal disorders |
| 14 | 胃肠系统疾病 | Gastrointestinal disorders |
| 15 | 肝胆系统疾病 | Hepatobiliary disorders |
| 16 | 皮肤及皮下组织类疾病 | Skin and subcutaneous tissue disorders |
| 17 | 各种肌肉骨骼及结缔组织疾病 | Musculoskeletal and connective tissue disorders |
| 18 | 肾脏及泌尿系统疾病 | Renal and urinary disorders |
| 19 | 妊娠期、产褥期及围产期状况 | Pregnancy, puerperium and perinatal conditions |
| 20 | 生殖系统及乳腺疾病 | Reproductive system and breast disorders |
| 21 | 先天性、家族性及遗传性疾病 | Congenital, familial and genetic disorders |
| 22 | 各类检查 | Investigations |
| 23 | 各类损伤、中毒及操作并发症 | Injury, poisoning and procedural complications |
| 24 | 外科及内科的各种操作及治疗 | Surgical and medical procedures |
| 25 | 社会环境 | Social circumstances |
| 26 | 产品问题 | Product issues |
| 27 | 全身性疾病及给药部位各种反应 | General disorders and administration site conditions |

## 本系统使用方式
本系统在 MVP 阶段使用内置的 MedDRA 同义词映射表（30+ 医学同义词），
覆盖了临床试验中最常见的不良事件术语。完整版 MedDRA 词典可通过
meddra.org 官网免费申请获取（非商业用途）。

## 替代方案
- SNOMED CT: https://www.snomed.org （免费版）
- ICD-11: https://icd.who.int （WHO 完全免费）