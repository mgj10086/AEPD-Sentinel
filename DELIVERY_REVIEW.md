# AE Sentinel V1.0 交付验收报告

> 审查日期：2026-06-10 | 专家组：医药领域 + 技术架构 + 产品商业化 + 法务合规

---

## 总览

| 级别 | 数量 | 说明 |
|---|---|---|
| P0 阻断 | 7 | 必须修复才能交付 |
| P1 重要 | 10 | 应在交付前修复 |
| P2 改进 | 8 | 可在V1.1迭代 |

---

## P0 — 阻断交付（立即修复）

### P0-1 [安全/法务] 密钥硬编码并已提交公开仓库

**文件:** `backend/core/config.py:37-38, 61`

SECRET_KEY、NCBI_API_KEY、FAERS_API_KEY 全部明文硬编码，已通过 git push 到 gitee 公开仓库。这是安全事件 —— 任何拿到代码的人都可以伪造 JWT token、滥用 API key。

**修复:** 1) 立即轮换所有密钥 2) 移至 `.env` 文件 3) 确认 `.gitignore` 已包含 `.env`

### P0-2 [医药] 信号挖掘 p 值公式无统计学依据

**文件:** `backend/agents/signal_agent.py:121`

```python
p_value = round(0.03 * (event_count ** -0.3), 4)
```

这是捏造的数学公式，不是真实的 Fisher 精确检验。客户(药企PV部门)会立即识破。

**修复:** 使用 `scipy.stats.fisher_exact` 做真实检验，或标注为"模拟数据仅供演示"并在UI明确提示。

### P0-3 [医药] PubMed 文献检索完全随机生成

**文件:** `backend/agents/signal_agent.py:49-70`

标题、PMID、期刊、年份全部随机拼接。PMID `random.randint(30000000, 39999999)` 对应的是真实论文ID但不是该主题的文献。

**修复:** 接入 NCBI E-utilities API(已有 NCBI_API_KEY)，或标注为"模拟数据供演示"。

### P0-4 [医药] PD-003 偏离检测使用随机数模拟

**文件:** `backend/agents/deviation.py:80`

```python
if drug_name and random.random() < 0.15:  # 15%概率模拟
```

15%概率随机生成"用药依从性不足"偏离，与实际数据完全无关。客户CRA团队看到随机偏离记录会立即质疑系统可靠性。

**修复:** 移除随机逻辑，改为基于实际数据(actual_dose字段)判定，或在无数据时返回空。

### P0-5 [技术] 健康检查虚假报告

**文件:** `backend/api/health.py:28-29`

```python
"llm_status": "healthy",        # 硬编码
"vector_db_status": "healthy",   # 硬编码
```

LLM 和 VectorDB 从未做真实连接检查。如果 ChromaDB 挂掉，健康检查依然返回 healthy。

**修复:** health.py 中对 ChromaDB 做真实 ping，LLM 状态诚实标注为 "mock"(当前未接入)。

### P0-6 [UX] AeCoding.vue 中 MedDRA 编码显示 [object Object]

**文件:** `frontend/src/views/AeCoding.vue:65-67`

```html
<el-tag v-for="code in result.meddra_codes" :key="code">
  {{ code }}    <!-- code 是对象，显示 [object Object] -->
</el-tag>
```

**修复:** 改为 `{{ code.pt_name }}` 或 `{{ code.llt_name }}`。

### P0-7 [技术] health.py 中 conn.cursor() 在 SQLite 模式下崩溃

**文件:** `backend/api/health.py:17`

```python
conn = get_connection()
with conn.cursor() as cur:   # SQLite 连接没有 cursor() 方法
```

`_sqlite_connection()` 返回的是 `sqlite3.Connection`，它没有 `.cursor()` 返回上下文管理器的方式与 pymysql 不同。

**修复:** 统一使用 `execute_query()` 或做引擎判断。

---

## P1 — 重要（交付前修复）

### P1-1 [安全] CORS allow_origins=["*"]

**文件:** `backend/main.py:34`

生产环境不应允许任意跨域。改为白名单。

### P1-2 [安全] Mock 用户密码明文存储

**文件:** `backend/core/config.py:54-58`

MOCK_USERS 中密码明文 "123456"。虽然是 mock，但应改为 hash。

### P1-3 [产品] SAE 报告缺少 submit 操作

**文件:** `backend/api/sae.py`

report_status 永远是 "draft"，没有提交/审核/签发的状态流转。SAE 报告的最核心操作缺失——CRA 写完报告后无法提交。

### P1-4 [产品] 角色权限未实际生效

**文件:** `backend/api/` 全部路由, `frontend/src/router/index.js`

3 种角色(pv_specialist/cra/admin)定义了但：
- 后端所有路由均无角色中间件
- 前端菜单对 3 种角色完全一样
- 路由守卫只检查 token 存在性，不检查角色

### P1-5 [合规] SAE 缺少 24 小时快速报告时限

**文件:** `backend/agents/sae_report.py:29-35`

NMPA GCP(2020版)第四十八条要求 SAE 在获知后 **24 小时内** 报告。当前只有 onset_date + 7 天截止日，缺少 24 小时快速报告时限。

### P1-6 [医药] CIOMS-I 字段严重不完整

**文件:** `backend/agents/sae_report.py:41-57`

```python
"patient_dob": "",       # 出生日期为空
"patient_gender": "",    # 性别为空
"suspect_drug_dose": "", # 剂量为空
"study_number": "",      # 研究编号为空
"concomitant_drugs": [], # 合并用药为空
```

这些是 CIOMS-I 表格的必填字段。缺字段的 SAE 报告提交到药监会被退回。

### P1-7 [医药] SAE 判定缺少"先天性畸形"标准

**文件:** `backend/agents/ae_coder.py:48-54`

ICH E2A 定义了 6 条 SAE 标准，当前代码只实现了 5 条：
- ✅ 死亡
- ✅ 危及生命
- ✅ 导致住院
- ✅ 残疾
- ✅ 重要医学事件
- ❌ **先天性畸形/出生缺陷** — 缺失

### P1-8 [医药] 因果关系评估不符合 WHO-UMC 标准

**文件:** `backend/agents/ae_coder.py:116-121`

WHO-UMC 因果关系评估为 **6 级**：certain / probable / possible / unlikely / conditional / unassessable。当前只返回 "possible" 和 "probable" 两种。CIOMS-I 报告引用了 "WHO-UMC Causality Assessment" 方法但实际评估不完整。

### P1-9 [技术] auth.py 中 jwt 被 import 两次

**文件:** `backend/api/auth.py:5-6`

```python
import jwt
import jwt as pyjwt   # 冗余
```

### P1-10 [产品] Dashboard 硬编码 mockCases 导入逻辑

**文件:** `frontend/src/views/Dashboard.vue:162-173`

Dashboard 页面应展示概览数据，不应包含 10 条硬编码的 AE 测试数据和"导入模拟测试病例"按钮。导入功能应在 AeCoding 页面。

---

## P2 — 改进建议（V1.1 迭代）

| ID | 分类 | 描述 |
|---|---|---|
| P2-1 | 医药 | MedDRA 关键词子串匹配可能误匹配("气促"→"喘不过气") |
| P2-2 | 医药 | 信号挖掘暴露人数 hardcode 为 85，非实际统计 |
| P2-3 | 技术 | 知识库上传无文件大小/类型校验 |
| P2-4 | 技术 | 无请求速率限制(rate limiting) |
| P2-5 | 产品 | 知识库无搜索检索前端功能 |
| P2-6 | 产品 | 缺少通知/告警机制(偏离预警、SAE截止日) |
| P2-7 | 产品 | 缺少用户管理功能 |
| P2-8 | 法务 | 审计日志缺少数字签名防篡改 |
| P2-9 | 法务 | SAE报告导出PDF为docx占位(非真实PDF渲染) |
| P2-10 | 部署 | Dockerfile healthcheck 使用 curl 但镜像可能未安装 |

---

## 交付建议

**当前状态：不建议直接交付。** 7 个 P0 问题必须在交付前修复，其中 P0-1(密钥泄露)最为紧急需立即处理。

**推荐的修复顺序：**
1. 先修 P0-1(密钥泄露，立即轮换)
2. 再修 P0-5/P0-7(健康检查崩溃)
3. 再修 P0-6(前端显示bug)
4. 再修 P0-2/P0-3/P0-4(医药逻辑Mock标注)
5. 再修 P1 各项
6. P2 排入 V1.1
