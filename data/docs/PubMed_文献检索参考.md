# PubMed 药物安全性文献检索参考

## 来源
NCBI PubMed E-utilities API
https://www.ncbi.nlm.nih.gov/books/NBK25501/

## API 使用方式
- Base URL: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
- 速率限制: 无 API Key 3次/秒，有 API Key 10次/秒
- 费用: 完全免费

## 检索策略示例

### 1. 免疫检查点抑制剂肝毒性
查询: `immune checkpoint inhibitor adverse events hepatotoxicity`
PMID 示例: 42162618, 42130622, 42117126, 42057600, 42014238

### 2. PD-1/PD-L1 抑制剂相关肺炎
查询: `PD-1 inhibitor pneumonitis clinical trial safety`

### 3. 单克隆抗体输液反应
查询: `monoclonal antibody infusion reaction management`

### 4. 药物性肝损伤 (DILI)
查询: `drug-induced liver injury clinical trial monitoring guidelines`

## 本系统使用场景
智能体4（安全性信号挖掘）使用 PubMed API 进行：
1. 同类药物安全性文献检索
2. 新发安全性信号验证
3. 信号背景文献支持
4. 药品说明书（IB）更新参考

## 文献筛选标准
- 发表时间: 近5年优先
- 研究类型: 临床试验、系统综述、Meta分析、病例报告
- 相关性: 与目标药物和 AE 直接相关
- 语言: 英文为主

## 当前 MVP 实现
MVP 阶段使用 PubMed API 进行实时文献检索，检索结果作为信号评估的
文献支持证据。完整文献分析功能需接入 LLM 进行摘要提取和证据评级。