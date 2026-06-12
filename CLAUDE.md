# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@规则参见：d:/Users/Administrator/Documents/Obsidian Vault/Claude相关/项目启动宪法.md
@全局上下文：C:/Users/Administrator/.claude/projects/d--works-AIclass-agent-AEPD-Sentinel/memory/global-context.md

## Project Overview

AE Sentinel — 药物临床试验不良事件智能监测平台。对临床试验中的不良事件(AE)进行 MedDRA 编码、严重性判定、SAE报告自动生成、方案偏离检测、安全性信号挖掘和合规质控。

## 技术栈

- **后端**：Python 3.9+ / FastAPI / Uvicorn / ChromaDB / PyMySQL (vendored) / PyJWT (vendored)
- **前端**：Vue3 Composition API / Pinia / Element Plus / ECharts / Vite / axios
- **数据库**：MySQL (生产) / SQLite (本地开发)，通过 `DATABASE_ENGINE` 环境变量切换
- **容器化**：Docker Compose (应用 + ChromaDB + 可选 Ollama)

## Commands

```bash
# 启动后端 (开发模式, 热重载)
python run.py

# 启动前端开发服务器 (端口5173, Vite 自动代理 /api → localhost:8000)
cd frontend && npm run dev

# 前端构建
cd frontend && npm run build

# Docker 全栈启动 (应用 + ChromaDB + 可选 Ollama)
docker-compose up -d

# 端到端测试 (先确保后端已启动)
python test_e2e.py
```

## Architecture

```
请求 → FastAPI Router (backend/api/) → Agent (backend/agents/) → Database (backend/core/database.py)
                                                    ↕
                                           Service (backend/services/)
```

**三层分离**：
- `backend/api/` — 路由层，只做参数校验和响应格式化，调用 agent。每个模块有独立的 router 和 prefix
- `backend/agents/` — 业务逻辑层，所有领域计算在这里（当前为规则匹配 + 模拟数据）
- `backend/services/` — 基础设施层（向量检索、文档导出、知识管理、审计日志）

**API 路由映射**（全部挂在 FastAPI app 上）：

| Router 模块 | URL Prefix | 对应 Agent | 功能 |
|---|---|---|---|
| `api/auth.py` | `/api/auth` | — | Mock JWT 登录 |
| `api/ae.py` | `/api/ae` | `agents/ae_coder.py` | AE 编码、批量导入 |
| `api/sae.py` | `/api/sae` | `agents/sae_report.py` | SAE 报告生成与导出 |
| `api/deviations.py` | `/api/deviations` | `agents/deviation.py` | 方案偏离检测 |
| `api/signals.py` | `/api/signals` | `agents/signal_agent.py` | 信号挖掘（后台线程） |
| `api/compliance.py` | `/api/compliance` | `agents/compliance.py` | 合规质控报告 |
| `api/knowledge.py` | `/api/knowledge` | `services/rag_engine.py` | 知识文档管理 |
| `api/audit.py` | `/api/audit` | `services/audit_service.py` | 审计日志查询（HMAC 防篡改链） |
| `api/users.py` | `/api/users` | `services/user_service.py` | 用户管理 CRUD |
| `api/notifications.py` | `/api/notifications` | `services/notification_service.py` | 通知/告警系统 |
| `api/admin.py` | `/api/admin` | — | 管理功能（seed 数据、mock-cases） |
| `api/health.py` | `/api/health` | — | 健康检查 |

## Backend Patterns

**数据库抽象**：`backend/core/database.py` 提供统一的 `get_db()` / `execute_query()` / `execute_insert()` API，自动将 MySQL `%s` 占位符转换为 SQLite `?`。引擎由环境变量 `DATABASE_ENGINE` 控制（默认 `mysql`，可设为 `sqlite` 用于本地无 MySQL 开发）。所有 DDL 写在 `init_db()` 中，启动时自动建表和插入默认数据。

**向量检索**：`backend/services/rag_engine.py` 封装 ChromaDB 持久化客户端，数据目录在 `data/chroma/`。提供 `add_documents()` / `search_documents()` / `delete_documents()` API。知识文档上传后自动向量化存入 ChromaDB。

**审计日志自动记录**：每个 API 端点处理完业务后，通过 `audit_service.extract_username_from_token()` 从 JWT 中提取用户，调用 `write_audit_log()` 写入 `audit_logs` 表。审计日志 ID 格式为 `AUD-{12位HEX}`。

**AE 编码 → 偏离检测自动联动**：`process_ae()` 写入 ae_results 后，自动调用 `deviation.process_patient_visit()` 检测该患者访视的方案偏离。这是一个跨 agent 的隐式依赖 — 修改 ae_coder 或 deviation 时需注意此耦合。

**审计日志 HMAC 防篡改链**：`audit_logs` 表包含 `hmac`/`prev_hmac`/`prev_log_id` 字段形成哈希链，防止历史日志被篡改。`/api/audit/verify` 端点可验证完整日志链的完整性。

**通知系统自动触发**：方案偏离检测、SAE 判定等关键事件自动调用 `notification_service.create_notification()` 生成通知，目标用户从偏离规则配置或任务分配中获取。

**全局前端状态三态**：`stores/app.js` 管理 `loading`/`error`/`success` 三态，`App.vue` 提供全局遮罩层，`composables/usePageState.js` 提供页面级 loading 封装。

**文档导出**：`backend/services/export_service.py` 支持 SAE 报告导出为 docx/json/pdf（PDF 使用 fpdf2 真实渲染 CIOMS-I 报告，自动检测中文字体）。

**本地依赖**：`lib/` 目录包含 vendored 的 PyJWT (v2.13.0)、PyMySQL (v1.2.0)、python-multipart (v0.0.32)，`run.py` 和 `database.py` 都会将 `lib/` 加入 `sys.path`。不需要 `pip install` 这些包。

**启动流程**：`run.py` → 设置 sys.path (项目根 + lib/) → `uvicorn.run(app)` → FastAPI `startup` 事件 → `init_db()` 建表 + 插入默认偏离规则 (PD-001~PD-007)。

## Frontend Architecture

```
frontend/src/
├── main.js              # 挂载 Vue app，注册 router + Pinia + Element Plus
├── App.vue              # 根组件 (<router-view/> + 全局 loading/error 遮罩)
├── router/index.js      # 路由定义 + beforeEach 守卫 + meta.roles 角色权限
├── api/index.js         # axios 实例 + 拦截器
├── stores/
│   └── app.js           # Pinia store (token/user/login/logout + loading/error 三态)
├── composables/
│   └── usePageState.js  # 页面级 loading/error 封装
├── components/
│   └── AppLayout.vue    # 主布局 (侧边栏角色过滤菜单 + 顶栏通知铃铛 + <router-view/>)
└── views/               # 10 个页面组件 (懒加载)
    ├── Login.vue        # 登录页 (独立路由，不使用 AppLayout)
    ├── Dashboard.vue    # 仪表盘 (ECharts 图表，数据来自后端 seed API)
    ├── AeCoding.vue     # AE 编码
    ├── SaeReports.vue   # SAE 报告
    ├── Deviations.vue   # 方案偏离
    ├── Signals.vue      # 信号挖掘
    ├── Compliance.vue   # 合规质控
    ├── Knowledge.vue    # 知识库
    ├── Audit.vue        # 审计日志
    └── UserManagement.vue # 用户管理 (admin 专属)
```

**路由设计**：`/login` 是独立路由（无布局）；其他页面均为 `AppLayout` 的子路由。`beforeEach` 守卫检查 `ae_token` 是否存在，未登录自动跳转 `/login`。每个子路由 `meta.roles` 定义可见角色，`AppLayout` 按用户角色动态过滤菜单项。

**API 层**：axios 实例 `baseURL: ''`，开发时 Vite dev server (port 5173) 把 `/api/*` 代理到 `http://localhost:8000`。请求拦截器自动附加 `Bearer token`；响应拦截器统一处理 401/403/500 错误，401 时自动清空 token 并跳转登录页。

**状态管理**：单 store (`useAppStore`)，管理 `token`、`user`、`isLoggedIn`，登录信息持久化到 localStorage (`ae_token` / `ae_user`)。

## Key Conventions

- **导入路径**：全项目统一使用 `backend.xxx` 绝对导入（如 `from backend.core.config import TRIAL_DRUG`），不要使用 `from core.xxx` 相对路径
- **数据库 SQL**：编写时使用 MySQL 语法（`%s` 占位符、`INSERT IGNORE` 等），SQLite 兼容层通过 `_to_sqlite_sql()` 自动转换。DDL 语句写在 `init_db()` 中
- **API 响应格式**：统一 `{"code": 200, "message": "success", "data": {...}, "timestamp": "ISO8601"}`
- **Agent 实现**：当前为规则匹配 + 模拟数据。ae_coder 基于 `MEDDRA_SYNONYMS` 关键词字典匹配 MedDRA 编码；severity/sae 判定基于关键词；signal_agent 模拟 Fisher 检验和 PubMed 检索。config 中已预留 LLM 接入点 (ZHIPU/QWEN API key)
- **前端**：Vue3 Composition API + Pinia + Element Plus + ECharts。页面组件均为懒加载
- **Auth**：Mock JWT 认证（HS256），用户数据存储在 `users` 数据库表中（`services/user_service.py` 管理）。登录返回 token，前端所有 API 请求通过 axios 拦截器自动附加。角色支持：`admin` / `pv_specialist` / `cra`

## Data Flow Examples

**AE 编码流程**：`POST /api/ae/process` → `ae_coder.process_ae()` → MedDRA 关键词匹配 → 严重性/SAE/预期性/因果关系判定 → 写入 `ae_results` 表 → 自动触发方案偏离检测 (`deviation.process_patient_visit()`) → 写入审计日志

**SAE 报告流程**：`POST /api/saereport/generate` → `sae_report.generate_sae_report()` → 从 `ae_results` 读取 → 生成 CIOMS-I 字段 → 写入 `sae_reports` 表 → 支持导出 docx/json/pdf

**信号挖掘流程**：`POST /api/signals/trigger` → 后台线程运行 `signal_agent.analyze_signal()` → 按器官系统分类统计 AE → 模拟 Fisher 检验 → 模拟 PubMed 文献检索 → 写入 `signals` 表

## Database Tables

`ae_results`, `sae_reports`, `deviation_rules`, `deviations`, `signals`, `knowledge_items`, `audit_logs`, `users`, `notifications` — 全部在 `init_db()` 中自动创建，支持 MySQL 和 SQLite 双引擎。默认偏差规则（PD-001 ~ PD-007）在首次初始化时通过 `INSERT IGNORE` / `INSERT OR IGNORE` 幂等插入。

## Reference Documents

- `data/docs/` — 领域参考文档：CIOMS-I 报告规范、MedDRA 层级结构、FDA FAERS 数据格式、PubMed 检索方法、ICH GCP 安全性报告指南、方案偏离检测规则
- `项目文件/` — 项目文档：项目书、开发需求配合确认书、前后端接口文档、模拟测试病例、API keys
- `data/downloads/` — FAERS 原始数据文件 (ASCII 格式)、下载脚本

## Docker Architecture

`docker-compose.yml` 包含两个 service：
- `ae-sentinel` — **多阶段构建**：Stage 1 (node:20) 构建前端静态文件 → Stage 2 (python:3.10 + nginx) 运行 FastAPI 并 serve 静态文件，端口 80
- `chromadb` — ChromaDB 向量数据库容器（端口 8001），持久化到 `data/chroma/`
- 注释掉的 `ollama` service 用于本地 LLM 部署（端口 11434）

`Dockerfile` 采用多阶段构建，最终镜像仅包含 Python 运行时 + nginx 二进制，不包含 node 和构建依赖。

## 质量优先级

功能完整度 > 代码简洁性 > token 节省 > 性能优化

## 工作方式（宪法规定，不可违反）

1. 跨文件改动（3+文件）→ 必须先 EnterPlanMode，用户确认后才写代码
2. 每次只改一个逻辑单元 → 改完验证
3. 每个小任务完成后 → 提交
4. 并行任务 → 用 Worktree 隔离
5. 遇到阻碍 → 先查 `d:/Users/Administrator/Documents/Obsidian Vault/Claude相关/操作突破日志.md`
