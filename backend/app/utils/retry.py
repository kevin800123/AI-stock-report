from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TypeVar

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

_TRANSIENT_TYPES = (
    ConnectionError,
    TimeoutError,
    OSError,
    BrokenPipeError,
)


def is_transient_error(exc: BaseException) -> bool:
    if isinstance(exc, _TRANSIENT_TYPES):
        return True
    status = getattr(exc, "status_code", None)
    if status is None:
        response = getattr(exc, "response", None)
        status = getattr(response, "status_code", None)
    if status in (429, 500, 502, 503, 504):
        return True
    name = type(exc).__name__
    if "Timeout" in name or "Connection" in name or "ServiceUnavailable" in name:
        return True
    return False


def call_with_sync_retry(fn: Callable[[], T]) -> T:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception(is_transient_error),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _wrapped() -> T:
        return fn()

    return _wrapped()
