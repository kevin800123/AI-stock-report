import os

from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from notion_client import Client
from pydantic import BaseModel

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsGetResponse(BaseModel):
    notion_database_id: str | None = None


def _load_backend_env() -> None:
    # 固定只讀取專案內 backend/.env（避免 cwd 或其他路徑混淆）
    backend_root = Path(__file__).resolve().parents[2]
    load_dotenv(dotenv_path=backend_root / ".env", override=True)


@router.get("/", response_model=SettingsGetResponse)
async def get_settings():
    # 僅從 backend/.env（或環境變數）讀取，不接受前端上傳任何 secret
    _load_backend_env()
    return {"notion_database_id": os.getenv("NOTION_DATABASE_ID")}


@router.get("/notion-test")
async def notion_test():
    """
    Notion 連線測試（不回傳任何 secret）。
    成功回傳 {"ok": true}，失敗回 400 與錯誤原因。
    """
    _load_backend_env()
    notion_secret = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_SECRET")
    notion_database_id = os.getenv("NOTION_DATABASE_ID")

    if not notion_secret or not notion_database_id:
        raise HTTPException(status_code=400, detail="缺少 NOTION_API_KEY/NOTION_SECRET 或 NOTION_DATABASE_ID（請檢查 backend/.env）")

    try:
        client = Client(auth=notion_secret)
        client.databases.retrieve(database_id=notion_database_id)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Notion 連線失敗: {e}")


@router.get("/ping")
async def ping_settings():
    return {"ok": True}