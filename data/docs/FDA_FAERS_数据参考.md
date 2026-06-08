# FDA FAERS 不良事件报告系统参考

## 来源
FDA Adverse Event Reporting System (FAERS)
https://www.fda.gov/drugs/questions-and-answers-fdas-adverse-event-reporting-system-faers/fda-adverse-event-reporting-system-faers-public-dashboard

## 数据概述
- **范围**: 2004年至今，每季度更新
- **费用**: 完全免费，无需注册
- **格式**: ASCII/XML
- **数据量**: 每季度约60-70MB，全部约5-8GB

## 数据文件结构（7个表）

| 文件名 | 内容 | 说明 |
|--------|------|------|
| DEMO | 患者人口学信息 | 年龄、性别、体重、事件日期、报告来源 |
| DRUG | 药物信息 | 药物名称、给药途径、剂量、适应症、在事件中的角色 |
| REAC | 不良反应 | MedDRA PT 编码的不良事件 |
| OUTC | 转归 | 事件转归（死亡、危及生命、住院等） |
| RPSR | 报告来源 | 报告人职业、报告国家 |
| THER | 治疗日期 | 药物治疗开始/结束日期 |
| INDI | 适应症 | 药物使用适应症（MedDRA 编码） |

## 下载方式
- 主页面: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
- 按年份+季度下载 ZIP 压缩包
- 示例: https://fis.fda.gov/content/Exports/faers_ascii_2024Q1.zip

## 数据特点
- 非累积数据，需自行合并去重
- 主要为英文数据
- 包含自发报告和临床试验报告
- 每个季度数据独立，需要按 CASEID 去重

## 本系统使用场景
智能体4（安全性信号挖掘）使用 FAERS 数据进行：
1. 药物-事件信号检测（PRR/ROR/EBGM 等算法）
2. 背景发生率估算
3. 同类药物安全性对比

## 当前 MVP 实现
MVP 阶段使用模拟数据替代 FAERS 完整数据集，核心算法逻辑已实现。
完整 FAERS 数据可通过上述链接下载后导入系统的向量数据库。