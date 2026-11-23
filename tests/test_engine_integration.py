"""
tests/test_engine_integration.py — Tes Integrasi Engine (dag_repo + state_mutator)

Menguji alur lengkap:
1. commit_turn menyisipkan node + state + relasi + jangkar.
2. state_mutator menerapkan delta dengan benar.
3. Anti-halusinasi: actor_id fiktif diabaikan.
4. fork_branch + commit di cabang baru terisolasi.
5. checkout memindahkan head.
6. Lineage anchors benar setelah fork.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.engine.dag_repo import (
    commit_turn,
    fork_branch,
    checkout_branch,
    get_lineage,
    get_node_state,
    get_lineage_anchors,
    get_graph,
    load_seed_scenario,
)
from app.engine.state_mutator import apply_turn_deltas
from app.schemas import (
    TurnResponse,
    ActorStateDelta,
    RelationDelta,
    CausalAnchorDelta,
)


_SEEDS_DIR = Path(__file__).parent.parent / "app" / "seeds"


def _load_kampus(conn):
    """Muat seed kampus_anti_scam."""
    with open(_SEEDS_DIR / "kampus_anti_scam.json", encoding="utf-8") as f:
        return load_seed_scenario(conn, json.load(f))


def _get_main_branch_and_root(conn, scenario_id):
    """Ambil branch_id dan head_node_id dari branch main."""
    row = conn.execute(
        "SELECT branch_id, head_node_id FROM branches "
        "WHERE scenario_id = ? AND name = 'main'",
        (scenario_id,),
    ).fetchone()
    return row["branch_id"], row["head_node_id"]


class TestCommitTurn:
    """commit_turn menyisipkan node baru dengan benar."""

    def test_basic_commit(self, db_conn):
        sid = _load_kampus(db_conn)
        bid, root_id = _get_main_branch_and_root(db_conn, sid)

        turn_resp = TurnResponse(
            narrative="Raka memutuskan untuk menghubungi Alin terlebih dahulu.",
            actor_deltas=[
                ActorStateDelta(actor_id="raka", mood=1, energy=2),
            ],
            relation_deltas=[
                RelationDelta(
                    source_actor_id="raka", target_actor_id="ketua_alin",
                    trust=5, tension=0,
                ),
            ],
            updated_arc_summary="Raka menghubungi Alin.",
            suggested_choices=["Tanya Alin", "Tolak vendor"],
        )

        valid_ids = {"raka", "vendor_dewi", "ketua_alin"}
        new_states, new_edges = apply_turn_deltas(
            db_conn, root_id, turn_resp, valid_ids
        )

        node_id = commit_turn(
            db_conn,
            scenario_id=sid, branch_id=bid,
            parent_node_id=root_id, user_action="Hubungi Alin dulu",
            turn_response=turn_resp,
            actor_states=new_states, relation_edges=new_edges,
        )

        # Node tersimpan
        row = db_conn.execute(
            "SELECT * FROM nodes WHERE node_id = ?", (node_id,)
        ).fetchone()
        assert row is not None
        assert row["turn_index"] == 1
        assert row["parent_id"] == root_id

        # Head branch bergeser
        head = db_conn.execute(
            "SELECT head_node_id FROM branches WHERE branch_id = ?", (bid,)
        ).fetchone()
        assert head["head_node_id"] == node_id

    def test_commit_with_anchor(self, db_conn):
        sid = _load_kampus(db_conn)
        bid, root_id = _get_main_branch_and_root(db_conn, sid)

        turn_resp = TurnResponse(
            narrative="Dewi memberikan ultimatum.",
            new_anchor=CausalAnchorDelta(summary="Ultimatum DP hari ini", severity=4),
            updated_arc_summary="Tekanan meningkat.",
        )

        valid_ids = {"raka", "vendor_dewi", "ketua_alin"}
        new_states, new_edges = apply_turn_deltas(
            db_conn, root_id, turn_resp, valid_ids
        )

        node_id = commit_turn(
            db_conn, scenario_id=sid, branch_id=bid,
            parent_node_id=root_id, user_action="Minta bukti legalitas",
            turn_response=turn_resp,
            actor_states=new_states, relation_edges=new_edges,
        )

        anchors = get_lineage_anchors(db_conn, node_id)
        assert len(anchors) == 1
        assert anchors[0].summary == "Ultimatum DP hari ini"
        assert anchors[0].severity == 4


class TestStateMutator:
    """state_mutator menerapkan delta dengan clamping dan anti-halusinasi."""

    def test_delta_applied_correctly(self, db_conn):
        sid = _load_kampus(db_conn)
        _, root_id = _get_main_branch_and_root(db_conn, sid)

        turn_resp = TurnResponse(
            narrative="Perubahan state.",
            actor_deltas=[
                ActorStateDelta(actor_id="raka", mood=3, safety=5),
                ActorStateDelta(actor_id="vendor_dewi", energy=1),
            ],
        )
        valid_ids = {"raka", "vendor_dewi", "ketua_alin"}
        states, edges = apply_turn_deltas(db_conn, root_id, turn_resp, valid_ids)

        raka_state = next(s for s in states if s["actor_id"] == "raka")
        assert raka_state["mood"] == 3
        assert raka_state["safety"] == 5
        # energy tidak di-delta, harus tetap dari parent (3)
        assert raka_state["energy"] == 3

        dewi_state = next(s for s in states if s["actor_id"] == "vendor_dewi")
        assert dewi_state["energy"] == 1

    def test_hallucinated_actor_ignored(self, db_conn):
        """actor_id yang tidak terdaftar diabaikan tanpa error."""
        sid = _load_kampus(db_conn)
        _, root_id = _get_main_branch_and_root(db_conn, sid)

        turn_resp = TurnResponse(
            narrative="Ada aktor fiktif.",
            actor_deltas=[
                ActorStateDelta(actor_id="hantu_fiktif", mood=1),
                ActorStateDelta(actor_id="raka", mood=1),
            ],
        )
        valid_ids = {"raka", "vendor_dewi", "ketua_alin"}
        states, _ = apply_turn_deltas(db_conn, root_id, turn_resp, valid_ids)

        # Tidak ada state untuk hantu_fiktif
        actor_ids = {s["actor_id"] for s in states}
        assert "hantu_fiktif" not in actor_ids
        assert "raka" in actor_ids

    def test_relation_delta_asymmetric(self, db_conn):
        """Mengubah A->B tidak mengubah B->A."""
        sid = _load_kampus(db_conn)
        _, root_id = _get_main_branch_and_root(db_conn, sid)

        turn_resp = TurnResponse(
            narrative="Hanya Raka->Dewi berubah.",
            relation_deltas=[
                RelationDelta(
                    source_actor_id="raka", target_actor_id="vendor_dewi",
                    trust=-5, tension=5,
                ),
            ],
        )
        valid_ids = {"raka", "vendor_dewi", "ketua_alin"}
        _, edges = apply_turn_deltas(db_conn, root_id, turn_resp, valid_ids)

        raka_to_dewi = next(
            e for e in edges
            if e["source_actor_id"] == "raka" and e["target_actor_id"] == "vendor_dewi"
        )
        dewi_to_raka = next(
            e for e in edges
            if e["source_actor_id"] == "vendor_dewi" and e["target_actor_id"] == "raka"
        )

        assert raka_to_dewi["trust"] == -5
        assert raka_to_dewi["tension"] == 5
        # Dewi -> Raka TIDAK berubah (dari seed: trust=1, tension=1)
        assert dewi_to_raka["trust"] == 1
        assert dewi_to_raka["tension"] == 1

    def test_hallucinated_relation_ignored(self, db_conn):
        """Relasi dengan actor_id fiktif diabaikan."""
        sid = _load_kampus(db_conn)
        _, root_id = _get_main_branch_and_root(db_conn, sid)

        turn_resp = TurnResponse(
            narrative="Relasi fiktif.",
            relation_deltas=[
                RelationDelta(
                    source_actor_id="hantu", target_actor_id="raka",
                    trust=5,
                ),
            ],
        )
        valid_ids = {"raka", "vendor_dewi", "ketua_alin"}
        _, edges = apply_turn_deltas(db_conn, root_id, turn_resp, valid_ids)

        # Tidak ada edge dari "hantu"
        hantu_edges = [e for e in edges if e["source_actor_id"] == "hantu"]
        assert len(hantu_edges) == 0


class TestForkAndCheckout:
    """Fork dan checkout bekerja dengan isolasi penuh."""

    def test_fork_creates_new_branch(self, db_conn):
        sid = _load_kampus(db_conn)
        bid, root_id = _get_main_branch_and_root(db_conn, sid)

        fork_bid = fork_branch(
            db_conn,
            scenario_id=sid,
            from_node_id=root_id,
            new_branch_name="opsi-tolak",
        )

        branch = db_conn.execute(
            "SELECT * FROM branches WHERE branch_id = ?", (fork_bid,)
        ).fetchone()
        assert branch["name"] == "opsi-tolak"
        assert branch["head_node_id"] == root_id

    def test_fork_does_not_modify_original(self, db_conn):
        sid = _load_kampus(db_conn)
        bid, root_id = _get_main_branch_and_root(db_conn, sid)

        # Tambah satu node di main
        turn_resp = TurnResponse(narrative="Langkah pertama di main.")
        valid_ids = {"raka", "vendor_dewi", "ketua_alin"}
        states, edges = apply_turn_deltas(db_conn, root_id, turn_resp, valid_ids)
        s01 = commit_turn(
            db_conn, scenario_id=sid, branch_id=bid,
            parent_node_id=root_id, user_action="Aksi main",
            turn_response=turn_resp,
            actor_states=states, relation_edges=edges,
        )

        # Fork dari root
        fork_bid = fork_branch(
            db_conn, scenario_id=sid,
            from_node_id=root_id, new_branch_name="cabang-b",
        )

        # Tambah node di cabang fork
        turn_resp_b = TurnResponse(narrative="Langkah pertama di cabang B.")
        states_b, edges_b = apply_turn_deltas(db_conn, root_id, turn_resp_b, valid_ids)
        s01b = commit_turn(
            db_conn, scenario_id=sid, branch_id=fork_bid,
            parent_node_id=root_id, user_action="Aksi fork",
            turn_response=turn_resp_b,
            actor_states=states_b, relation_edges=edges_b,
        )

        # Verifikasi: node main masih utuh
        main_nodes = db_conn.execute(
            "SELECT node_id FROM nodes WHERE branch_id = ? ORDER BY turn_index",
            (bid,),
        ).fetchall()
        main_ids = [r["node_id"] for r in main_nodes]
        assert main_ids == [root_id, s01]

        # Verifikasi: fork punya node sendiri
        fork_nodes = db_conn.execute(
            "SELECT node_id FROM nodes WHERE branch_id = ? ORDER BY turn_index",
            (fork_bid,),
        ).fetchall()
        fork_ids = [r["node_id"] for r in fork_nodes]
        assert fork_ids == [s01b]

    def test_checkout_moves_head(self, db_conn):
        sid = _load_kampus(db_conn)
        bid, root_id = _get_main_branch_and_root(db_conn, sid)

        # Tambah node
        turn_resp = TurnResponse(narrative="S01")
        valid_ids = {"raka", "vendor_dewi", "ketua_alin"}
        states, edges = apply_turn_deltas(db_conn, root_id, turn_resp, valid_ids)
        s01 = commit_turn(
            db_conn, scenario_id=sid, branch_id=bid,
            parent_node_id=root_id, user_action="Maju",
            turn_response=turn_resp,
            actor_states=states, relation_edges=edges,
        )

        # Head sekarang di s01
        head = db_conn.execute(
            "SELECT head_node_id FROM branches WHERE branch_id = ?", (bid,)
        ).fetchone()
        assert head["head_node_id"] == s01

        # Checkout kembali ke root
        result = checkout_branch(db_conn, branch_id=bid, target_node_id=root_id)
        assert result == root_id

        head2 = db_conn.execute(
            "SELECT head_node_id FROM branches WHERE branch_id = ?", (bid,)
        ).fetchone()
        assert head2["head_node_id"] == root_id

    def test_lineage_correctness(self, db_conn):
        sid = _load_kampus(db_conn)
        bid, root_id = _get_main_branch_and_root(db_conn, sid)
        valid_ids = {"raka", "vendor_dewi", "ketua_alin"}

        # Buat chain: root -> s01 -> s02 -> s03
        nodes_chain = [root_id]
        for i in range(3):
            turn_resp = TurnResponse(narrative=f"Giliran {i+1}")
            states, edges = apply_turn_deltas(
                db_conn, nodes_chain[-1], turn_resp, valid_ids
            )
            nid = commit_turn(
                db_conn, scenario_id=sid, branch_id=bid,
                parent_node_id=nodes_chain[-1], user_action=f"Aksi {i+1}",
                turn_response=turn_resp,
                actor_states=states, relation_edges=edges,
            )
            nodes_chain.append(nid)

        # Lineage dari s03 harus: [s03, s02, s01, root]
        lineage = get_lineage(db_conn, nodes_chain[-1])
        assert lineage == list(reversed(nodes_chain))


class TestGraphQuery:
    """get_graph mengembalikan data lengkap."""

    def test_graph_contains_all_data(self, db_conn):
        sid = _load_kampus(db_conn)
        graph = get_graph(db_conn, sid)

        assert graph.scenario_id == sid
        assert len(graph.branches) == 1
        assert graph.branches[0].name == "main"
        assert len(graph.nodes) == 1  # hanya root
        assert graph.head_node_id is not None
        assert len(graph.nodes[0].actor_states) == 3
        assert len(graph.nodes[0].relation_edges) == 6
