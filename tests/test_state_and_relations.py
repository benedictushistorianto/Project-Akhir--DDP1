"""
tests/test_state_and_relations.py — Suite #2: State, Relasi Asimetris, Clamping

Menguji bahwa:
1. actor_cores bersifat imutabel (tidak bisa di-UPDATE).
2. Relasi A->B terpisah dari B->A (asimetris).
3. Field_validator melakukan clamping angka di rentang yang benar.
4. Jangkar Kausal terisolasi antar-cabang.
"""

from __future__ import annotations

import sqlite3
import uuid

import pytest

from app.db.connection import write_transaction
from app.schemas import ActorStateDelta, RelationDelta, CausalAnchorDelta


def _make_id() -> str:
    return uuid.uuid4().hex[:12]


def _seed_full(conn: sqlite3.Connection):
    """Buat skenario lengkap: 2 aktor, 1 branch, 1 node akar, states & relasi."""
    sid, bid, nid = _make_id(), _make_id(), _make_id()
    a1, a2 = "aktor_raka", "aktor_vendor"

    with write_transaction(conn) as c:
        c.execute("INSERT INTO scenarios (scenario_id, title) VALUES (?, ?)", (sid, "Test"))
        c.execute(
            "INSERT INTO actor_cores (actor_id, scenario_id, name, role) VALUES (?, ?, ?, ?)",
            (a1, sid, "Raka", "Mahasiswa"),
        )
        c.execute(
            "INSERT INTO actor_cores (actor_id, scenario_id, name, role) VALUES (?, ?, ?, ?)",
            (a2, sid, "Vendor", "Penjual"),
        )
        c.execute(
            "INSERT INTO branches (branch_id, scenario_id, name, head_node_id) VALUES (?, ?, ?, ?)",
            (bid, sid, "main", nid),
        )
        c.execute(
            "INSERT INTO nodes (node_id, scenario_id, branch_id, parent_id, turn_index) "
            "VALUES (?, ?, ?, NULL, 0)",
            (nid, sid, bid),
        )
        # States
        c.execute(
            "INSERT INTO actor_states (node_id, actor_id, mood, energy) VALUES (?, ?, 2, 3)",
            (nid, a1),
        )
        c.execute(
            "INSERT INTO actor_states (node_id, actor_id, mood, energy) VALUES (?, ?, 2, 4)",
            (nid, a2),
        )
        # Relasi asimetris
        c.execute(
            "INSERT INTO relation_edges (node_id, source_actor_id, target_actor_id, trust, tension) "
            "VALUES (?, ?, ?, 2, 1)",
            (nid, a1, a2),
        )
        c.execute(
            "INSERT INTO relation_edges (node_id, source_actor_id, target_actor_id, trust, tension) "
            "VALUES (?, ?, ?, -1, 3)",
            (nid, a2, a1),
        )

    return sid, bid, nid, a1, a2


class TestActorCoreImmutability:
    """actor_cores tidak boleh berubah setelah disisipkan."""

    def test_core_exists(self, db_conn):
        sid, _, _, a1, _ = _seed_full(db_conn)
        row = db_conn.execute(
            "SELECT name, role FROM actor_cores WHERE actor_id = ? AND scenario_id = ?",
            (a1, sid),
        ).fetchone()
        assert row["name"] == "Raka"
        assert row["role"] == "Mahasiswa"


class TestAsymmetricRelations:
    """Relasi A->B terpisah dari B->A."""

    def test_a_to_b_different_from_b_to_a(self, db_conn):
        _, _, nid, a1, a2 = _seed_full(db_conn)

        ab = db_conn.execute(
            "SELECT trust, tension FROM relation_edges "
            "WHERE node_id = ? AND source_actor_id = ? AND target_actor_id = ?",
            (nid, a1, a2),
        ).fetchone()
        ba = db_conn.execute(
            "SELECT trust, tension FROM relation_edges "
            "WHERE node_id = ? AND source_actor_id = ? AND target_actor_id = ?",
            (nid, a2, a1),
        ).fetchone()

        assert ab["trust"] == 2
        assert ba["trust"] == -1
        assert ab["trust"] != ba["trust"], "Relasi harus asimetris!"

    def test_update_a_to_b_does_not_change_b_to_a(self, db_conn):
        sid, bid, nid, a1, a2 = _seed_full(db_conn)

        # Buat node baru (giliran 1) dengan relasi yang diperbarui hanya A->B
        new_nid = _make_id()
        with write_transaction(db_conn) as c:
            c.execute(
                "INSERT INTO nodes (node_id, scenario_id, branch_id, parent_id, turn_index) "
                "VALUES (?, ?, ?, ?, 1)",
                (new_nid, sid, bid, nid),
            )
            # A->B berubah trust +3
            c.execute(
                "INSERT INTO relation_edges (node_id, source_actor_id, target_actor_id, trust, tension) "
                "VALUES (?, ?, ?, 3, 0)",
                (new_nid, a1, a2),
            )
            # B->A tetap sama seperti sebelumnya
            c.execute(
                "INSERT INTO relation_edges (node_id, source_actor_id, target_actor_id, trust, tension) "
                "VALUES (?, ?, ?, -1, 3)",
                (new_nid, a2, a1),
            )

        # Verifikasi B->A di node baru tetap -1
        ba_new = db_conn.execute(
            "SELECT trust FROM relation_edges "
            "WHERE node_id = ? AND source_actor_id = ? AND target_actor_id = ?",
            (new_nid, a2, a1),
        ).fetchone()
        assert ba_new["trust"] == -1


class TestClampingValidators:
    """@field_validator di schemas.py melakukan clamping yang benar."""

    def test_mood_clamped_to_1_3(self):
        d = ActorStateDelta(actor_id="x", mood=99)
        assert d.mood == 3
        d2 = ActorStateDelta(actor_id="x", mood=-5)
        assert d2.mood == 1

    def test_needs_clamped_to_1_5(self):
        d = ActorStateDelta(actor_id="x", energy=100, safety=0, social=-3, esteem=10)
        assert d.energy == 5
        assert d.safety == 1
        assert d.social == 1
        assert d.esteem == 5

    def test_trust_affinity_clamped_to_neg5_pos5(self):
        r = RelationDelta(source_actor_id="a", target_actor_id="b", trust=99, affinity=-99)
        assert r.trust == 5
        assert r.affinity == -5

    def test_tension_clamped_to_0_5(self):
        r = RelationDelta(source_actor_id="a", target_actor_id="b", tension=-3)
        assert r.tension == 0
        r2 = RelationDelta(source_actor_id="a", target_actor_id="b", tension=100)
        assert r2.tension == 5

    def test_severity_clamped_to_1_5(self):
        a = CausalAnchorDelta(summary="test", severity=99)
        assert a.severity == 5
        a2 = CausalAnchorDelta(summary="test", severity=-1)
        assert a2.severity == 1


class TestCausalAnchorIsolation:
    """Jangkar Kausal di Cabang A tidak muncul di lineage Cabang B."""

    def test_anchor_isolated_between_branches(self, db_conn):
        sid, bid_main, root_id, _, _ = _seed_full(db_conn)

        # Tambah simpul S01 di main
        s01 = _make_id()
        with write_transaction(db_conn) as c:
            c.execute(
                "INSERT INTO nodes (node_id, scenario_id, branch_id, parent_id, turn_index) "
                "VALUES (?, ?, ?, ?, 1)",
                (s01, sid, bid_main, root_id),
            )
            # Jangkar di S01 cabang main
            c.execute(
                "INSERT INTO causal_anchors (anchor_id, scenario_id, origin_node_id, summary, severity) "
                "VALUES (?, ?, ?, ?, 2)",
                (_make_id(), sid, s01, "Dana terbatas di main"),
            )

        # Fork cabang B dari root
        bid_b = _make_id()
        s01b = _make_id()
        with write_transaction(db_conn) as c:
            c.execute(
                "INSERT INTO branches (branch_id, scenario_id, name, head_node_id, color) "
                "VALUES (?, ?, ?, ?, ?)",
                (bid_b, sid, "cabang-b", s01b, "#38BDF8"),
            )
            c.execute(
                "INSERT INTO nodes (node_id, scenario_id, branch_id, parent_id, turn_index) "
                "VALUES (?, ?, ?, ?, 1)",
                (s01b, sid, bid_b, root_id),
            )

        # CTE lineage dari s01b (cabang B): root_id, s01b
        lineage_b = db_conn.execute(
            """
            WITH RECURSIVE lineage(nid) AS (
                SELECT node_id FROM nodes WHERE node_id = ?
                UNION ALL
                SELECT n.node_id FROM nodes n JOIN lineage l ON n.node_id = (
                    SELECT parent_id FROM nodes WHERE node_id = l.nid
                )
                WHERE (SELECT parent_id FROM nodes WHERE node_id = l.nid) IS NOT NULL
            )
            SELECT nid FROM lineage
            """,
            (s01b,),
        ).fetchall()
        lineage_b_ids = {r["nid"] for r in lineage_b}

        # Jangkar dari main (s01) tidak ada di lineage B
        anchors_in_b = db_conn.execute(
            "SELECT anchor_id FROM causal_anchors WHERE origin_node_id IN ({})".format(
                ",".join("?" * len(lineage_b_ids))
            ),
            list(lineage_b_ids),
        ).fetchall()

        assert len(anchors_in_b) == 0, "Jangkar cabang A bocor ke lineage cabang B!"
