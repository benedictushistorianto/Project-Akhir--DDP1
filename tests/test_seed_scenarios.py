"""
tests/test_seed_scenarios.py — Suite #6: Integritas 3 Skenario Bawaan

Menguji bahwa:
1. Setiap seed JSON bisa dimuat tanpa error foreign key.
2. Aktor, state awal, dan relasi awal tersimpan dengan benar.
3. Ketiga skenario bisa diakses via API /api/scenarios.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.engine.dag_repo import load_seed_scenario, get_graph

_SEEDS_DIR = Path(__file__).parent.parent / "app" / "seeds"
_SEED_FILES = [
    "kampus_anti_scam.json",
    "kebijakan_parkir.json",
    "misteri_pelabuhan_1928.json",
]


def _load_all_seeds(conn):
    """Muat ketiga seed ke database."""
    for fname in _SEED_FILES:
        fpath = _SEEDS_DIR / fname
        with open(fpath, encoding="utf-8") as f:
            seed_data = json.load(f)
        load_seed_scenario(conn, seed_data)


class TestSeedLoading:
    """Seed JSON bisa dimuat tanpa error FK."""

    def test_all_seeds_load_without_error(self, db_conn):
        _load_all_seeds(db_conn)
        rows = db_conn.execute("SELECT COUNT(*) as cnt FROM scenarios").fetchone()
        assert rows["cnt"] == 3

    def test_idempotent_load(self, db_conn):
        """Memuat ulang seed yang sama tidak menyebabkan duplikasi."""
        _load_all_seeds(db_conn)
        _load_all_seeds(db_conn)  # muat ulang
        rows = db_conn.execute("SELECT COUNT(*) as cnt FROM scenarios").fetchone()
        assert rows["cnt"] == 3


class TestSeedIntegrity:
    """Data seed tersimpan dengan benar di SQLite."""

    def test_kampus_anti_scam_actors(self, db_conn):
        _load_all_seeds(db_conn)
        actors = db_conn.execute(
            "SELECT actor_id FROM actor_cores WHERE scenario_id = 'kampus_anti_scam' ORDER BY actor_id"
        ).fetchall()
        ids = [a["actor_id"] for a in actors]
        assert "raka" in ids
        assert "vendor_dewi" in ids
        assert "ketua_alin" in ids
        assert len(ids) == 3

    def test_kebijakan_parkir_initial_state(self, db_conn):
        _load_all_seeds(db_conn)
        # Pastikan ada node root dengan narrative
        graph = get_graph(db_conn, "kebijakan_parkir")
        assert len(graph.nodes) == 1
        root = graph.nodes[0]
        assert root.turn_index == 0
        assert "Ruang rapat" in root.narrative

    def test_misteri_pelabuhan_relations(self, db_conn):
        _load_all_seeds(db_conn)
        graph = get_graph(db_conn, "misteri_pelabuhan_1928")
        root = graph.nodes[0]
        # Harus ada 6 relasi (3 aktor x 2 arah)
        assert len(root.relation_edges) == 6

        # Halim -> de Vries harus trust negatif (mencurigakan)
        halim_to_devries = [
            e for e in root.relation_edges
            if e.source_actor_id == "halim"
            and e.target_actor_id == "meneer_de_vries"
        ]
        assert len(halim_to_devries) == 1
        assert halim_to_devries[0].trust == -2

    def test_seed_scenario_has_branch_and_head(self, db_conn):
        _load_all_seeds(db_conn)
        for sid in ["kampus_anti_scam", "kebijakan_parkir", "misteri_pelabuhan_1928"]:
            branch = db_conn.execute(
                "SELECT * FROM branches WHERE scenario_id = ? AND name = 'main'",
                (sid,),
            ).fetchone()
            assert branch is not None, f"Skenario {sid} tidak punya branch main"
            assert branch["head_node_id"] is not None
