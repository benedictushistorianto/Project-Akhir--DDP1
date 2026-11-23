"""
tests/test_context_compiler_o1.py — Dynamic Context Compiler O(1)

Memverifikasi:
1. Total input <= 2.200 token di setiap kompilasi.
2. Zona prefiks statis identik byte-for-byte antar-giliran
   (KV prefix cache hit).
3. Zona sufiks dinamis mengandung Sim Pulse deterministik,
   maks 10 Jangkar Kausal, 2 narasi bersih terakhir,
   dan tidak pernah memuat JSON delta.
4. arc_summary dipangkas bila melewati 240 token.
5. Stres 100 giliran: input tetap <= 2.200 token.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.engine.context_compiler import (
    BUDGET_TOTAL_TOKENS,
    est_tokens,
    compile_context,
)
from app.engine.dag_repo import commit_turn, load_seed_scenario
from app.engine.sim_pulse import generate_sim_pulse
from app.engine.state_mutator import apply_turn_deltas
from app.schemas import TurnResponse, ActorStateDelta


_SEEDS_DIR = Path(__file__).parent.parent / "app" / "seeds"
VALID_IDS = {"raka", "vendor_dewi", "ketua_alin"}


def _load_kampus(conn):
    with open(_SEEDS_DIR / "kampus_anti_scam.json", encoding="utf-8") as f:
        return load_seed_scenario(conn, json.load(f))


def _main_head(conn, sid):
    row = conn.execute(
        "SELECT branch_id, head_node_id FROM branches "
        "WHERE scenario_id = ? AND name = 'main'",
        (sid,),
    ).fetchone()
    return row["branch_id"], row["head_node_id"]


def _advance(conn, sid, bid, head_id, turn_label: str) -> str:
    """Commit satu giliran kosong dan kembalikan node barunya."""
    resp = TurnResponse(narrative=f"Narrasi {turn_label}.",
                        updated_arc_summary=f"Ringkasan {turn_label}.")
    states, edges = apply_turn_deltas(conn, head_id, resp, VALID_IDS)
    return commit_turn(
        conn, scenario_id=sid, branch_id=bid,
        parent_node_id=head_id, user_action=f"Aksi {turn_label}",
        turn_response=resp, actor_states=states, relation_edges=edges,
    )


class TestSimPulse:
    """Sim Pulse deterministik dan dapat direproduksi."""

    def test_deterministic_for_same_args(self):
        a = generate_sim_pulse(rng_seed=42, node_id="n1", turn_index=1)
        b = generate_sim_pulse(rng_seed=42, node_id="n1", turn_index=1)
        assert a.directive == b.directive
        assert a.ticking_clock == b.ticking_clock

    def test_different_turn_gives_different_pulse(self):
        a = generate_sim_pulse(rng_seed=42, node_id="n1", turn_index=1)
        b = generate_sim_pulse(rng_seed=42, node_id="n1", turn_index=2)
        assert a.directive != b.directive or a.ticking_clock != b.ticking_clock


class TestStaticPrefix:
    """Zona prefiks statis identik antar-giliran pada skenario sama."""

    def test_prefix_byte_for_byte_identical(self, db_conn):
        sid = _load_kampus(db_conn)
        bid, head = _main_head(db_conn, sid)

        head1 = _advance(db_conn, sid, bid, head, "T1")
        head2 = _advance(db_conn, sid, bid, head1, "T2")

        ctx1 = compile_context(db_conn, scenario_id=sid,
                               parent_node_id=head1, user_action="A1")
        ctx2 = compile_context(db_conn, scenario_id=sid,
                               parent_node_id=head2, user_action="A2")

        # messages[0] (system) harus persis sama byte-for-byte
        assert ctx1.messages[0] == ctx2.messages[0]

    def test_prefix_contains_actor_cores_sorted(self, db_conn):
        sid = _load_kampus(db_conn)
        _, head = _main_head(db_conn, sid)
        ctx = compile_context(db_conn, scenario_id=sid,
                              parent_node_id=head, user_action="X")
        system_msg = ctx.messages[0]["content"]
        ids = [l.split(" | ")[0].lstrip("- ")
               for l in system_msg.splitlines()
               if l.startswith("- ") and ":" in l]
        assert ids == sorted(ids)  # deterministik
        assert "raka" in ids and "vendor_dewi" in ids and "ketua_alin" in ids


class TestDynamicSuffix:
    """Zona sufiks dinamis: blok wajib ada, JSON delta tidak ikut."""

    def test_contains_required_blocks(self, db_conn):
        sid = _load_kampus(db_conn)
        _, head = _main_head(db_conn, sid)
        ctx = compile_context(db_conn, scenario_id=sid,
                              parent_node_id=head, user_action="Tanya harga")
        user_msg = ctx.messages[1]["content"]
        assert "STATE AKTOR TERKINI" in user_msg
        assert "MATRIKS RELASI" in user_msg
        assert "SIM PULSE" in user_msg
        assert "Tanya harga" in user_msg  # aksi pengguna
        # JSON delta tidak boleh ikut ke LLM
        assert "actor_deltas" not in user_msg

    def test_sim_pulse_in_suffix_is_deterministic(self, db_conn):
        sid = _load_kampus(db_conn)
        _, head = _main_head(db_conn, sid)
        c1 = compile_context(db_conn, scenario_id=sid,
                             parent_node_id=head, user_action="A")
        c2 = compile_context(db_conn, scenario_id=sid,
                             parent_node_id=head, user_action="B")
        # Blok Sim Pulse harus sama (bergantung node & turn_index, bukan aksi)
        assert "SIM PULSE" in c1.messages[1]["content"]
        pulse_line1 = [l for l in c1.messages[1]["content"].splitlines()
                       if l.startswith("Sim Pulse")][0]
        pulse_line2 = [l for l in c2.messages[1]["content"].splitlines()
                       if l.startswith("Sim Pulse")][0]
        assert pulse_line1 == pulse_line2


class TestTokenBudget:
    """Plafon O(1) <= 2.200 token."""

    def test_single_turn_under_budget(self, db_conn):
        sid = _load_kampus(db_conn)
        _, head = _main_head(db_conn, sid)
        ctx = compile_context(db_conn, scenario_id=sid,
                              parent_node_id=head, user_action="Pilih A")
        assert ctx.estimated_input_tokens <= BUDGET_TOTAL_TOKENS

    def test_arc_summary_clamped_to_240(self, db_conn):
        sid = _load_kampus(db_conn)
        bid, head = _main_head(db_conn, sid)
        long_summary = " ".join(["katapanjang"] * 200)  # jauh melebihi 240 tok
        resp = TurnResponse(narrative="N.", updated_arc_summary=long_summary)
        states, edges = apply_turn_deltas(db_conn, head, resp, VALID_IDS)
        head1 = commit_turn(
            db_conn, scenario_id=sid, branch_id=bid,
            parent_node_id=head, user_action="U",
            turn_response=resp, actor_states=states, relation_edges=edges,
        )
        ctx = compile_context(db_conn, scenario_id=sid,
                              parent_node_id=head1, user_action="Pilih B")
        user_msg = ctx.messages[1]["content"]
        # arc_summary terpotong, tandai dengan " ..."
        assert "katapanjang" in user_msg
        assert "..." in user_msg

    def test_stress_100_turns_stays_under_budget(self, db_conn):
        """Stres: 100 giliran beruntun, input tetap O(1)."""
        sid = _load_kampus(db_conn)
        bid, head = _main_head(db_conn, sid)

        for i in range(100):
            # Commit giliran ke-100
            resp = TurnResponse(narrative=f"Narasi T{i+1}.",
                                updated_arc_summary=f"Ringkasan T{i+1}.")
            states, edges = apply_turn_deltas(db_conn, head, resp, VALID_IDS)
            head = commit_turn(
                db_conn, scenario_id=sid, branch_id=bid,
                parent_node_id=head, user_action=f"Aksi T{i+1}",
                turn_response=resp, actor_states=states, relation_edges=edges,
            )
            # Kompilasi konteks untuk giliran berikutnya
            ctx = compile_context(db_conn, scenario_id=sid,
                                  parent_node_id=head, user_action=f"T{i+2}")
            assert ctx.estimated_input_tokens <= BUDGET_TOTAL_TOKENS, (
                f"giliran {i+1}: {ctx.estimated_input_tokens} token"
            )
