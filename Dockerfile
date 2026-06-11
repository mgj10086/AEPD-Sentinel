# AE Sentinel - 多阶段构建
# 药物临床试验不良事件智能监测平台

# ===== 阶段 1: 构建前端 =====
FROM node:20-alpine AS frontend-builder

WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ===== 阶段 2: Python 运行时 + nginx =====
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖（含 nginx + curl）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl nginx \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/
COPY lib/ ./lib/
COPY run.py .

# 从前端构建产物复制到 nginx 静态目录
COPY --from=frontend-builder /build/dist /usr/share/nginx/html/

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 创建数据目录
RUN mkdir -p /app/data

EXPOSE 80

# 启动脚本：先启动 uvicorn 后端，再启动 nginx（前台运行）
CMD python run.py & nginx -g 'daemon off;'
