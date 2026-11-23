"""
app/routers/system.py — Endpoint Kesehatan dan Utilitas Sistem

Endpoint:
- GET  /healthz          -> {"status": "ok"} selalu (liveness probe)
- GET  /readyz           -> {"status": "ready", "db": true/false}
- GET  /api/llm/models   -> daftar model dari provider aktif ([] jika gagal)
- POST /api/llm/test     -> uji konektivitas LLM: {"ok": bool, "latency_ms": int}

Catatan:
- /api/llm/models dan /api/llm/test menggunakan httpx.AsyncClient (async IO).
- X-LLM-API-Key dari header diteruskan ke provider; TIDAK pernah dilog.
- Timeout 3 detik agar UI tidak tergantung lama jika provider mati.
"""

from __future__ import annotations

import time

import httpx
from fastapi import APIRouter, Request

from app.llm.client import PROVIDER_PRESETS
from app.schemas import LLMConfig

router = APIRouter(tags=["system"])

_MODELS_TIMEOUT_S = 3.0  # detik, agar UI responsif
_TEST_TIMEOUT_S = 10.0   # detik, uji prompt mikro


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


@router.get("/api/llm/models")
async def list_llm_models(request: Request) -> dict:
    """Ambil daftar model dari provider aktif.

    Mencoba GET {base_url}/models dengan timeout 3 detik.
    Mengembalikan {"models": [...]} atau {"models": [], "error": "..."}.
    X-LLM-API-Key tidak pernah dilog.
    """
    # Baca config provider dari header custom (opsional)
    provider = request.headers.get("X-LLM-Provider", "ollama")
    api_key = request.headers.get("X-LLM-API-Key", "")
    base_url_header = request.headers.get("X-LLM-Base-Url", "")

    preset = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS["ollama"])
    base_url = base_url_header or preset["base_url"]

    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        async with httpx.AsyncClient(timeout=_MODELS_TIMEOUT_S) as client:
            resp = await client.get(
                f"{base_url.rstrip('/')}/models",
                headers=headers,
            )
        if resp.status_code != 200:
            return {"models": [], "error": f"HTTP {resp.status_code}"}
        data = resp.json()
        # OpenAI format: {"data": [{"id": "..."}, ...]}
        raw_models = data.get("data", data.get("models", []))
        model_ids = [
            m["id"] if isinstance(m, dict) else str(m)
            for m in raw_models
        ]
        return {"models": model_ids}
    except httpx.TimeoutException:
        return {"models": [], "error": "timeout"}
    except Exception as e:
        return {"models": [], "error": f"{type(e).__name__}: {str(e)[:120]}"}


@router.post("/api/llm/test")
async def test_llm_connection(body: LLMConfig, request: Request) -> dict:
    """Uji konektivitas LLM dengan mengirim 1 prompt mikro.

    Mengembalikan {"ok": bool, "latency_ms": int, "error": str|null}.
    X-LLM-API-Key tidak pernah dilog; hanya hidup di memori request ini.
    """
    api_key = request.headers.get("X-LLM-API-Key", "")

    # Provider mock: selalu sukses (untuk tes & demo offline)
    if body.provider == "mock":
        return {"ok": True, "latency_ms": 1, "error": None}

    preset = PROVIDER_PRESETS.get(body.provider, PROVIDER_PRESETS["ollama"])
    base_url = body.base_url or preset["base_url"]
    model = body.model_name or preset.get("model_name", "qwen2.5:7b")

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # Payload minimal — 1 token output
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
        "temperature": 0.0,
    }
    # Qwen thinking off
    if body.provider == "ollama" and model.lower().startswith(("qwen3", "qwen2.5")):
        payload["think"] = False

    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=_TEST_TIMEOUT_S) as client:
            resp = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
        latency_ms = int((time.perf_counter() - t0) * 1000)
        if resp.status_code == 200:
            return {"ok": True, "latency_ms": latency_ms, "error": None}
        return {
            "ok": False,
            "latency_ms": latency_ms,
            "error": f"HTTP {resp.status_code}",
        }
    except httpx.TimeoutException:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        return {"ok": False, "latency_ms": latency_ms, "error": "timeout"}
    except Exception as e:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        return {
            "ok": False,
            "latency_ms": latency_ms,
            "error": f"{type(e).__name__}: {str(e)[:120]}",
        }
