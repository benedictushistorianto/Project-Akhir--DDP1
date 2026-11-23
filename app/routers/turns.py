"""
app/routers/turns.py — Endpoint Giliran, Fork, dan Checkout

Endpoint:
- POST /api/turns             -> Eksekusi satu giliran (placeholder LLM: mock)
- POST /api/branches/fork     -> Fork cabang baru
- POST /api/branches/checkout -> Pindah ke simpul/cabang lain
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.engine.context_compiler import compile_context
from app.engine.dag_repo import (
    checkout_branch,
    commit_turn,
    fork_branch,
    get_lineage,
    get_lineage_anchors,
    get_node_state,
)
from app.engine.state_mutator import apply_turn_deltas
from app.llm.client import make_client
from app.llm.resilience import run_turn_pipeline
from app.schemas import (
    CheckoutRequest,
    ForkRequest,
    NodeDTO,
    TurnRequest,
    TurnResponse,
    CausalAnchorDTO,
)

router = APIRouter(tags=["turns"])


def _get_valid_actor_ids(conn, scenario_id: str) -> set[str]:
    """Ambil set actor_id yang terdaftar di scenario ini."""
    rows = conn.execute(
        "SELECT actor_id FROM actor_cores WHERE scenario_id = ?",
        (scenario_id,),
    ).fetchall()
    return {r["actor_id"] for r in rows}


@router.post("/api/turns", status_code=201)
async def execute_turn(body: TurnRequest, request: Request) -> dict:
    """Jalankan satu giliran simulasi.

    Alur:
    1. Validasi skenario, branch, dan parent_node ada.
    2. compile_context() merakit paket O(1) <= 2.200 token.
    3. make_client() memilih provider (mock/ollama/lmstudio/byom).
    4. run_turn_pipeline() menjalankan pipa ketahanan 4 lapis;
       gagal total -> Deterministic Safe Fallback (HTTP tetap 200).
    5. apply_turn_deltas() + commit_turn() menyimpan simpul baru.
    6. Kembalikan NodeDTO lengkap dengan telemetri token & latensi.
    """
    conn = request.app.state.db_conn

    # Validasi skenario
    scenario = conn.execute(
        "SELECT scenario_id FROM scenarios WHERE scenario_id = ?",
        (body.scenario_id,),
    ).fetchone()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Skenario tidak ditemukan")

    # Validasi branch
    branch = conn.execute(
        "SELECT branch_id FROM branches WHERE branch_id = ?",
        (body.branch_id,),
    ).fetchone()
    if branch is None:
        raise HTTPException(status_code=404, detail="Branch tidak ditemukan")

    # Validasi parent node
    parent = conn.execute(
        "SELECT node_id FROM nodes WHERE node_id = ?",
        (body.parent_node_id,),
    ).fetchone()
    if parent is None:
        raise HTTPException(status_code=404, detail="Parent node tidak ditemukan")

    # ── Phase 2: Compiler O(1) -> LLM Gateway -> Pipa 4 Lapis ─
    compiled = compile_context(
        conn,
        scenario_id=body.scenario_id,
        parent_node_id=body.parent_node_id,
        user_action=body.user_action,
    )

    # Narasi bersih terakhir (untuk Deterministic Safe Fallback)
    lineage_ids = list(reversed(get_lineage(conn, body.parent_node_id)))
    recent_narrative = ""
    if lineage_ids:
        placeholders = ",".join("?" * len(lineage_ids[-2:]))
        rows = conn.execute(
            f"SELECT narrative FROM nodes WHERE node_id IN ({placeholders}) "
            "ORDER BY turn_index",
            lineage_ids[-2:],
        ).fetchall()
        recent_narrative = rows[-1]["narrative"] if rows else ""

    # Pilih klien: mock untuk pytest; provider lain -> OpenAI-compatible
    api_key = request.headers.get("X-LLM-API-Key", "")
    client = make_client(body.llm_config, api_key=api_key)

    outcome = run_turn_pipeline(
        client,
        compiled.messages,
        body.llm_config,
        rescued_narrative=recent_narrative,
    )
    turn_response = outcome.turn_response

    # ── Apply deltas + commit ────────────────────────────────
    valid_ids = _get_valid_actor_ids(conn, body.scenario_id)

    new_states, new_edges = apply_turn_deltas(
        conn, body.parent_node_id, turn_response, valid_ids
    )

    node_id = commit_turn(
        conn,
        scenario_id=body.scenario_id,
        branch_id=body.branch_id,
        parent_node_id=body.parent_node_id,
        user_action=body.user_action,
        turn_response=turn_response,
        actor_states=new_states,
        relation_edges=new_edges,
        prompt_tokens=outcome.prompt_tokens,
        completion_tokens=outcome.completion_tokens,
        latency_ms=outcome.latency_ms,
        is_fallback=outcome.is_fallback,
    )

    # ── Bangun NodeDTO respons ───────────────────────────────
    a_states, r_edges = get_node_state(conn, node_id)

    # Ambil jangkar baru jika ada
    new_anchor_dto = None
    if turn_response.new_anchor is not None:
        anchors = conn.execute(
            "SELECT * FROM causal_anchors WHERE origin_node_id = ?",
            (node_id,),
        ).fetchall()
        if anchors:
            a = anchors[0]
            new_anchor_dto = CausalAnchorDTO(
                anchor_id=a["anchor_id"],
                origin_node_id=a["origin_node_id"],
                summary=a["summary"],
                severity=a["severity"],
                is_resolved=bool(a["is_resolved"]),
            )

    node_row = conn.execute(
        "SELECT * FROM nodes WHERE node_id = ?", (node_id,)
    ).fetchone()

    result = NodeDTO(
        node_id=node_id,
        scenario_id=body.scenario_id,
        branch_id=body.branch_id,
        parent_id=body.parent_node_id,
        turn_index=node_row["turn_index"],
        user_action=body.user_action,
        narrative=turn_response.narrative,
        arc_summary=turn_response.updated_arc_summary,
        prompt_tokens=outcome.prompt_tokens,
        completion_tokens=outcome.completion_tokens,
        latency_ms=outcome.latency_ms,
        is_fallback=outcome.is_fallback,
        actor_states=a_states,
        relation_edges=r_edges,
        new_anchor=new_anchor_dto,
        suggested_choices=turn_response.suggested_choices,
    )

    return result.model_dump()


@router.post("/api/branches/fork", status_code=201)
async def fork(body: ForkRequest, request: Request) -> dict:
    """Buat cabang baru dari simpul tertentu."""
    conn = request.app.state.db_conn

    try:
        branch_id = fork_branch(
            conn,
            scenario_id=body.scenario_id,
            from_node_id=body.from_node_id,
            new_branch_name=body.new_branch_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    branch_row = conn.execute(
        "SELECT * FROM branches WHERE branch_id = ?", (branch_id,)
    ).fetchone()

    return {
        "branch_id": branch_row["branch_id"],
        "scenario_id": branch_row["scenario_id"],
        "name": branch_row["name"],
        "head_node_id": branch_row["head_node_id"],
        "color": branch_row["color"],
    }


@router.post("/api/branches/checkout")
async def checkout(body: CheckoutRequest, request: Request) -> dict:
    """Pindahkan head cabang ke simpul target."""
    conn = request.app.state.db_conn

    try:
        head_id = checkout_branch(
            conn,
            branch_id=body.branch_id,
            target_node_id=body.target_node_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Ambil state di node head
    a_states, r_edges = get_node_state(conn, head_id)
    anchors = get_lineage_anchors(conn, head_id)

    return {
        "branch_id": body.branch_id,
        "head_node_id": head_id,
        "actor_states": [s.model_dump() for s in a_states],
        "relation_edges": [e.model_dump() for e in r_edges],
        "causal_anchors": [a.model_dump() for a in anchors],
    }
