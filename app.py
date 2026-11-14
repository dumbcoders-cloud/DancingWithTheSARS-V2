"""Run the local FastAPI API and Flask web interface for development."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import uvicorn  # noqa: E402
from dancing_sars.server import app  # noqa: E402


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8501, log_level="info")
