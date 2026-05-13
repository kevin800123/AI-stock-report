from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Report
from app.schemas.report import ReportResponse
from app.services.report_processor import process_report_file

router = APIRouter(prefix="/reports", tags=["reports"])


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
REPORTS_DIR = DATA_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", response_model=ReportResponse)
async def upload_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只接受 PDF 檔案")

    file_id = uuid4().hex
    storage_path = REPORTS_DIR / f"{file_id}.pdf"

    content = await file.read()
    storage_path.write_bytes(content)

    report = Report(
        original_filename=file.filename,
        storage_path=str(storage_path),
        status="parsing",
    )
    session.add(report)
    await session.commit()
    await session.refresh(report)

    background_tasks.add_task(process_report_file, report.id)

    return ReportResponse.model_validate(report)


@router.get("/", response_model=list[ReportResponse])
async def list_reports(session: AsyncSession = Depends(get_session)):
    stmt = select(Report).order_by(Report.created_at.desc())
    reports = (await session.execute(stmt)).scalars().all()
    return [ReportResponse.model_validate(r) for r in reports]


@router.delete("/{report_id}", status_code=204)
async def delete_report(report_id: int, session: AsyncSession = Depends(get_session)):
    report = (await session.execute(select(Report).where(Report.id == report_id))).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="找不到報告")
    storage_path = report.storage_path
    await session.delete(report)
    await session.commit()
    if storage_path:
        p = Path(storage_path)
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass
    return Response(status_code=204)


@router.get("/ping")
async def ping_reports():
    return {"ok": True}
