"""
app/routers/scenarios.py — Endpoint Skenario

Endpoint:
- GET  /api/scenarios                      -> Daftar semua skenario
- GET  /api/scenarios/{scenario_id}        -> Detail satu skenario
- GET  /api/scenarios/{scenario_id}/graph   -> Graf DAG lengkap
- GET  /api/scenarios/{scenario_id}/export  -> Ekspor JSON atau Markdown
"""

from __future__ import annotations

import json
from fastapi import APIRouter, HTTPException, Query, Request, Response

from app.engine.dag_repo import get_graph, get_scenario_list, get_lineage

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("")
async def list_scenarios(request: Request) -> list[dict]:
    """Daftar semua skenario yang tersedia."""
    conn = request.app.state.db_conn
    scenarios = get_scenario_list(conn)
    return [s.model_dump() for s in scenarios]


@router.get("/{scenario_id}")
async def get_scenario(scenario_id: str, request: Request) -> dict:
    """Detail satu skenario beserta aktor dan cabang."""
    conn = request.app.state.db_conn
    scenarios = get_scenario_list(conn)
    for s in scenarios:
        if s.scenario_id == scenario_id:
            return s.model_dump()
    raise HTTPException(status_code=404, detail="Skenario tidak ditemukan")


@router.get("/{scenario_id}/graph")
async def get_scenario_graph(scenario_id: str, request: Request) -> dict:
    """Graf DAG lengkap untuk satu skenario."""
    conn = request.app.state.db_conn

    # Pastikan skenario ada
    row = conn.execute(
        "SELECT scenario_id FROM scenarios WHERE scenario_id = ?",
        (scenario_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Skenario tidak ditemukan")

    graph = get_graph(conn, scenario_id)
    return graph.model_dump()


@router.get("/{scenario_id}/export")
async def export_scenario(
    scenario_id: str,
    request: Request,
    format: str = Query("json", pattern="^(json|md)$"),
) -> Response:
    """Ekspor skenario ke JSON atau Markdown untuk unduhan lokal."""
    conn = request.app.state.db_conn

    row = conn.execute(
        "SELECT * FROM scenarios WHERE scenario_id = ?",
        (scenario_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Skenario tidak ditemukan")

    graph = get_graph(conn, scenario_id)

    if format == "json":
        content = json.dumps(graph.model_dump(), ensure_ascii=False, indent=2)
        return Response(
            content=content,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{scenario_id}.json"'
            },
        )

    # format == "md"
    lines = [
        f"# {row['title']}",
        "",
        f"**Premis:** {row['premise']}",
        "",
        "---",
        "",
    ]

    # Ambil cabang main
    main_branch = conn.execute(
        "SELECT * FROM branches WHERE scenario_id = ? AND name = 'main'",
        (scenario_id,),
    ).fetchone()

    if main_branch and main_branch["head_node_id"]:
        lineage_ids = get_lineage(conn, main_branch["head_node_id"])
        lineage_ids.reverse()  # dari akar ke daun

        for nid in lineage_ids:
            node = conn.execute(
                "SELECT * FROM nodes WHERE node_id = ?", (nid,)
            ).fetchone()
            if node:
                lines.append(f"## Giliran {node['turn_index']} ({nid[:8]})")
                if node["user_action"]:
                    lines.append(f"\n**Aksi:** {node['user_action']}")
                if node["narrative"]:
                    lines.append(f"\n{node['narrative']}")
                lines.append("")

    content = "\n".join(lines)
    return Response(
        content=content,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{scenario_id}.md"'
        },
    )
