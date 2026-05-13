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


def _env_path() -> Path:
    return Path(__file__).resolve().parents[2] / ".env"


def _read_env_kv() -> dict[str, str]:
    p = _env_path()
    if not p.exists():
        return {}
    txt = p.read_text(encoding="utf-8", errors="ignore")
    out: dict[str, str] = {}
    for line in txt.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


@router.get("/runtime")
async def runtime_env_info():
    """
    回傳後端實際讀取的 .env 路徑（不洩漏任何 secret）。
    用於排查多份專案/多份 .env 時的混淆。
    """
    backend_root = Path(__file__).resolve().parents[2]
    env_path = backend_root / ".env"
    _load_backend_env()
    notion_db = os.getenv("NOTION_DATABASE_ID") or ""
    return {
        "backend_root": str(backend_root),
        "env_path": str(env_path),
        "env_exists": env_path.exists(),
        "notion_db_is_placeholder": notion_db == "your_notion_database_id_here",
        "notion_db_len": len(notion_db),
    }


@router.get("/env-check")
async def env_check():
    """
    檢查 backend/.env 檔案內容是否仍為 placeholder（不回傳任何 secret）。
    """
    kv = _read_env_kv()
    ndb = kv.get("NOTION_DATABASE_ID", "")
    nkey = kv.get("NOTION_API_KEY", kv.get("NOTION_SECRET", ""))
    gkey = kv.get("GEMINI_API_KEY", kv.get("GOOGLE_API_KEY", ""))
    return {
        "env_path": str(_env_path()),
        "env_exists": _env_path().exists(),
        "notion_db_is_placeholder": ndb == "your_notion_database_id_here",
        "notion_db_len": len(ndb),
        "notion_key_is_placeholder": nkey == "your_notion_api_key_here",
        "notion_key_len": len(nkey),
        "gemini_key_is_placeholder": gkey == "your_gemini_api_key_here",
        "gemini_key_len": len(gkey),
    }


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