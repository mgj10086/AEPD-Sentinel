"""AE Sentinel Launch Script"""
import sys
import os

# Disable ChromaDB telemetry to avoid posthog API compatibility issues
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"

# Add project root to sys.path so 'backend.xxx' imports work
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add local lib to path (jwt, multipart, etc.)
lib_dir = os.path.join(project_root, "lib")
if os.path.exists(lib_dir) and lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

import uvicorn
from backend.core.config import HOST, PORT, DEBUG
from backend.main import app

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)
