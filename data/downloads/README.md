# 公开数据下载 - AE Sentinel

本文件夹用于存放开发计划书要求下载的公开文档和数据。

## 已下载的参考文档（可在 ../docs/ 查看）

- `CIOMS-I_参考文档.md` - CIOMS-I 报告规范参考
- `MedDRA_层级结构参考.md` - MedDRA 层级结构说明
- `FDA_FAERS_数据参考.md` - FAERS 数据格式说明
- `PubMed_文献检索参考.md` - PubMed API 使用说明
- `ICH_GCP_安全性报告指南.md` - ICH GCP 安全性报告要求
- `方案偏离检测规则参考.md` - 方案偏离检测规则

## FAERS 公开数据下载指南

### 下载地址
官网：https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html

推荐下载最新的季度数据：
- ASCII 格式比较小：约 60-65MB/季度
- XML 格式较大：约 110-140MB/季度

示例链接（2024 Q4 ASCII）：
```
https://fis.fda.gov/content/Exports/faers_ascii_2024q4.zip
```

### 文件说明
FAERS 每个季度包包含以下文件：
- `DEMOxx` - 人口统计学信息
- `DRUGxx` - 药物信息
- `REACxx` - 不良反应/事件信息
- `OUTCxx` - 患者结局
- `RPSRxx` - 报告来源
- `THERxx` - 治疗信息
- `INDIxx` - 适应症信息

## PubMed API 文献数据

项目已内置 NCBI API Key，可直接用于检索。文献检索示例结果保存在：
- `../docs/PubMed_文献检索参考.md`

## MedDRA 术语库

### 官方获取方式
官网：https://www.meddra.org
- 需要注册订阅，学术/非商业用途免费
- 审核通过后下载 ASCII 格式文件

### 替代方案（开发阶段）
本项目已内置 MedDRA 层级结构参考字典，可直接用于原型开发。

## CIOMS-I 报告模板

CIOMS 官网提供免费报告模板下载：
https://cioms.ch/publications/ 搜索 "Working Group VI"

## ICH GCP 指南

ICH GCP E6(R2) 完整版：
https://www.ich.org/page/ich-guidelines


### 数据文件夹结构
```
data/
├── docs/              # 参考文档（Markdown 格式）
├── downloads/         # 原始数据文件（本文件夹）
├── chroma/            # ChromaDB 向量数据库
└── ae_sentinel.db     # SQLite 关系数据库
```

## 说明

由于网络原因，无法自动下载完整的 FAERS 原始数据文件（约 65MB）。用户可根据上述链接手动下载后放入本文件夹。项目代码已支持读取 FAERS 数据。
