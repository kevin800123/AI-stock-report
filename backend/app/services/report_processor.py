from __future__ import annotations

import json
import os
import re
from datetime import date, datetime
from pathlib import Path

import fitz  # PyMuPDF
import anyio
import yfinance as yf
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Report, Setting
from app.services.notion_service import create_notion_page


class _AiReportSummary(BaseModel):
    category: str = Field(..., description="產業類別(例如: 半導體/金融/電子/生技等)")
    ticker: str = Field(
        ...,
        description="股票欄位請用「台股代號 空格 中文簡稱」，例如：2330 台積電、2344 華邦電；勿用括號格式。",
    )
    stock_code: str | None = Field(
        None,
        description="四位台股代號（數字），若能辨識請填，便於系統與 yfinance 對接。",
    )
    stock_name: str | None = Field(
        None,
        description="公司中文簡稱（不含代號），若能辨識請填，例如：台積電。",
    )
    report_date: str = Field(..., description="報告發布日期 (例如: 2025/12/09 或 2025-12-09)")
    advisor_name: str = Field(..., description="投顧或券商名稱 (例如: 國票、群益、元大等)")
    current_price: float | None = Field(None, description="報告提及的當前股價 (Current Price)")
    valuation_method: str = Field(..., description="評價方法: 'PER' (本益比) 或 'PBR' (股價淨值比)")
    eps_next_year: float | None = Field(None, description="評價基礎數值 (若為 PER 則填 EPS；若為 PBR 則填每股淨值 BVPS)")
    pe_low: float | None = Field(None, description="評價倍數低值 (P/E 或 P/B Ratio)")
    pe_high: float | None = Field(None, description="評價倍數高值 (P/E 或 P/B Ratio)")
    rating_change: str = Field(..., description="評等變動 (只能是: 調升/調降/維持/初次覆蓋)")
    industry_outlook: str = Field(..., description="未來產業展望")
    company_outlook: str = Field(..., description="未來公司展望")
    catalyst_event: str = Field(..., description="事件與日期")
    risk_tags: list[str] = Field(..., description="關鍵風險標籤 (不超過 3 個)")
    core_logic: str = Field(..., description="看多或看空的濃縮重點")


def _get_live_price(ticker_str: str | None) -> float | None:
    """透過 yfinance 獲取台灣股市即時股價"""
    if not ticker_str:
        return None
    
    # 提取 4 位或以上的數字代號
    match = re.search(r"(\d{4,6})", ticker_str)
    if not match:
        return None
    code = match.group(1)
    
    # 台灣市場可能是 .TW (上市) 或 .TWO (上櫃)
    for suffix in [".TW", ".TWO"]:
        try:
            ticker = yf.Ticker(f"{code}{suffix}")
            # 使用 fast_info 獲取最後成交價，這比 history 快得多
            price = ticker.fast_info.last_price
            if price and price > 0:
                return round(float(price), 2)
        except Exception:
            continue
    return None


def _extract_summary_fields(data, live_price: float | None = None) -> tuple[str | None, str | None, str | None, dict]:
    """Gemini 可能回傳 Pydantic 物件（resp.parsed）或 dict（json.loads），統一取出欄位。"""
    if data is None:
        return None, None, None, {"report_date": None}
    if isinstance(data, BaseModel):
        d = data.model_dump()
    elif isinstance(data, dict):
        d = data
    else:
        raise RuntimeError(f"無法解析 Gemini 回傳型別: {type(data)}")
    
    # 取出數值型數據
    eps = d.get("eps_next_year")
    pe_low = d.get("pe_low")
    pe_high = d.get("pe_high")
    method = d.get("valuation_method", "PER")
    
    # 優先使用即時抓取的股價，若無則用報告中的
    curr_price = live_price or d.get("current_price")
    rating_change = d.get("rating_change")
    risk_tags = d.get("risk_tags", [])
    
    # 計算預估股價區間與漲幅
    target_low = d.get("target_low")
    target_high = d.get("target_high")
    upside_low = None
    upside_high = None
    
    # 如果 AI 沒直接給目標價，但有給基礎數值與倍數，則進行計算
    if eps is not None:
        if target_low is None and pe_low is not None:
            try: target_low = round(float(eps) * float(pe_low), 1)
            except: pass
        if target_high is None and pe_high is not None:
            try: target_high = round(float(eps) * float(pe_high), 1)
            except: pass

    # 格式化輸出文字
    if target_low and target_high:
        price_range_str = f"${target_low} ~ ${target_high}"
    elif target_high:
        price_range_str = f"${target_high}"
    elif target_low:
        price_range_str = f"${target_low}"
    else:
        price_range_str = "未提及"

    upside_str = ""
    if curr_price:
        try:
            if target_high:
                upside_high = round((float(target_high) / float(curr_price) - 1) * 100, 1)
            if target_low:
                upside_low = round((float(target_low) / float(curr_price) - 1) * 100, 1)
            
            if upside_low is not None and upside_high is not None:
                upside_str = f" (潛在空間: {upside_low}% ~ {upside_high}%)"
            elif upside_high is not None:
                upside_str = f" (潛在空間: {upside_high}%)"
        except:
            pass
    
    # 根據評價方法調整文字標籤
    eps_label = "每股淨值 (BVPS)" if method == "PBR" else "預估 EPS"
    pe_label = "預估 P/B 區間" if method == "PBR" else "預估 P/E 區間"
    
    eps_str = f"{eps}" if eps is not None else "未提及"
    pe_str = f"{pe_low}x ~ {pe_high}x" if pe_low and pe_high else "未提及"
    curr_price_str = f"${curr_price}" if curr_price else "未提及"
    risk_str = ", ".join(risk_tags) if risk_tags else "無明顯風險"
    
    summary = f"""### 📝 報告基本資訊
- **投顧名稱**：{d.get('advisor_name', '未提及')}
- **報告日期**：{d.get('report_date', '未提及')}
- **評等變動**：**{rating_change}**
- **評價方法**：`{method}`
- **風險標籤**：`{risk_str}`

### 📊 核心評價 (Valuation)
- **當前股價**：{curr_price_str}
- **{eps_label}**：{eps_str}
- **{pe_label}**：{pe_str}
- **🎯 預估目標價**：**{price_range_str}**{upside_str}

### 🔮 展望與分析 (Outlook)
- **未來產業展望**：
  {d.get('industry_outlook', '未提及')}
- **未來公司展望**：
  {d.get('company_outlook', '未提及')}
- **催化劑 / 關鍵事件**：
  {d.get('catalyst_event', '未提及')}

### 💡 核心邏輯 (Core Logic)
{d.get('core_logic', '未提及')}
"""
    
    category = (d.get("category") or "").strip() or None
    tickers = _format_ticker_column(d) or _normalize_tickers(d.get("ticker"))
    report_date_iso = _parse_report_date_iso(d.get("report_date"))

    valuation_data = {
        "eps": eps,
        "pe_low": pe_low,
        "pe_high": pe_high,
        "target_low": target_low,
        "target_high": target_high,
        "current_price": curr_price,
        "upside_high": upside_high,
        "rating_change": rating_change,
        "risk_tags": risk_tags,
        "method": method,
        "report_date": report_date_iso,
    }

    return summary, category, tickers, valuation_data


def _extract_pdf_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    try:
        chunks: list[str] = []
        for page in doc:
            chunks.append(page.get_text("text"))
        return "\n".join(chunks).strip()
    finally:
        doc.close()


async def _get_setting_value(session, key: str) -> str | None:
    row = (await session.execute(select(Setting).where(Setting.key == key))).scalar_one_or_none()
    return row.value if row else None


def _normalize_tickers(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    if isinstance(value, list):
        items = [str(x).strip() for x in value if str(x).strip()]
        return ",".join(items) if items else None
    return str(value).strip() or None


def _format_ticker_display_from_string(raw: str | None) -> str | None:
    """正規化為『代號 名稱』，例如：2330 台積電。"""
    if not raw or not str(raw).strip():
        return None
    s = re.sub(r"\s+", " ", str(raw).strip())
    # 2330 台積電
    m = re.match(r"^(\d{4,6})\s+(.+)$", s)
    if m:
        return f"{m.group(1)} {m.group(2).strip()}"
    # 飛捷(6206)、環宇-KY(4991)
    m = re.match(r"^(.+?)\s*[（(]\s*(\d{4,6})\s*[)）]\s*$", s)
    if m:
        name = re.sub(r"\s+", " ", m.group(1).strip())
        code = m.group(2)
        return f"{code} {name}"
    # 8299 TT Phison
    m = re.match(r"^(\d{4,6})\s+(?:TT|T\.?T\.?)\s+(.+)$", s, re.I)
    if m:
        return f"{m.group(1)} {m.group(2).strip()}"
    # 僅數字代號
    m = re.match(r"^(\d{4,6})$", s)
    if m:
        return m.group(1)
    return s


def _format_ticker_column(d: dict) -> str | None:
    code = (d.get("stock_code") or "").strip()
    name = (d.get("stock_name") or "").strip()
    if code:
        code_clean = "".join(ch for ch in code if ch.isdigit())[:6]
        if len(code_clean) >= 4 and name:
            return f"{code_clean} {name}"
        if len(code_clean) >= 4:
            rest = _format_ticker_display_from_string(d.get("ticker"))
            if rest and rest.startswith(code_clean):
                return rest
            return code_clean
    return _format_ticker_display_from_string(d.get("ticker"))


def _parse_report_date_iso(s: str | None) -> str | None:
    """轉成 Notion date 用的 YYYY-MM-DD。"""
    if not s or not str(s).strip():
        return None
    s = str(s).strip()
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(s[:10], fmt).date().isoformat()
        except ValueError:
            continue
    if re.fullmatch(r"\d{8}", s):
        try:
            return datetime.strptime(s, "%Y%m%d").date().isoformat()
        except ValueError:
            pass
    m = re.match(r"(\d{4})\s*[/.\-年]\s*(\d{1,2})\s*[/.\-月]\s*(\d{1,2})", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            pass
    m = re.match(r"^(\d{4})[/.\-](\d{1,2})[/.\-](\d{1,2})$", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            pass
    return None


async def process_report_file(report_id: int) -> None:
    """
    背景處理：PDF 解析 → OpenAI 摘要（強制 JSON）→ 寫入 Notion → 更新資料庫狀態。
    """
    async with AsyncSessionLocal() as session:
        report = (await session.execute(select(Report).where(Report.id == report_id))).scalar_one_or_none()
        if not report:
            return

        try:
            report.status = "parsing"
            report.error_message = None
            await session.commit()

            pdf_path = report.storage_path
            if not pdf_path or not Path(pdf_path).exists():
                raise FileNotFoundError(f"找不到檔案: {pdf_path}")

            text_content = _extract_pdf_text(pdf_path)
            if not text_content:
                raise RuntimeError("PDF 無法解析出任何文字")

            report.status = "summarizing"
            await session.commit()

            # 支援 .env / 環境變數
            backend_root = Path(__file__).resolve().parents[2]
            load_dotenv(dotenv_path=backend_root / ".env", override=True)
            gemini_api_key = (
                await _get_setting_value(session, "gemini_api_key")
                or os.getenv("GEMINI_API_KEY")
                or os.getenv("GOOGLE_API_KEY")
            )
            if not gemini_api_key:
                raise RuntimeError("缺少 Gemini API Key（請先設定 GEMINI_API_KEY 或在 settings 存入 gemini_api_key）")

            system_prompt = (
                "你是一個精準的金融 AI 助理。請從 PDF 文字中萃取數據並輸出 JSON。請遵循以下『精準模式』：\n"
                "1. **目標價 (Target Price)**：優先尋找『目標價』、『TP』、『Target』。這是你的核心參考點。\n"
                "2. **預估數據 (Forecast Year)**：報告中若有『年度 EPS 預估表』，請『強行鎖定』最遠的預估年度（如 2026F 或 2026 預估）。\n"
                "3. **評價邏輯 (Logic Matching)**：\n"
                "   - 如果分析師明確說是用 PBR 估值，基礎數值 (eps_next_year) 請填入每股淨值 (BVPS)，倍數填入 P/B Ratio。\n"
                "   - 如果是用 PER 估值，基礎數值請填入預估 EPS，倍數填入 P/E Ratio。\n"
                "   - **關鍵**：倍數必須選取用來計算『目標價』的那一組（通常在報告開頭或評價單元），而非歷史平均區間。\n"
                "4. **現價校對**：抓取報告中的收盤價，若有即時股價則由系統覆蓋。\n"
                "5. **股票顯示**：`ticker` 必須為「台股代號 空格 中文簡稱」，例如 `2330 台積電`；並盡量填 `stock_code`（如 2330）與 `stock_name`（如 台積電）。\n"
                "6. **報告日期**：`report_date` 填報告日，建議 YYYY/MM/DD 或 YYYY-MM-DD。\n"
                "7. ** JSON 欄位說明**：\n"
                "   - `eps_next_year`: 填入評價用的基礎數值 (EPS 或 BVPS)。\n"
                "   - `pe_low` / `pe_high`: 填入評價用的倍數區間（若只有單一倍數，填在 high，low 設為 null）。\n"
                "   - `target_low` / `target_high`: 直接抓取報告中的目標價數字（若只有單一目標價，填在 high）。"
            )
            user_prompt = f"以下為 PDF 解析文字，請依需求輸出 JSON。\n\n{text_content[:20000]}"

            def _call_gemini():
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=gemini_api_key)
                try:
                    resp = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[system_prompt, user_prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=_AiReportSummary,
                        ),
                    )
                    if getattr(resp, "parsed", None) is not None:
                        return resp.parsed
                    return json.loads(resp.text or "{}")
                finally:
                    try:
                        client.close()
                    except Exception:
                        pass

            data = await anyio.to_thread.run_sync(_call_gemini)
            
            # 先提取代號以便抓取即時股價（僅需數字代號）
            if isinstance(data, BaseModel):
                dump = data.model_dump()
            else:
                dump = data if isinstance(data, dict) else {}
            raw_ticker = dump.get("ticker")
            code_hint = (dump.get("stock_code") or "").strip()
            tickers_for_price = None
            if code_hint:
                digits = "".join(ch for ch in code_hint if ch.isdigit())
                if len(digits) >= 4:
                    tickers_for_price = digits
            if not tickers_for_price:
                tickers_for_price = _normalize_tickers(raw_ticker)

            # --- [新增] 獲取即時股價 ---
            live_price = await anyio.to_thread.run_sync(_get_live_price, tickers_for_price)
            
            summary, category, tickers, val_data = _extract_summary_fields(data, live_price=live_price)

            report.summary = summary
            report.category = category
            report.stock_tickers = tickers

            report.status = "writing_notion"
            await session.commit()

            # 寫入 Notion
            notion_page_id = await create_notion_page(
                db=session,
                title=report.original_filename,
                category=category,
                summary=summary,
                tickers=tickers,
                report_date_iso=val_data.get("report_date"),
                eps=val_data.get("eps"),
                pe_low=val_data.get("pe_low"),
                pe_high=val_data.get("pe_high"),
                target_low=val_data.get("target_low"),
                target_high=val_data.get("target_high"),
                current_price=val_data.get("current_price"),
                upside_high=val_data.get("upside_high"),
                rating_change=val_data.get("rating_change"),
                risk_tags=val_data.get("risk_tags"),
                valuation_method=val_data.get("method"),
            )

            report.notion_page_id = notion_page_id
            report.status = "completed"
            await session.commit()

        except Exception as e:
            report.status = "error"
            report.error_message = str(e)
            await session.commit()

