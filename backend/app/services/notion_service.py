from __future__ import annotations

import os
from pathlib import Path

import anyio
from dotenv import load_dotenv
from notion_client import Client
from sqlalchemy.ext.asyncio import AsyncSession


def _props_map(database_obj: dict) -> dict:
    return (database_obj or {}).get("properties") or {}


def _title_property_key(props: dict) -> str | None:
    for prop_key, prop_def in props.items():
        if (prop_def or {}).get("type") == "title":
            return prop_key
    return None


def _env_prop(env_var: str) -> str | None:
    v = os.getenv(env_var)
    return v.strip() if v and v.strip() else None


def _resolve_field_key(
    props: dict,
    env_var: str,
    candidates: tuple[str, ...],
) -> str | None:
    """優先使用環境變數指定的欄位名（須存在於 schema），否則找第一個候選鍵。"""
    custom = _env_prop(env_var)
    if custom and custom in props:
        return custom
    for name in candidates:
        if name in props:
            return name
    return None


def _value_for_property_type(prop_def: dict, text: str) -> dict | None:
    """依 Notion 欄位型別組出 properties 的值物件（不含外層 key）。"""
    ptype = (prop_def or {}).get("type")
    t = (text or "").strip()
    if not t or not ptype:
        return None
    if ptype == "rich_text":
        return {"rich_text": [{"text": {"content": t[:2000]}}]}
    if ptype == "title":
        return {"title": [{"text": {"content": t[:2000]}}]}
    if ptype == "select":
        return {"select": {"name": t[:2000]}}
    if ptype == "multi_select":
        parts = [x.strip() for x in t.replace("，", ",").split(",") if x.strip()]
        return {"multi_select": [{"name": p[:2000]} for p in parts[:25]]}
    if ptype == "status":
        return {"status": {"name": t[:2000]}}
    if ptype == "number":
        try:
            return {"number": float(t)}
        except ValueError:
            return {"rich_text": [{"text": {"content": t[:2000]}}]}
    return None


async def create_notion_page(
    db: AsyncSession,
    title: str,
    category: str | None,
    summary: str | None,
    tickers: str | None,
    # 數據欄位
    eps: float | None = None,
    pe_low: float | None = None,
    pe_high: float | None = None,
    target_low: float | None = None,
    target_high: float | None = None,
    # 新增優化欄位
    current_price: float | None = None,
    upside_high: float | None = None,
    rating_change: str | None = None,
    risk_tags: list[str] | None = None,
    valuation_method: str | None = "PER",
) -> str:
    """
    讀取資料庫中的 Notion 憑證，透過 Notion API 將資料新增到 Database。

    欄位名稱會依 Database schema 自動對應（標題 type=title；類別／代號依 rich_text、select 等）。
    若您的欄位名稱特殊，可在 backend/.env 設定：
    NOTION_PROPERTY_TITLE、NOTION_PROPERTY_CATEGORY、NOTION_PROPERTY_TICKERS
    等...

    回傳建立成功的 page_id。
    """
    backend_root = Path(__file__).resolve().parents[2]
    load_dotenv(dotenv_path=backend_root / ".env", override=True)
    notion_secret = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_SECRET")
    notion_database_id = os.getenv("NOTION_DATABASE_ID")

    if not notion_secret or not notion_database_id:
        raise RuntimeError("Notion 設定不存在（請先在 backend/.env 設定 NOTION_API_KEY 與 NOTION_DATABASE_ID）")

    client = Client(auth=notion_secret)

    database_obj = await anyio.to_thread.run_sync(
        lambda: client.databases.retrieve(database_id=notion_database_id)
    )
    props = _props_map(database_obj)

    # 如果是 Linked View，Notion API 不會回傳 properties
    is_view = not props and "data_sources" in database_obj
    
    # --- [優化] 如果是 View，嘗試追蹤到「原始資料庫」以利自動建立欄位 ---
    if is_view and database_obj.get("data_sources"):
        try:
            source_db_id = database_obj["data_sources"][0].get("id")
            if source_db_id:
                # 試著讀取原始資料庫的結構
                source_db_obj = await anyio.to_thread.run_sync(
                    lambda: client.databases.retrieve(database_id=source_db_id)
                )
                source_props = _props_map(source_db_obj)
                if source_props:
                    # 成功獲取原始資料庫結構！將操作目標切換為原始資料庫
                    notion_database_id = source_db_id
                    props = source_props
                    is_view = False
        except Exception:
            # 若無權限讀取原始資料庫，則維持原本的「盲寫」模式
            pass

    # --- 自動建立缺少的欄位 (只在能讀到 props 時進行) ---
    db_updates = {}
    if not is_view:
        # 基本欄位
        if not _resolve_field_key(props, "NOTION_PROPERTY_CATEGORY", ("類別", "Category", "分類", "category", "產業")):
            db_updates["類別"] = {"select": {}}
        if not _resolve_field_key(props, "NOTION_PROPERTY_TICKERS", ("股票代號", "Tickers", "Ticker", "ticker", "代號", "Stock", "股票")):
            db_updates["股票代號"] = {"rich_text": {}}
        
        # 數據欄位 (支援通用稱呼，避免 PBR 誤標為 PE)
        if not _resolve_field_key(props, "NOTION_PROPERTY_EPS", ("評價基礎數值", "預估EPS", "EPS", "BVPS")):
            db_updates["評價基礎數值"] = {"number": {"format": "number"}}
        if not _resolve_field_key(props, "NOTION_PROPERTY_PE_LOW", ("評價倍數(低)", "本益比(低)", "PE Low", "PB Low")):
            db_updates["評價倍數(低)"] = {"number": {"format": "number"}}
        if not _resolve_field_key(props, "NOTION_PROPERTY_PE_HIGH", ("評價倍數(高)", "本益比(高)", "PE High", "PB High")):
            db_updates["評價倍數(高)"] = {"number": {"format": "number"}}
        if not _resolve_field_key(props, "NOTION_PROPERTY_TARGET_LOW", ("目標價(低)", "Target Low", "target_low")):
            db_updates["目標價(低)"] = {"number": {"format": "number"}}
        if not _resolve_field_key(props, "NOTION_PROPERTY_TARGET_HIGH", ("目標價(高)", "Target High", "target_high")):
            db_updates["目標價(高)"] = {"number": {"format": "number"}}
        
        # 優化欄位
        if not _resolve_field_key(props, "NOTION_PROPERTY_CURRENT_PRICE", ("當前股價", "Current Price", "現價")):
            db_updates["當前股價"] = {"number": {"format": "number"}}
        if not _resolve_field_key(props, "NOTION_PROPERTY_UPSIDE", ("潛在漲幅", "Upside", "漲幅空間")):
            db_updates["潛在漲幅"] = {"number": {"format": "percent"}}
        if not _resolve_field_key(props, "NOTION_PROPERTY_RATING", ("評等變動", "Rating", "評等")):
            db_updates["評等變動"] = {"select": {}}
        if not _resolve_field_key(props, "NOTION_PROPERTY_RISK", ("風險標籤", "Risk Tags", "風險")):
            db_updates["風險標籤"] = {"multi_select": {}}
        if not _resolve_field_key(props, "NOTION_PROPERTY_METHOD", ("評價方法", "Evaluation Method", "估值方式")):
            db_updates["評價方法"] = {"select": {}}
        
        if db_updates:
            database_obj = await anyio.to_thread.run_sync(
                lambda: client.databases.update(database_id=notion_database_id, properties=db_updates)
            )
            props = _props_map(database_obj)
    # ---------------------------

    if is_view:
        title_key = _env_prop("NOTION_PROPERTY_TITLE") or "Name"
    else:
        title_key = _env_prop("NOTION_PROPERTY_TITLE") or _title_property_key(props)
        if not title_key or title_key not in props:
            raise RuntimeError(
                "Notion 資料庫找不到「標題」欄位（type=title）。請確認 NOTION_DATABASE_ID 正確，"
                "或於 .env 設定 NOTION_PROPERTY_TITLE 為實際欄位名稱。"
            )

    properties: dict = {
        title_key: {"title": [{"text": {"content": (title or "")[:2000]}}]},
    }

    # 封裝映射邏輯
    def _add_prop(env_var: str, candidates: tuple[str, ...], value: any, ptype: str = "rich_text"):
        if value is None:
            return
        
        # 解析實際存在的 Key (不論是否為 View，只要 props 有資料就優先檢查)
        key = _resolve_field_key(props, env_var, candidates)
        
        if key:
            # 欄位存在，依型別填入
            if ptype == "multi_select" and isinstance(value, list):
                properties[key] = {"multi_select": [{"name": str(v)[:100]} for v in value]}
            elif ptype == "number" and env_var == "NOTION_PROPERTY_UPSIDE":
                # Percent 欄位需要除以 100
                try:
                    properties[key] = {"number": float(value) / 100.0}
                except (ValueError, TypeError):
                    pass
            else:
                inner = _value_for_property_type(props[key], str(value))
                if inner:
                    properties[key] = inner
        elif is_view:
            # 如果是 View 且 props 為空 (無法獲取 schema)，才進行盲寫
            # 優先取環境變數，否則取 candidates[0] (我們定義的最推薦名稱)
            key = _env_prop(env_var) or candidates[0]
            if key:
                if ptype == "select":
                    properties[key] = {"select": {"name": str(value)[:2000]}}
                elif ptype == "number":
                    try:
                        v = float(value)
                        if env_var == "NOTION_PROPERTY_UPSIDE": v /= 100.0
                        properties[key] = {"number": v}
                    except (ValueError, TypeError):
                        pass
                elif ptype == "multi_select" and isinstance(value, list):
                    properties[key] = {"multi_select": [{"name": str(v)[:100]} for v in value]}
                else:
                    properties[key] = {"rich_text": [{"text": {"content": str(value)[:2000]}}]}

    # 執行所有屬性添加
    _add_prop("NOTION_PROPERTY_CATEGORY", ("類別", "Category", "分類", "category", "產業"), category, "select")
    _add_prop("NOTION_PROPERTY_TICKERS", ("股票代號", "Tickers", "Ticker", "ticker", "代號", "Stock", "股票"), tickers, "rich_text")
    _add_prop("NOTION_PROPERTY_EPS", ("評價基礎數值", "預估EPS", "EPS", "BVPS"), eps, "number")
    _add_prop("NOTION_PROPERTY_PE_LOW", ("評價倍數(低)", "本益比(低)", "PE Low", "PB Low"), pe_low, "number")
    _add_prop("NOTION_PROPERTY_PE_HIGH", ("評價倍數(高)", "本益比(高)", "PE High", "PB High"), pe_high, "number")
    _add_prop("NOTION_PROPERTY_TARGET_LOW", ("目標價(低)", "Target Low", "target_low"), target_low, "number")
    _add_prop("NOTION_PROPERTY_TARGET_HIGH", ("目標價(高)", "Target High", "target_high"), target_high, "number")
    
    # 新增優化欄位添加
    _add_prop("NOTION_PROPERTY_CURRENT_PRICE", ("當前股價", "Current Price", "現價"), current_price, "number")
    _add_prop("NOTION_PROPERTY_UPSIDE", ("潛在漲幅", "Upside", "漲幅空間"), upside_high, "number")
    _add_prop("NOTION_PROPERTY_RATING", ("評等變動", "Rating", "評等"), rating_change, "select")
    _add_prop("NOTION_PROPERTY_RISK", ("風險標籤", "風險", "Risk Tags"), risk_tags, "multi_select")
    _add_prop("NOTION_PROPERTY_METHOD", ("評價方法", "Evaluation Method", "估值方式"), valuation_method, "select")

    page = await anyio.to_thread.run_sync(
        lambda: client.pages.create(
            parent={"database_id": notion_database_id},
            properties=properties,
            children=(
                [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {"rich_text": [{"type": "text", "text": {"content": summary[:1800]}}]},
                    }
                ]
                if summary
                else []
            ),
        )
    )

    return page["id"]
