"""
app/db/connection.py — SQLite Connection Factory

Fungsi utama:
- get_connection(db_path): Membuat koneksi SQLite dengan PRAGMA wajib
  (WAL, synchronous=NORMAL, busy_timeout=5000, foreign_keys=ON, cache_size=-16000).
- init_db(db_path): Menjalankan schema.sql untuk membuat tabel jika belum ada.
- write_transaction(conn): Context manager yang membungkus blok tulis
  dengan BEGIN IMMEDIATE agar aman dari race condition.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

# Path ke file schema.sql relatif terhadap modul ini
_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection(db_path: str = "whenyhh.db") -> sqlite3.Connection:
    """Buat koneksi SQLite baru dengan PRAGMA wajib proyek.

    - check_same_thread=False agar bisa dipakai di async FastAPI.
    - Row factory diset ke sqlite3.Row supaya hasil kueri bisa diakses
      seperti dict (row["column_name"]).
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    # PRAGMA wajib sesuai TechDesign
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA cache_size=-16000")

    return conn


def init_db(db_path: str = "whenyhh.db") -> sqlite3.Connection:
    """Inisialisasi database: buat koneksi + jalankan schema.sql.

    Mengembalikan koneksi yang sudah siap pakai.
    """
    conn = get_connection(db_path)
    schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    return conn


@contextmanager
def write_transaction(conn: sqlite3.Connection) -> Generator[sqlite3.Connection, None, None]:
    """Context manager untuk transaksi tulis dengan BEGIN IMMEDIATE.

    Penggunaan:
        with write_transaction(conn) as c:
            c.execute("INSERT INTO ...")
    
    Otomatis COMMIT jika sukses, ROLLBACK jika ada exception.
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
