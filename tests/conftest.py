"""
tests/conftest.py — Fixture Bersama untuk Seluruh Suite Pytest

Menyediakan:
- db_path: Path temporer ke file SQLite (pakai tmp_path pytest).
- db_conn: Koneksi SQLite yang sudah diinisialisasi dengan schema.
- test_app: Instance FastAPI yang menunjuk ke database temporer.
- client: TestClient untuk integrasi test endpoint HTTP.

Semua test berjalan tanpa GPU, tanpa API key, dan tanpa jaringan.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.db.connection import init_db
from app.main import app


@pytest.fixture()
def db_path(tmp_path) -> str:
    """Path file database SQLite di folder temporer."""
    return str(tmp_path / "test_whenyhh.db")


@pytest.fixture()
def db_conn(db_path):
    """Koneksi SQLite yang sudah diinisialisasi dengan seluruh tabel."""
    conn = init_db(db_path)
    yield conn
    conn.close()


@pytest.fixture()
def test_app(db_path):
    """Instance FastAPI dengan database temporer."""
    app.state.db_path = db_path
    return app


@pytest.fixture()
def client(test_app):
    """TestClient FastAPI untuk menguji endpoint HTTP."""
    with TestClient(test_app) as c:
        yield c
