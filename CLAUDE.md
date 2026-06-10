# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AE Sentinel — 药物临床试验不良事件智能监测平台。对临床试验中的不良事件(AE)进行 MedDRA 编码、严重性判定、SAE报告自动生成、方案偏离检测、安全性信号挖掘和合规质控。

## Commands

```bash
# 启动后端 (开发模式, 热重载)
python run.py

# 启动前端开发服务器 (端口5173, API代理到8000)
cd frontend && npm run dev

# 前端构建
cd frontend && npm run build

# Docker 全栈启动
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
- `backend/api/` — 路由层，只做参数校验和响应格式化，调用 agent
- `backend/agents/` — 业务逻辑层，所有领域计算在这里
- `backend/services/` — 基础设施层（向量检索、文档导出、知识管理）

**数据库抽象**：`backend/core/database.py` 提供统一的 `get_db()` / `execute_query()` / `execute_insert()` API，自动将 MySQL `%s` 占位符转换为 SQLite `?`。引擎由环境变量 `DATABASE_ENGINE` 控制（默认 `mysql`，可设为 `sqlite` 用于本地无 MySQL 开发）。

**向量检索**：`backend/services/rag_engine.py` 封装 ChromaDB 持久化客户端，数据目录在 `data/chroma/`。知识文档上传后自动向量化存入 ChromaDB。

**本地依赖**：`lib/` 目录包含 vendored 的 PyJWT、PyMySQL、python-multipart，`run.py` 和 `database.py` 会将 `lib/` 加入 `sys.path`。不需要 `pip install` 这些包。

## Key Conventions

- **导入路径**：全项目统一使用 `backend.xxx` 绝对导入（如 `from backend.core.config import TRIAL_DRUG`），不要使用 `from core.xxx` 相对路径
- **数据库 SQL**：编写时使用 MySQL 语法（`%s` 占位符），SQLite 兼容层自动转换。DDL 语句写在 `init_db()` 中
- **API 响应格式**：统一 `{"code": 200, "message": "success", "data": {...}, "timestamp": "..."}`
- **Agent 实现**：当前为规则匹配 + 模拟数据（基于关键词字典），预留了 LLM 接入点（config 中已配 ZHIPU/QWEN API key）
- **前端**：Vue3 Composition API + Pinia 状态管理 + Element Plus 组件库 + ECharts 图表。路由守卫检查 token 存在性，API 层通过 axios 拦截器自动附加 Bearer token
- **Auth**：Mock JWT 认证，用户定义在 `backend/core/config.py` 的 `MOCK_USERS` 字典中

## Data Flow Examples

**AE 编码流程**：`POST /api/ae/process` → `ae_coder.process_ae()` → MedDRA 关键词匹配 → 严重性/SAE/预期性/因果关系判定 → 写入 `ae_results` 表 → 自动触发方案偏离检测 (`deviation.process_patient_visit()`)

**SAE 报告流程**：`POST /api/saereport/generate` → `sae_report.generate_sae_report()` → 从 `ae_results` 读取 → 生成 CIOMS-I 字段 → 写入 `sae_reports` 表 → 支持导出 docx/json/pdf

**信号挖掘流程**：`POST /api/signals/trigger` → 后台线程运行 `signal_agent.analyze_signal()` → 按器官系统分类统计 AE → 模拟 Fisher 检验 → 模拟 PubMed 文献检索 → 写入 `signals` 表

## Database Tables

`ae_results`, `sae_reports`, `deviation_rules`, `deviations`, `signals`, `knowledge_items`, `audit_logs` — 全部在 `init_db()` 中自动创建，支持 MySQL 和 SQLite 双引擎。默认偏差规则（PD-001 ~ PD-007）在首次初始化时插入。
