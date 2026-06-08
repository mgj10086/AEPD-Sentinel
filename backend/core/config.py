"""AE Sentinel Configuration"""
import os

# Server
HOST = "0.0.0.0"
PORT = 8000
DEBUG = False

# SQLite
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ae_sentinel.db")

# ChromaDB
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chroma")
CHROMA_COLLECTION = "ae_knowledge"

# LLM
LLM_MODEL = "glm-4"
LLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")

# APIs
NCBI_API_KEY = "48ad085bdbd9480a4c9cd14a4470afc83c09"
FAERS_API_KEY = "Fke2z4izGbpdUgMC845cDYBEQOofQz4bqrXHfNgU"

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

# Mock auth
MOCK_USERS = {
    "pv_user": {"password": "123456", "role": "pv_specialist", "name": "张医生"},
    "cra_user": {"password": "123456", "role": "cra", "name": "李监查"},
    "admin_user": {"password": "123456", "role": "admin", "name": "管理员"},
}

# JWT
SECRET_KEY = "ae-sentinel-secret-key-2026"
ALGORITHM = "HS256"
TOKEN_EXPIRE = 3600
