"""
app/engine/dag_repo.py — Git-DAG Repository

Fungsi utama untuk mengelola pohon simpul imutabel:
- get_lineage(conn, node_id): Menelusuri garis keturunan dari simpul
  ke akar menggunakan WITH RECURSIVE CTE.
- commit_turn(...): Menyisipkan simpul baru sebagai anak dari parent_id,
  menyimpan state/relasi/jangkar, dan memperbarui head_node_id cabang.
- fork_branch(...): Membuat cabang baru yang dimulai dari simpul tertentu
  tanpa menyentuh cabang asal.
- get_graph(conn, scenario_id): Mengambil seluruh graf DAG untuk satu skenario.
- get_node_state(conn, node_id): Mengambil snapshot state + relasi pada
  satu simpul.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Any

from app.db.connection import write_transaction
from app.schemas import (
    ActorCoreDTO,
    ActorStateDTO,
    BranchDTO,
    CausalAnchorDTO,
    GraphDTO,
    NodeDTO,
    RelationEdgeDTO,
    ScenarioDTO,
    TurnResponse,
)


# ── Utilitas ─────────────────────────────────────────────────

_LANE_COLORS = ["#2DD4BF", "#38BDF8", "#F59E0B", "#FB7185"]


def _new_id() -> str:
    """Buat ID pendek yang unik (12 karakter hex)."""
    return uuid.uuid4().hex[:12]


# ── Lineage (Recursive CTE) ─────────────────────────────────

def get_lineage(conn: sqlite3.Connection, node_id: str) -> list[str]:
    """Kembalikan daftar node_id dari node_id ke akar (urut dari daun ke akar).

    Memakai WITH RECURSIVE agar pencarian O(depth), bukan O(N total nodes).
    """
    rows = conn.execute(
        """
        WITH RECURSIVE lineage(nid, pid, depth) AS (
            SELECT node_id, parent_id, 0
            FROM nodes WHERE node_id = ?
            UNION ALL
            SELECT n.node_id, n.parent_id, l.depth + 1
            FROM nodes n
            JOIN lineage l ON n.node_id = l.pid
        )
        SELECT nid FROM lineage ORDER BY depth
        """,
        (node_id,),
    ).fetchall()
    return [r["nid"] for r in rows]


# ── Commit Turn ──────────────────────────────────────────────

def commit_turn(
    conn: sqlite3.Connection,
    *,
    scenario_id: str,
    branch_id: str,
    parent_node_id: str,
    user_action: str,
    turn_response: TurnResponse,
    actor_states: list[dict[str, Any]],
    relation_edges: list[dict[str, Any]],
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    latency_ms: int = 0,
    is_fallback: bool = False,
) -> str:
    """Simpan satu giliran sebagai simpul baru di pohon DAG.

    Alur:
    1. Hitung turn_index dari parent + 1.
    2. Sisipkan node baru ke tabel nodes.
    3. Sisipkan actor_states dan relation_edges (snapshot imutabel).
    4. Jika ada new_anchor, sisipkan ke causal_anchors.
    5. Update head_node_id cabang.

    Return: node_id baru.
    """
    node_id = _new_id()

    with write_transaction(conn) as c:
        # Ambil turn_index parent
        parent_row = c.execute(
            "SELECT turn_index FROM nodes WHERE node_id = ?",
            (parent_node_id,),
        ).fetchone()
        if parent_row is None:
            raise ValueError(f"Parent node tidak ditemukan: {parent_node_id}")
        turn_index = parent_row["turn_index"] + 1

        # Sisipkan node
        c.execute(
            """INSERT INTO nodes
            (node_id, scenario_id, branch_id, parent_id, turn_index,
             user_action, narrative, arc_summary,
             prompt_tokens, completion_tokens, latency_ms, is_fallback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                node_id, scenario_id, branch_id, parent_node_id, turn_index,
                user_action, turn_response.narrative,
                turn_response.updated_arc_summary,
                prompt_tokens, completion_tokens, latency_ms,
                1 if is_fallback else 0,
            ),
        )

        # Sisipkan actor_states
        for state in actor_states:
            c.execute(
                """INSERT INTO actor_states
                (node_id, actor_id, mood, energy, safety, social, esteem,
                 location, ticking_clock)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    node_id, state["actor_id"],
                    state["mood"], state["energy"], state["safety"],
                    state["social"], state["esteem"],
                    state.get("location", ""),
                    state.get("ticking_clock", ""),
                ),
            )

        # Sisipkan relation_edges
        for edge in relation_edges:
            c.execute(
                """INSERT INTO relation_edges
                (node_id, source_actor_id, target_actor_id,
                 trust, affinity, tension, bond_event)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    node_id, edge["source_actor_id"], edge["target_actor_id"],
                    edge["trust"], edge["affinity"], edge["tension"],
                    edge.get("bond_event", ""),
                ),
            )

        # Sisipkan causal anchor jika ada
        if turn_response.new_anchor is not None:
            anchor_id = _new_id()
            c.execute(
                """INSERT INTO causal_anchors
                (anchor_id, scenario_id, origin_node_id, summary, severity)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    anchor_id, scenario_id, node_id,
                    turn_response.new_anchor.summary,
                    turn_response.new_anchor.severity,
                ),
            )

        # Update head cabang
        c.execute(
            "UPDATE branches SET head_node_id = ? WHERE branch_id = ?",
            (node_id, branch_id),
        )

    return node_id


# ── Fork Branch ──────────────────────────────────────────────

def fork_branch(
    conn: sqlite3.Connection,
    *,
    scenario_id: str,
    from_node_id: str,
    new_branch_name: str,
) -> str:
    """Buat cabang baru yang dimulai dari simpul from_node_id.

    Cabang asal TIDAK dimodifikasi. Head cabang baru menunjuk ke
    from_node_id (belum ada simpul baru; simpul pertama di cabang
    baru dibuat saat giliran berikutnya lewat commit_turn).

    Return: branch_id baru.
    """
    branch_id = _new_id()

    # Pilih warna berdasarkan jumlah cabang yang sudah ada
    existing = conn.execute(
        "SELECT COUNT(*) as cnt FROM branches WHERE scenario_id = ?",
        (scenario_id,),
    ).fetchone()
    color_idx = existing["cnt"] % len(_LANE_COLORS)

    with write_transaction(conn) as c:
        # Pastikan from_node_id ada
        node_row = c.execute(
            "SELECT node_id FROM nodes WHERE node_id = ? AND scenario_id = ?",
            (from_node_id, scenario_id),
        ).fetchone()
        if node_row is None:
            raise ValueError(f"Node tidak ditemukan: {from_node_id}")

        c.execute(
            """INSERT INTO branches
            (branch_id, scenario_id, name, head_node_id, color)
            VALUES (?, ?, ?, ?, ?)""",
            (branch_id, scenario_id, new_branch_name,
             from_node_id, _LANE_COLORS[color_idx]),
        )

    return branch_id


# ── Checkout ─────────────────────────────────────────────────

def checkout_branch(
    conn: sqlite3.Connection,
    *,
    branch_id: str,
    target_node_id: str | None = None,
) -> str:
    """Pindahkan head cabang ke simpul target.

    Jika target_node_id None, head tetap di posisi sekarang.
    Return: node_id yang sekarang menjadi head.
    """
    branch_row = conn.execute(
        "SELECT head_node_id FROM branches WHERE branch_id = ?",
        (branch_id,),
    ).fetchone()
    if branch_row is None:
        raise ValueError(f"Branch tidak ditemukan: {branch_id}")

    if target_node_id is None:
        return branch_row["head_node_id"]

    # Pastikan target ada
    node_row = conn.execute(
        "SELECT node_id FROM nodes WHERE node_id = ?",
        (target_node_id,),
    ).fetchone()
    if node_row is None:
        raise ValueError(f"Node tidak ditemukan: {target_node_id}")

    with write_transaction(conn) as c:
        c.execute(
            "UPDATE branches SET head_node_id = ? WHERE branch_id = ?",
            (target_node_id, branch_id),
        )

    return target_node_id


# ── Query Helpers ────────────────────────────────────────────

def get_node_state(
    conn: sqlite3.Connection, node_id: str
) -> tuple[list[ActorStateDTO], list[RelationEdgeDTO]]:
    """Ambil snapshot actor_states dan relation_edges pada satu simpul."""
    states = conn.execute(
        "SELECT * FROM actor_states WHERE node_id = ?", (node_id,)
    ).fetchall()
    edges = conn.execute(
        "SELECT * FROM relation_edges WHERE node_id = ?", (node_id,)
    ).fetchall()

    actor_states = [
        ActorStateDTO(
            actor_id=s["actor_id"],
            mood=s["mood"], energy=s["energy"], safety=s["safety"],
            social=s["social"], esteem=s["esteem"],
            location=s["location"], ticking_clock=s["ticking_clock"],
        )
        for s in states
    ]
    relation_edges = [
        RelationEdgeDTO(
            source_actor_id=e["source_actor_id"],
            target_actor_id=e["target_actor_id"],
            trust=e["trust"], affinity=e["affinity"], tension=e["tension"],
            bond_event=e["bond_event"],
        )
        for e in edges
    ]
    return actor_states, relation_edges


def get_lineage_anchors(
    conn: sqlite3.Connection, node_id: str, *, limit: int = 10
) -> list[CausalAnchorDTO]:
    """Ambil Jangkar Kausal aktif di garis keturunan node_id.

    Hanya mengambil jangkar yang belum resolved, diurutkan severity
    DESC lalu origin terbaru. Dibatasi `limit` (default 10).
    """
    lineage_ids = get_lineage(conn, node_id)
    if not lineage_ids:
        return []

    placeholders = ",".join("?" * len(lineage_ids))
    rows = conn.execute(
        f"""SELECT * FROM causal_anchors
        WHERE origin_node_id IN ({placeholders})
          AND is_resolved = 0
        ORDER BY severity DESC, origin_node_id DESC
        LIMIT ?""",
        [*lineage_ids, limit],
    ).fetchall()

    return [
        CausalAnchorDTO(
            anchor_id=r["anchor_id"],
            origin_node_id=r["origin_node_id"],
            summary=r["summary"],
            severity=r["severity"],
            is_resolved=bool(r["is_resolved"]),
        )
        for r in rows
    ]


def get_graph(conn: sqlite3.Connection, scenario_id: str) -> GraphDTO:
    """Ambil seluruh graf DAG untuk satu skenario."""
    # Branches
    branch_rows = conn.execute(
        "SELECT * FROM branches WHERE scenario_id = ?", (scenario_id,)
    ).fetchall()
    branches = [
        BranchDTO(
            branch_id=b["branch_id"], scenario_id=b["scenario_id"],
            name=b["name"], head_node_id=b["head_node_id"],
            color=b["color"],
        )
        for b in branch_rows
    ]

    # Head node: ambil dari branch main (atau branch pertama)
    head_node_id = None
    main_branch = conn.execute(
        "SELECT head_node_id FROM branches WHERE scenario_id = ? AND name = 'main'",
        (scenario_id,),
    ).fetchone()
    if main_branch:
        head_node_id = main_branch["head_node_id"]
    elif branches:
        head_node_id = branches[0].head_node_id

    # Nodes
    node_rows = conn.execute(
        "SELECT * FROM nodes WHERE scenario_id = ? ORDER BY turn_index",
        (scenario_id,),
    ).fetchall()
    nodes = []
    for n in node_rows:
        a_states, r_edges = get_node_state(conn, n["node_id"])
        nodes.append(NodeDTO(
            node_id=n["node_id"], scenario_id=n["scenario_id"],
            branch_id=n["branch_id"],
            parent_id=n["parent_id"], turn_index=n["turn_index"],
            user_action=n["user_action"], narrative=n["narrative"],
            arc_summary=n["arc_summary"],
            prompt_tokens=n["prompt_tokens"],
            completion_tokens=n["completion_tokens"],
            latency_ms=n["latency_ms"],
            is_fallback=bool(n["is_fallback"]),
            actor_states=a_states, relation_edges=r_edges,
        ))

    # Causal anchors (semua di skenario ini)
    anchor_rows = conn.execute(
        "SELECT * FROM causal_anchors WHERE scenario_id = ? ORDER BY severity DESC",
        (scenario_id,),
    ).fetchall()
    anchors = [
        CausalAnchorDTO(
            anchor_id=a["anchor_id"], origin_node_id=a["origin_node_id"],
            summary=a["summary"], severity=a["severity"],
            is_resolved=bool(a["is_resolved"]),
        )
        for a in anchor_rows
    ]

    return GraphDTO(
        scenario_id=scenario_id, nodes=nodes, branches=branches,
        head_node_id=head_node_id, causal_anchors=anchors,
    )


def get_scenario_list(conn: sqlite3.Connection) -> list[ScenarioDTO]:
    """Ambil daftar semua skenario dengan aktor dan cabang."""
    rows = conn.execute("SELECT * FROM scenarios ORDER BY created_at").fetchall()
    result = []
    for s in rows:
        # Aktor
        actor_rows = conn.execute(
            "SELECT * FROM actor_cores WHERE scenario_id = ?",
            (s["scenario_id"],),
        ).fetchall()
        actors = [
            ActorCoreDTO(
                actor_id=a["actor_id"], name=a["name"], role=a["role"],
                traits=json.loads(a["traits"]) if a["traits"] else [],
                backstory=a["backstory"],
            )
            for a in actor_rows
        ]
        # Cabang
        branch_rows = conn.execute(
            "SELECT * FROM branches WHERE scenario_id = ?",
            (s["scenario_id"],),
        ).fetchall()
        branches = [
            BranchDTO(
                branch_id=b["branch_id"], scenario_id=b["scenario_id"],
                name=b["name"], head_node_id=b["head_node_id"],
                color=b["color"],
            )
            for b in branch_rows
        ]
        result.append(ScenarioDTO(
            scenario_id=s["scenario_id"], title=s["title"],
            premise=s["premise"], actor_cores=actors, branches=branches,
        ))
    return result


def load_seed_scenario(conn: sqlite3.Connection, seed_data: dict) -> str:
    """Muat skenario dari dict seed JSON ke database.

    Struktur seed_data:
    {
        "scenario_id": "...",
        "title": "...",
        "premise": "...",
        "world_rules": "...",
        "rng_seed": 42,
        "actor_cores": [{"actor_id": "...", "name": "...", ...}],
        "initial_state": {
            "narrative": "...",
            "arc_summary": "...",
            "actor_states": [{...}],
            "relation_edges": [{...}]
        }
    }

    Return: scenario_id.
    """
    sid = seed_data["scenario_id"]

    # Cek apakah sudah dimuat
    existing = conn.execute(
        "SELECT scenario_id FROM scenarios WHERE scenario_id = ?", (sid,)
    ).fetchone()
    if existing:
        return sid

    bid = _new_id()
    root_nid = _new_id()

    with write_transaction(conn) as c:
        # Scenario
        c.execute(
            """INSERT INTO scenarios
            (scenario_id, title, premise, world_rules, rng_seed)
            VALUES (?, ?, ?, ?, ?)""",
            (
                sid, seed_data["title"], seed_data.get("premise", ""),
                seed_data.get("world_rules", ""),
                seed_data.get("rng_seed", 42),
            ),
        )

        # Actor cores
        for actor in seed_data.get("actor_cores", []):
            c.execute(
                """INSERT INTO actor_cores
                (actor_id, scenario_id, name, role, traits, backstory)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    actor["actor_id"], sid, actor["name"],
                    actor.get("role", ""),
                    json.dumps(actor.get("traits", []), ensure_ascii=False),
                    actor.get("backstory", ""),
                ),
            )

        # Branch main
        c.execute(
            """INSERT INTO branches
            (branch_id, scenario_id, name, head_node_id, color)
            VALUES (?, ?, 'main', ?, '#2DD4BF')""",
            (bid, sid, root_nid),
        )

        # Root node (S00)
        init = seed_data.get("initial_state", {})
        c.execute(
            """INSERT INTO nodes
            (node_id, scenario_id, branch_id, parent_id, turn_index,
             user_action, narrative, arc_summary)
            VALUES (?, ?, ?, NULL, 0, '', ?, ?)""",
            (
                root_nid, sid, bid,
                init.get("narrative", ""),
                init.get("arc_summary", ""),
            ),
        )

        # Initial actor states
        for state in init.get("actor_states", []):
            c.execute(
                """INSERT INTO actor_states
                (node_id, actor_id, mood, energy, safety, social, esteem,
                 location, ticking_clock)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    root_nid, state["actor_id"],
                    state.get("mood", 2), state.get("energy", 3),
                    state.get("safety", 3), state.get("social", 3),
                    state.get("esteem", 3), state.get("location", ""),
                    state.get("ticking_clock", ""),
                ),
            )

        # Initial relation edges
        for edge in init.get("relation_edges", []):
            c.execute(
                """INSERT INTO relation_edges
                (node_id, source_actor_id, target_actor_id,
                 trust, affinity, tension, bond_event)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    root_nid, edge["source_actor_id"],
                    edge["target_actor_id"],
                    edge.get("trust", 0), edge.get("affinity", 0),
                    edge.get("tension", 0), edge.get("bond_event", ""),
                ),
            )

    return sid
