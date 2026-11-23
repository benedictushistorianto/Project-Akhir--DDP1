"""
app/routers/system.py — Endpoint Kesehatan dan Utilitas Sistem

Endpoint:
- GET /healthz          -> {"status": "ok"} selalu (liveness probe)
- GET /readyz           -> {"status": "ready", "db": true/false}
- GET /api/llm/models   -> (placeholder, akan diimplementasi di Phase 2)
- POST /api/llm/test    -> (placeholder, akan diimplementasi di Phase 2)
"""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["system"])


@router.get("/healthz")
async def healthz() -> dict:
    """Liveness probe: selalu mengembalikan 200 OK."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(request: Request) -> dict:
    """Readiness probe: cek apakah database tersedia."""
    db_ok = False
    try:
        conn = request.app.state.db_conn
        row = conn.execute("SELECT 1").fetchone()
        db_ok = row is not None
    except Exception:
        pass
    return {"status": "ready" if db_ok else "not_ready", "db": db_ok}
