from __future__ import annotations

from app.schemas.report import ReportResponse


def test_report_response_excludes_storage_path():
    fields = set(ReportResponse.model_fields.keys())
    assert "storage_path" not in fields
