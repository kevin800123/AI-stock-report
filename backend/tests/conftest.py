from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("UPLOAD_API_KEY", "test-upload-key")
os.environ.setdefault("REQUIRE_UPLOAD_API_KEY", "true")
os.environ.setdefault("UPLOAD_MAX_BYTES", str(10 * 1024 * 1024))


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


@pytest.fixture
def upload_headers():
    return {"X-API-Key": "test-upload-key"}
