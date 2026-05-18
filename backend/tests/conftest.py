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
# 測試套件含多次上傳，避免 slowapi 5/min 導致非預期 429
os.environ["UPLOAD_RATE_LIMIT"] = "1000/minute"


def _ensure_reports_schema():
    """CI 為全新 DB：先建表，再對舊庫補 content_sha256 欄位。"""
    import asyncio

    from sqlalchemy import text

    import app.models  # noqa: F401 — register ORM
    from app.database import Base, engine

    async def _run():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            rows = await conn.execute(text("PRAGMA table_info(reports)"))
            cols = {r[1] for r in rows.fetchall()}
            if "content_sha256" not in cols:
                await conn.execute(
                    text("ALTER TABLE reports ADD COLUMN content_sha256 VARCHAR(64)")
                )
                await conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_reports_content_sha256 "
                        "ON reports (content_sha256)"
                    )
                )

    asyncio.run(_run())


_ensure_reports_schema()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


@pytest.fixture
def upload_headers():
    return {"X-API-Key": "test-upload-key"}
