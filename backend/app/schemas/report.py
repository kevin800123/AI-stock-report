"""報告相關 Pydantic Schema。

API Response 僅反映資料表欄位；機密請勿存入 Report（Notion Secret 應仅存於 Setting）。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReportBase(BaseModel):
    """報告共通欄位。"""

    original_filename: str = Field(..., max_length=512)
    storage_path: str = Field(..., max_length=1024)
    status: str = Field(default="uploading", max_length=64)
    summary: str | None = None
    category: str | None = Field(None, max_length=128)
    stock_tickers: str | None = Field(None, max_length=512)
    notion_page_id: str | None = Field(None, max_length=128)
    error_message: str | None = None


class ReportCreate(BaseModel):
    """建立報告紀錄（上傳後寫入）。"""

    original_filename: str = Field(..., max_length=512)
    storage_path: str = Field(..., max_length=1024)
    status: str = Field(default="uploading", max_length=64)


class ReportUpdate(BaseModel):
    """更新報告（部分欄位可選）。"""

    original_filename: str | None = Field(None, max_length=512)
    storage_path: str | None = Field(None, max_length=1024)
    status: str | None = Field(None, max_length=64)
    summary: str | None = None
    category: str | None = Field(None, max_length=128)
    stock_tickers: str | None = Field(None, max_length=512)
    notion_page_id: str | None = Field(None, max_length=128)
    error_message: str | None = None


class ReportResponse(BaseModel):
    """報告 API 回應（不含任何 Notion Secret；notion_page_id 為公開頁面識別）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    storage_path: str
    status: str
    summary: str | None
    category: str | None
    stock_tickers: str | None
    notion_page_id: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
