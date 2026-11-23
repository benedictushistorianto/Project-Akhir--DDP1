"""
tests/test_dag_immutability.py — Suite #1: Git-DAG Imutabel

Menguji bahwa:
1. Tabel bisa dibuat tanpa error.
2. Simpul akar (S00) bisa disisipkan.
3. Simpul anak terhubung ke parent.
4. Fork cabang tidak mengubah cabang asal.
5. Recursive CTE menghasilkan lineage yang benar.
6. parent_id fiktif ditolak oleh foreign key constraint.
"""

from __future__ import annotations

import sqlite3
import uuid

import pytest

from app.db.connection import write_transaction


def _make_id() -> str:
    return uuid.uuid4().hex[:12]


def _seed_scenario(conn: sqlite3.Connection) -> tuple[str, str, str]:
    """Buat skenario + branch main + node akar. Return (scenario_id, branch_id, root_node_id)."""
    sid = _make_id()
    bid = _make_id()
    nid = _make_id()

    with write_transaction(conn) as c:
        c.execute(
            "INSERT INTO scenarios (scenario_id, title, premise) VALUES (?, ?, ?)",
            (sid, "Test Skenario", "Premis uji coba"),
        )
        c.execute(
            "INSERT INTO branches (branch_id, scenario_id, name, head_node_id) VALUES (?, ?, ?, ?)",
            (bid, sid, "main", nid),
        )
        c.execute(
            "INSERT INTO nodes (node_id, scenario_id, branch_id, parent_id, turn_index, narrative) "
            "VALUES (?, ?, ?, NULL, 0, ?)",
            (nid, sid, bid, "Awal cerita."),
        )
    return sid, bid, nid


class TestSchemaCreation:
    """Tabel berhasil dibuat tanpa error."""

    def test_tables_exist(self, db_conn):
        tables = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        names = {row["name"] for row in tables}
        expected = {
            "scenarios", "actor_cores", "branches", "nodes",
            "actor_states", "relation_edges", "causal_anchors",
        }
        assert expected.issubset(names), f"Missing tables: {expected - names}"


class TestNodeInsertion:
    """Simpul bisa disisipkan dan dihubungkan."""

    def test_insert_root_node(self, db_conn):
        sid, bid, nid = _seed_scenario(db_conn)
        row = db_conn.execute("SELECT * FROM nodes WHERE node_id = ?", (nid,)).fetchone()
        assert row is not None
        assert row["parent_id"] is None
        assert row["turn_index"] == 0

    def test_insert_child_node(self, db_conn):
        sid, bid, root_id = _seed_scenario(db_conn)
        child_id = _make_id()

        with write_transaction(db_conn) as c:
            c.execute(
                "INSERT INTO nodes (node_id, scenario_id, branch_id, parent_id, turn_index, narrative) "
                "VALUES (?, ?, ?, ?, 1, ?)",
                (child_id, sid, bid, root_id, "Giliran pertama."),
            )

        row = db_conn.execute("SELECT * FROM nodes WHERE node_id = ?", (child_id,)).fetchone()
        assert row["parent_id"] == root_id
        assert row["turn_index"] == 1


class TestForkImmutability:
    """Fork cabang tidak mengubah simpul di cabang asal."""

    def test_fork_preserves_original(self, db_conn):
        sid, bid, root_id = _seed_scenario(db_conn)

        # Tambah 2 simpul di main: S01, S02
        s01 = _make_id()
        s02 = _make_id()
        with write_transaction(db_conn) as c:
            c.execute(
                "INSERT INTO nodes (node_id, scenario_id, branch_id, parent_id, turn_index) "
                "VALUES (?, ?, ?, ?, 1)",
                (s01, sid, bid, root_id),
            )
            c.execute(
                "INSERT INTO nodes (node_id, scenario_id, branch_id, parent_id, turn_index) "
                "VALUES (?, ?, ?, ?, 2)",
                (s02, sid, bid, s01),
            )

        # Fork dari root_id -> cabang baru
        fork_bid = _make_id()
        fork_node = _make_id()
        with write_transaction(db_conn) as c:
            c.execute(
                "INSERT INTO branches (branch_id, scenario_id, name, head_node_id, color) "
                "VALUES (?, ?, ?, ?, ?)",
                (fork_bid, sid, "opsi-b", fork_node, "#38BDF8"),
            )
            c.execute(
                "INSERT INTO nodes (node_id, scenario_id, branch_id, parent_id, turn_index) "
                "VALUES (?, ?, ?, ?, 1)",
                (fork_node, sid, fork_bid, root_id),
            )

        # Verifikasi simpul asli tetap utuh
        original_nodes = db_conn.execute(
            "SELECT node_id FROM nodes WHERE branch_id = ? ORDER BY turn_index",
            (bid,),
        ).fetchall()
        original_ids = [r["node_id"] for r in original_nodes]
        assert original_ids == [root_id, s01, s02], "Fork mengubah simpul cabang asal!"


class TestRecursiveCTE:
    """Recursive CTE menghasilkan garis keturunan yang benar."""

    def test_lineage_from_leaf(self, db_conn):
        sid, bid, root_id = _seed_scenario(db_conn)
        s01 = _make_id()
        s02 = _make_id()

        with write_transaction(db_conn) as c:
            c.execute(
                "INSERT INTO nodes (node_id, scenario_id, branch_id, parent_id, turn_index) "
                "VALUES (?, ?, ?, ?, 1)",
                (s01, sid, bid, root_id),
            )
            c.execute(
                "INSERT INTO nodes (node_id, scenario_id, branch_id, parent_id, turn_index) "
                "VALUES (?, ?, ?, ?, 2)",
                (s02, sid, bid, s01),
            )

        # CTE: dari s02 ke akar
        rows = db_conn.execute(
            """
            WITH RECURSIVE lineage(nid, pid, depth) AS (
                SELECT node_id, parent_id, 0 FROM nodes WHERE node_id = ?
                UNION ALL
                SELECT n.node_id, n.parent_id, l.depth + 1
                FROM nodes n JOIN lineage l ON n.node_id = l.pid
            )
            SELECT nid FROM lineage ORDER BY depth
            """,
            (s02,),
        ).fetchall()
        lineage_ids = [r["nid"] for r in rows]
        assert lineage_ids == [s02, s01, root_id]


class TestForeignKeyConstraint:
    """parent_id fiktif ditolak oleh foreign key constraint."""

    def test_reject_fake_parent(self, db_conn):
        sid, bid, _ = _seed_scenario(db_conn)
        fake_parent = "DOES_NOT_EXIST"
        with pytest.raises(sqlite3.IntegrityError):
            with write_transaction(db_conn) as c:
                c.execute(
                    "INSERT INTO nodes (node_id, scenario_id, branch_id, parent_id, turn_index) "
                    "VALUES (?, ?, ?, ?, 1)",
                    (_make_id(), sid, bid, fake_parent),
                )
