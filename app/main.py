"""
app/main.py — Entry Point FastAPI

Alur kerja:
1. Lifespan event menginisialisasi database SQLite (init_db) dan
   memuat seed scenarios saat startup.
2. StaticFiles melayani folder static/ untuk frontend zero-build.
3. Router modular di-include dari app/routers/.

Jalankan dengan:
    uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db.connection import init_db
from app.engine.dag_repo import load_seed_scenario
from app.routers import scenarios, system, turns


# ── Database path (bisa di-override untuk testing) ───────────

DB_PATH = os.environ.get("WHENYHH_DB_PATH", "whenyhh.db")

# Path ke folder seed JSON
_SEEDS_DIR = os.path.join(os.path.dirname(__file__), "seeds")


# ── Lifespan: init DB + muat seed saat startup ──────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Inisialisasi database, muat 3 seed scenarios, simpan koneksi."""
    import json as _json

    conn = init_db(app.state.db_path)
    app.state.db_conn = conn

    # Muat seed scenarios jika folder ada
    if os.path.isdir(_SEEDS_DIR):
        for fname in sorted(os.listdir(_SEEDS_DIR)):
            if fname.endswith(".json"):
                fpath = os.path.join(_SEEDS_DIR, fname)
                with open(fpath, encoding="utf-8") as f:
                    seed_data = _json.load(f)
                load_seed_scenario(conn, seed_data)

    yield
    conn.close()


# ── Buat instance FastAPI ────────────────────────────────────

app = FastAPI(
    title="Whenyhh.ai",
    description="Workbench visualisasi skenario bercabang dan simulasi keputusan what-if.",
    version="0.1.0",
    lifespan=lifespan,
)

# Simpan db_path di state agar bisa di-override oleh test
app.state.db_path = DB_PATH


# ── Mount static files ───────────────────────────────────────

_static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")


# ── Include Routers ──────────────────────────────────────────

app.include_router(system.router)
app.include_router(scenarios.router)
app.include_router(turns.router)
