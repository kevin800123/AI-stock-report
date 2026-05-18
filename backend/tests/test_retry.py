from __future__ import annotations

import pytest

from app.utils.retry import call_with_sync_retry, is_transient_error


def test_is_transient_error_connection():
    assert is_transient_error(ConnectionError("network"))


def test_is_transient_error_not_retry_runtime():
    assert not is_transient_error(RuntimeError("missing key"))


def test_call_with_sync_retry_succeeds_after_transient_failures():
    attempts = {"n": 0}

    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise ConnectionError("temporary")
        return "ok"

    assert call_with_sync_retry(flaky) == "ok"
    assert attempts["n"] == 3


def test_call_with_sync_retry_does_not_retry_runtime_error():
    attempts = {"n": 0}

    def fail_fast():
        attempts["n"] += 1
        raise ValueError("bad input")

    with pytest.raises(ValueError):
        call_with_sync_retry(fail_fast)
    assert attempts["n"] == 1
