"""資料庫連線：本機預設 SQLite；Render 等雲端請設定環境變數 DATABASE_URL（PostgreSQL）。"""
import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_ROOT / "data"
DATABASE_PATH = DATA_DIR / "app.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def _resolve_database_url() -> str:
    """
    - 未設定 DATABASE_URL：使用本機 SQLite（backend/data/app.db）。
    - Render / Neon 等：通常為 postgresql://…，改為 SQLAlchemy 非同步驅動 postgresql+asyncpg://。
    """
    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url:
        return f"sqlite+aiosqlite:///{DATABASE_PATH.as_posix()}"
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def _engine_kwargs(db_url: str) -> dict:
    """Render 上 Postgres 通常需要 TLS；asyncpg 需明確 ssl。"""
    if db_url.startswith("sqlite"):
        return {}
    if os.getenv("RENDER", "").lower() != "true":
        return {}
    # 由 Dashboard 貼上的 External URL 幾乎都帶 sslmode=require；避免與 connect_args 衝突可二選一
    if "sslmode=" in db_url.lower():
        return {}
    return {"connect_args": {"ssl": True}}


DATABASE_URL = _resolve_database_url()

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    **_engine_kwargs(DATABASE_URL),
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy Declarative Base。"""


async def get_session():
    """FastAPI Depends 用的 async session 產生器。"""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """建立所有資料表（應用啟動時呼叫）。"""
    import app.models  # noqa: F401 — 註冊 ORM 至 metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
