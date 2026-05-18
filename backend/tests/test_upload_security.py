from __future__ import annotations

from io import BytesIO


def test_upload_requires_api_key(client):
    files = {"file": ("test.pdf", BytesIO(b"%PDF-1.4 minimal"), "application/pdf")}
    r = client.post("/reports/upload", files=files)
    assert r.status_code == 401


def test_upload_rejects_non_pdf(client, upload_headers):
    files = {"file": ("fake.pdf", BytesIO(b"not a pdf"), "application/pdf")}
    r = client.post("/reports/upload", files=files, headers=upload_headers)
    assert r.status_code == 400


def test_upload_rejects_oversized_file(client, upload_headers):
    big = b"%PDF-1.4\n" + b"x" * (10 * 1024 * 1024)
    files = {"file": ("big.pdf", BytesIO(big), "application/pdf")}
    r = client.post("/reports/upload", files=files, headers=upload_headers)
    assert r.status_code == 413
