from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, Request, UploadFile
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import REQUIRE_UPLOAD_API_KEY, UPLOAD_API_KEY, UPLOAD_MAX_BYTES

limiter = Limiter(key_func=get_remote_address)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

CHUNK_SIZE = 1024 * 1024
PDF_MAGIC = b"%PDF"


async def verify_api_key(api_key: str | None = Depends(api_key_header)) -> None:
    if REQUIRE_UPLOAD_API_KEY and not UPLOAD_API_KEY:
        raise HTTPException(status_code=500, detail="伺服器未設定 UPLOAD_API_KEY")
    if not UPLOAD_API_KEY:
        return
    if not api_key or not secrets.compare_digest(api_key, UPLOAD_API_KEY):
        raise HTTPException(status_code=401, detail="缺少或無效的 API key")


async def read_upload_with_limits(
    file: UploadFile,
    request: Request,
    max_bytes: int = UPLOAD_MAX_BYTES,
) -> bytes:
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            declared = int(content_length)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="無效的 Content-Length") from exc
        if declared > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"檔案超過大小上限（{max_bytes // (1024 * 1024)} MB）",
            )

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"檔案超過大小上限（{max_bytes // (1024 * 1024)} MB）",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def assert_pdf_content(content: bytes) -> None:
    if len(content) < 5 or not content.startswith(PDF_MAGIC):
        raise HTTPException(status_code=400, detail="檔案內容不是有效的 PDF")
