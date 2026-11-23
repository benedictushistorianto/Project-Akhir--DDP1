"""
tests/test_api_contracts.py — Suite #5: Kontrak API Endpoint

Menguji bahwa:
1. /healthz mengembalikan 200.
2. /readyz mengembalikan 200 dengan db: true.
3. Endpoint yang belum ada mengembalikan 404.
"""

from __future__ import annotations


class TestHealthEndpoints:
    """Endpoint kesehatan berfungsi."""

    def test_healthz_ok(self, client):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_readyz_with_db(self, client):
        resp = client.get("/readyz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["db"] is True
        assert data["status"] == "ready"


class TestNotFound:
    """Route yang tidak terdaftar mengembalikan 404."""

    def test_unknown_route_404(self, client):
        resp = client.get("/api/nonexistent")
        assert resp.status_code == 404
