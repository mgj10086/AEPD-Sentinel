"""AE Sentinel Configuration"""
import os

# Server
HOST = "0.0.0.0"
PORT = 8000
DEBUG = False

# Database selection: "mysql" or "sqlite"
# If MySQL is not available, use "sqlite" for development
DATABASE_ENGINE = os.getenv("DATABASE_ENGINE", "mysql")

# MySQL configuration
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "123456")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "ae_sentinel")

# SQLite configuration (fallback)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ae_sentinel.db")

# Ensure data directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# ChromaDB
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chroma")
CHROMA_COLLECTION = "ae_knowledge"

# LLM (set via environment variables)
LLM_MODEL = os.getenv("LLM_MODEL", "glm-4")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")

# APIs (set via environment variables, never commit real keys)
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")
FAERS_API_KEY = os.getenv("FAERS_API_KEY", "")

# Trial
TRIAL_NAME = "XK-2025-001"
TRIAL_DRUG = "XK-001"
TRIAL_INDICATION = "晚期非小细胞肺癌（NSCLC）"
VISIT_WINDOW_DAYS = 3

# Expected AE
EXPECTED_AES = [
    "免疫相关肺炎", "免疫相关肝炎", "免疫相关结肠炎", "输液反应",
    "疲乏", "发热", "皮疹", "瘙痒", "恶心", "头痛", "食欲下降",
    "贫血", "血小板减少", "中性粒细胞减少"
]

# Mock auth (密码使用 SHA256 哈希存储)
# 注意：用户数据已迁移到 users 表，参见 user_service.py
# MOCK_USERS 字典已移除，保留 _hash 函数兼容性引用

# JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
ALGORITHM = "HS256"
TOKEN_EXPIRE = int(os.getenv("JWT_EXPIRE_SECONDS", 3600))

# Audit log HMAC key (for tamper-evident hash chain)
AUDIT_HMAC_KEY = os.getenv("AUDIT_HMAC_KEY", "")

# SECURITY: Refuse to start with default/empty secrets
# Set JWT_SECRET_KEY and AUDIT_HMAC_KEY in .env or environment
if not SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY 未设置！请在 .env 文件中设置一个随机密钥。\n"
        "生成命令: python -c \"import secrets; print(secrets.token_hex(32))\""
    )
if not AUDIT_HMAC_KEY:
    raise RuntimeError(
        "AUDIT_HMAC_KEY 未设置！请在 .env 文件中设置一个随机密钥。\n"
        "生成命令: python -c \"import secrets; print(secrets.token_hex(32))\""
    )
