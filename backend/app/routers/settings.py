from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from notion_client import Client

from app.deps.security import verify_api_key

router = APIRouter(prefix="/settings", tags=["settings"])


def _load_backend_env() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    load_dotenv(dotenv_path=backend_root / ".env", override=True)


@router.get("/notion-test")
async def notion_test(_: None = Depends(verify_api_key)):
    """
    Notion 連線測試（不回傳任何 secret）。
    成功回傳 {"ok": true}，失敗回 400 與錯誤原因。
    """
    import os

    _load_backend_env()
    notion_secret = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_SECRET")
    notion_database_id = os.getenv("NOTION_DATABASE_ID")

    if not notion_secret or not notion_database_id:
        raise HTTPException(
            status_code=400,
            detail="缺少 NOTION_API_KEY/NOTION_SECRET 或 NOTION_DATABASE_ID（請檢查 backend/.env）",
        )

    try:
        client = Client(auth=notion_secret)
        client.databases.retrieve(database_id=notion_database_id)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Notion 連線失敗: {e}") from e


@router.get("/ping")
async def ping_settings():
    return {"ok": True}
