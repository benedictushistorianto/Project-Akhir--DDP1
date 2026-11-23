"""
tests/test_api_contracts.py — Suite #5: Kontrak API Endpoint

Menguji bahwa:
1. /healthz mengembalikan 200.
2. /readyz mengembalikan 200 dengan db: true.
3. Endpoint yang belum ada mengembalikan 404.
4. /api/scenarios mengembalikan daftar skenario setelah seed dimuat.
5. /api/scenarios/{id}/graph mengembalikan graf.
6. /api/turns menyisipkan giliran baru (201).
7. /api/branches/fork membuat cabang baru (201).
8. /api/branches/checkout mengembalikan state.
9. /api/scenarios/{id}/export?format=json dan format=md berfungsi.
10. Payload invalid mengembalikan 422.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.engine.dag_repo import load_seed_scenario

_SEEDS_DIR = Path(__file__).parent.parent / "app" / "seeds"


def _load_seeds_via_client(client):
    """Muat seed secara langsung melalui db_conn di app.state."""
    conn = client.app.state.db_conn
    for fname in sorted((_SEEDS_DIR).iterdir()):
        if fname.suffix == ".json":
            with open(fname, encoding="utf-8") as f:
                load_seed_scenario(conn, json.load(f))


class TestHealthEndpoints:
    """Endpoint kesehatan berfungsi."""

    def test_healthz_ok(self, client):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_readyz_with_db(self, client):
        resp = client.get("/readyz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["db"] is True
        assert data["status"] == "ready"


class TestNotFound:
    """Route yang tidak terdaftar mengembalikan 404."""

    def test_unknown_route_404(self, client):
        resp = client.get("/api/nonexistent")
        assert resp.status_code == 404

    def test_scenario_not_found_404(self, client):
        resp = client.get("/api/scenarios/fake_id")
        assert resp.status_code == 404

    def test_graph_not_found_404(self, client):
        resp = client.get("/api/scenarios/fake_id/graph")
        assert resp.status_code == 404


class TestScenarioEndpoints:
    """Endpoint skenario berfungsi setelah seed dimuat."""

    def test_list_scenarios(self, client):
        _load_seeds_via_client(client)
        resp = client.get("/api/scenarios")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        titles = {s["title"] for s in data}
        assert "Mahasiswa vs Penipuan Daring" in titles

    def test_get_single_scenario(self, client):
        _load_seeds_via_client(client)
        resp = client.get("/api/scenarios/kampus_anti_scam")
        assert resp.status_code == 200
        data = resp.json()
        assert data["scenario_id"] == "kampus_anti_scam"
        assert len(data["actor_cores"]) == 3

    def test_get_scenario_graph(self, client):
        _load_seeds_via_client(client)
        resp = client.get("/api/scenarios/kampus_anti_scam/graph")
        assert resp.status_code == 200
        data = resp.json()
        assert data["scenario_id"] == "kampus_anti_scam"
        assert len(data["nodes"]) >= 1
        assert len(data["branches"]) >= 1
        assert data["head_node_id"] is not None


class TestTurnEndpoint:
    """POST /api/turns menyisipkan giliran baru."""

    def test_execute_turn_201(self, client):
        _load_seeds_via_client(client)
        # Ambil branch dan head node
        graph_resp = client.get("/api/scenarios/kampus_anti_scam/graph")
        graph = graph_resp.json()
        bid = graph["branches"][0]["branch_id"]
        head_id = graph["head_node_id"]

        resp = client.post("/api/turns", json={
            "scenario_id": "kampus_anti_scam",
            "parent_node_id": head_id,
            "branch_id": bid,
            "user_action": "Tanyakan nama lengkap CV ke Dewi",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["turn_index"] == 1
        assert data["parent_id"] == head_id
        assert data["user_action"] == "Tanyakan nama lengkap CV ke Dewi"
        assert len(data["narrative"]) > 0
        assert len(data["suggested_choices"]) > 0

    def test_execute_turn_nonexistent_scenario_404(self, client):
        resp = client.post("/api/turns", json={
            "scenario_id": "tidak_ada",
            "parent_node_id": "fake",
            "branch_id": "fake",
            "user_action": "test",
        })
        assert resp.status_code == 404

    def test_execute_turn_invalid_payload_422(self, client):
        resp = client.post("/api/turns", json={"scenario_id": "x"})
        assert resp.status_code == 422


class TestForkEndpoint:
    """POST /api/branches/fork membuat cabang baru."""

    def test_fork_201(self, client):
        _load_seeds_via_client(client)
        graph_resp = client.get("/api/scenarios/kampus_anti_scam/graph")
        graph = graph_resp.json()
        head_id = graph["head_node_id"]

        resp = client.post("/api/branches/fork", json={
            "scenario_id": "kampus_anti_scam",
            "from_node_id": head_id,
            "new_branch_name": "opsi-tolak",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "opsi-tolak"
        assert data["head_node_id"] == head_id

    def test_fork_nonexistent_node_404(self, client):
        _load_seeds_via_client(client)
        resp = client.post("/api/branches/fork", json={
            "scenario_id": "kampus_anti_scam",
            "from_node_id": "FAKE_NODE",
            "new_branch_name": "ghost",
        })
        assert resp.status_code == 404


class TestCheckoutEndpoint:
    """POST /api/branches/checkout mengembalikan state."""

    def test_checkout_returns_state(self, client):
        _load_seeds_via_client(client)
        graph_resp = client.get("/api/scenarios/kampus_anti_scam/graph")
        graph = graph_resp.json()
        bid = graph["branches"][0]["branch_id"]
        head_id = graph["head_node_id"]

        resp = client.post("/api/branches/checkout", json={
            "branch_id": bid,
            "target_node_id": head_id,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["head_node_id"] == head_id
        assert len(data["actor_states"]) == 3
        assert len(data["relation_edges"]) == 6


class TestExportEndpoint:
    """GET /api/scenarios/{id}/export berfungsi."""

    def test_export_json(self, client):
        _load_seeds_via_client(client)
        resp = client.get("/api/scenarios/kampus_anti_scam/export?format=json")
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]
        data = json.loads(resp.text)
        assert data["scenario_id"] == "kampus_anti_scam"

    def test_export_markdown(self, client):
        _load_seeds_via_client(client)
        resp = client.get("/api/scenarios/kampus_anti_scam/export?format=md")
        assert resp.status_code == 200
        assert "text/markdown" in resp.headers["content-type"]
        assert "Mahasiswa vs Penipuan Daring" in resp.text

    def test_export_nonexistent_404(self, client):
        resp = client.get("/api/scenarios/fake/export?format=json")
        assert resp.status_code == 404
