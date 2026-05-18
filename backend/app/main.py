from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import Base, engine
from app.deps.security import limiter
from app.routers.reports import router as reports_router
from app.routers.settings import router as settings_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 啟動時自動建表（SQLite 或 DATABASE_URL 指定的 PostgreSQL）
    import app.models  # noqa: F401 — 註冊 ORM 至 metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="投顧報告 AI 分析助理",
    description="使用 AI 自動分析投顧報告並彙整重點。",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"^http://127\.0\.0\.1:\d+$|^http://localhost:\d+$|^https://[a-zA-Z0-9_.-]+\.github\.io$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports_router)
app.include_router(settings_router)


@app.get("/")
async def root():
    return {"message": "投顧報告 AI 分析助理 API", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
