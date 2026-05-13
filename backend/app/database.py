"""SQLite 資料庫連線（檔案位於 backend/data/app.db）。"""
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_ROOT / "data"
DATABASE_PATH = DATA_DIR / "app.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH.as_posix()}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
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
