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
from app.routers import system


# ── Database path (bisa di-override untuk testing) ───────────

DB_PATH = os.environ.get("WHENYHH_DB_PATH", "whenyhh.db")


# ── Lifespan: init DB saat startup ───────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Inisialisasi database dan simpan koneksi di app.state."""
    conn = init_db(app.state.db_path)
    app.state.db_conn = conn
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
