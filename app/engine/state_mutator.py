"""
app/engine/state_mutator.py — Penerapan Delta ke State

Fungsi utama:
- apply_turn_deltas(conn, parent_node_id, turn_response, valid_actor_ids):
  Membaca state induk dari SQLite, menerapkan delta dari TurnResponse,
  melakukan clamping deterministik, dan mengembalikan list dict
  actor_states dan relation_edges yang siap disisipkan ke node baru.

Aturan penting:
1. actor_id yang tidak terdaftar di valid_actor_ids DIABAIKAN
   (anti-halusinasi LLM) tanpa melempar error.
2. Jika delta field bernilai None, field lama dipertahankan.
3. Clamping sudah dilakukan oleh Pydantic @field_validator di schemas.py,
   tapi kita tetap clamp ulang di sini sebagai safety net.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from app.schemas import TurnResponse


# ── Clamp Helpers ────────────────────────────────────────────

def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


# ── Apply Deltas ─────────────────────────────────────────────

def apply_turn_deltas(
    conn: sqlite3.Connection,
    parent_node_id: str,
    turn_response: TurnResponse,
    valid_actor_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Terapkan delta dari TurnResponse ke state induk.

    1. Baca actor_states induk dari SQLite.
    2. Untuk setiap ActorStateDelta, jika actor_id valid, terapkan
       perubahan (atau pertahankan nilai lama jika delta None).
    3. Baca relation_edges induk dari SQLite.
    4. Untuk setiap RelationDelta, jika kedua actor_id valid, terapkan.
    5. Clamp semua nilai akhir.

    Return: (new_actor_states, new_relation_edges) sebagai list[dict].
    """

    # ── 1. Baca state induk ──────────────────────────────────
    parent_states = conn.execute(
        "SELECT * FROM actor_states WHERE node_id = ?",
        (parent_node_id,),
    ).fetchall()

    # Bangun dict {actor_id: {field: value}}
    state_map: dict[str, dict[str, Any]] = {}
    for s in parent_states:
        state_map[s["actor_id"]] = {
            "actor_id": s["actor_id"],
            "mood": s["mood"],
            "energy": s["energy"],
            "safety": s["safety"],
            "social": s["social"],
            "esteem": s["esteem"],
            "location": s["location"],
            "ticking_clock": s["ticking_clock"],
        }

    # ── 2. Terapkan actor deltas ─────────────────────────────
    for delta in turn_response.actor_deltas:
        if delta.actor_id not in valid_actor_ids:
            # Anti-halusinasi: abaikan ID yang tidak terdaftar
            continue

        if delta.actor_id not in state_map:
            # Aktor valid tapi belum punya state di parent
            # (seharusnya tidak terjadi, tapi defensif)
            state_map[delta.actor_id] = {
                "actor_id": delta.actor_id,
                "mood": 2, "energy": 3, "safety": 3,
                "social": 3, "esteem": 3,
                "location": "", "ticking_clock": "",
            }

        current = state_map[delta.actor_id]
        if delta.mood is not None:
            current["mood"] = _clamp(delta.mood, 1, 3)
        if delta.energy is not None:
            current["energy"] = _clamp(delta.energy, 1, 5)
        if delta.safety is not None:
            current["safety"] = _clamp(delta.safety, 1, 5)
        if delta.social is not None:
            current["social"] = _clamp(delta.social, 1, 5)
        if delta.esteem is not None:
            current["esteem"] = _clamp(delta.esteem, 1, 5)
        if delta.location is not None:
            current["location"] = delta.location
        if delta.ticking_clock is not None:
            current["ticking_clock"] = delta.ticking_clock

    new_actor_states = list(state_map.values())

    # ── 3. Baca relasi induk ─────────────────────────────────
    parent_edges = conn.execute(
        "SELECT * FROM relation_edges WHERE node_id = ?",
        (parent_node_id,),
    ).fetchall()

    # Bangun dict {(source, target): {field: value}}
    edge_map: dict[tuple[str, str], dict[str, Any]] = {}
    for e in parent_edges:
        key = (e["source_actor_id"], e["target_actor_id"])
        edge_map[key] = {
            "source_actor_id": e["source_actor_id"],
            "target_actor_id": e["target_actor_id"],
            "trust": e["trust"],
            "affinity": e["affinity"],
            "tension": e["tension"],
            "bond_event": e["bond_event"],
        }

    # ── 4. Terapkan relation deltas ──────────────────────────
    for delta in turn_response.relation_deltas:
        # Anti-halusinasi: abaikan jika salah satu ID tidak valid
        if (delta.source_actor_id not in valid_actor_ids
                or delta.target_actor_id not in valid_actor_ids):
            continue

        key = (delta.source_actor_id, delta.target_actor_id)
        if key not in edge_map:
            # Relasi baru yang belum ada di parent
            edge_map[key] = {
                "source_actor_id": delta.source_actor_id,
                "target_actor_id": delta.target_actor_id,
                "trust": 0, "affinity": 0, "tension": 0,
                "bond_event": "",
            }

        current = edge_map[key]
        if delta.trust is not None:
            current["trust"] = _clamp(delta.trust, -5, 5)
        if delta.affinity is not None:
            current["affinity"] = _clamp(delta.affinity, -5, 5)
        if delta.tension is not None:
            current["tension"] = _clamp(delta.tension, 0, 5)
        if delta.bond_event is not None:
            current["bond_event"] = delta.bond_event

    new_relation_edges = list(edge_map.values())

    return new_actor_states, new_relation_edges
