"""运行脚本。

本地开发：
    python run.py
或：
    uvicorn app.main:app --reload --port 8000
"""
import sys
from pathlib import Path

# 确保 backend/ 在 sys.path 中
backend_dir = str(Path(__file__).resolve().parents[2] / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app", backend_dir],
    )
