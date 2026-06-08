"""AE Sentinel Launch Script"""
import sys
import os

# Add local lib to path (jwt, multipart, etc.)
lib_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
if os.path.exists(lib_dir) and lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

# Add backend to path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Change to backend directory for relative imports
os.chdir(backend_dir)

import uvicorn
from backend.core.config import HOST, PORT, DEBUG
from backend.main import app

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)