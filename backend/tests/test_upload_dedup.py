from __future__ import annotations

import asyncio
import uuid
from io import BytesIO

from sqlalchemy import select

def _pdf(suffix: bytes) -> bytes:
    return b"%PDF-1.4 minimal\n" + suffix


def _mark_latest_completed():
    from app.database import AsyncSessionLocal
    from app.models import Report

    async def _run():
        async with AsyncSessionLocal() as session:
            report = (await session.execute(select(Report).order_by(Report.id.desc()))).scalars().first()
            assert report is not None
            report.status = "completed"
            await session.commit()

    asyncio.run(_run())


def test_upload_duplicate_completed_returns_409(client, upload_headers):
    tag = uuid.uuid4().bytes
    payload = BytesIO(_pdf(tag))
    files = {"file": ("report-a.pdf", payload, "application/pdf")}
    r1 = client.post("/reports/upload", files=files, headers=upload_headers)
    assert r1.status_code == 200

    _mark_latest_completed()

    files2 = {"file": ("report-b.pdf", BytesIO(_pdf(tag)), "application/pdf")}
    r2 = client.post("/reports/upload", files=files2, headers=upload_headers)
    assert r2.status_code == 409
    assert "已分析過" in r2.json()["detail"]


def test_upload_duplicate_processing_returns_409(client, upload_headers, monkeypatch):
    monkeypatch.setattr("app.routers.reports.process_report_file", lambda *_a, **_k: None)

    tag = uuid.uuid4().bytes
    files = {"file": ("proc.pdf", BytesIO(_pdf(tag)), "application/pdf")}
    r1 = client.post("/reports/upload", files=files, headers=upload_headers)
    assert r1.status_code == 200

    files2 = {"file": ("proc2.pdf", BytesIO(_pdf(tag)), "application/pdf")}
    r2 = client.post("/reports/upload", files=files2, headers=upload_headers)
    assert r2.status_code == 409
    assert "正在處理" in r2.json()["detail"]
