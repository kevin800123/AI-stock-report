from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_backend_root = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=_backend_root / ".env", override=False)

_DEFAULT_MAX_BYTES = 10 * 1024 * 1024


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    return int(raw)


UPLOAD_MAX_BYTES = _env_int("UPLOAD_MAX_BYTES", _DEFAULT_MAX_BYTES)
UPLOAD_API_KEY = (os.getenv("UPLOAD_API_KEY") or "").strip()
REQUIRE_UPLOAD_API_KEY = _env_bool("REQUIRE_UPLOAD_API_KEY", False)
UPLOAD_RATE_LIMIT = (os.getenv("UPLOAD_RATE_LIMIT") or "5/minute").strip() or "5/minute"
