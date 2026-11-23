"""
app/engine/context_compiler.py — Dynamic Context Compiler O(1)

Merakit paket `messages` (maks 2 pesan: system + user) yang dikirim
ke LLM, dengan plafon ketat input <= 2.200 token, sehingga biaya
prompt tetap O(1) sepanjang giliran mana pun.

Dua zona:
1. ZONA PREFIKS STATIS (messages[0], role "system") — aturan roleplay,
   kontrak JSON TurnResponse, dan daftar actor_cores diurutkan
   deterministik menurut actor_id. Identik byte-for-byte antar-giliran
   pada skenario yang sama (KV prefix cache hit).
2. ZONA SUFIKS DINAMIS (messages[1], role "user") — actor_states terkini,
   matriks relation_edges, direktif Sim Pulse & Ticking Clock, maks 10
   Jangkar Kausal garis keturunan aktif (severity DESC), arc_summary
   (<= 240 token), 2 giliran narasi bersih terakhir (tanpa JSON delta),
   dan aksi pengguna saat ini.

Penghitung token: estimasi konservatif Bahasa Indonesia
~1.35 token/kata, diaproksimasi `max(1, len(text) // 3)`.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field

from app.engine.dag_repo import get_lineage, get_lineage_anchors, get_node_state
from app.engine.sim_pulse import generate_sim_pulse

# ── Konstanta Anggaran ───────────────────────────────────────

BUDGET_TOTAL_TOKENS = 2200
BUDGET_STATIC_TOKENS = 700      # plafon zona prefiks statis
BUDGET_DYNAMIC_TOKENS = 1500    # plafon zona sufiks dinamis
ARC_SUMMARY_TOKEN_CAP = 240     # plafon arc_summary
MAX_ACTIVE_ANCHORS = 10         # maks Jangkar Kausal aktif
LAST_NARRATIVE_WINDOW = 2       # sliding window narasi bersih terakhir


def est_tokens(text: str) -> int:
    """Estimasi token konservatif: ~1.35 token/kata, diaproksimasi
    dengan panjang karakter // 3 (aman untuk Bahasa Indonesia)."""
    return max(1, len(text) // 3)


@dataclass
class CompiledContext:
    """Hasil kompilasi siap kirim ke LLM."""

    messages: list[dict] = field(default_factory=list)
    estimated_input_tokens: int = 0


# ── Zona Prefiks Statis ─────────────────────────────────────

_ROLE_RULES_ID = (
    "Kamu adalah pemandu roleplay interaktif apa-itu-nya-Whenyhh.ai "
    "(skenario-and-roleplay-v1-5-id). Aturannya:\n"
    "1. Narasikan konsekuensi aksi pengguna secara imersif dalam Bahasa Indonesia.\n"
    "2. Karakter tetap konsisten dengan core mereka; tidak ada alur yang melompat.\n"
    "3. Jangkar kausal aktif harus terus berpengaruh hingga benar-benar terurai.\n"
    "4. Jangan mengarang identitas/properti baru di luar daftar actor_core.\n"
    "5. Panjang narasi target sekitar 120-180 kata.\n"
)

_CONTRACT_ID = (
    'Kembalikan HANYA satu objek JSON valid (tanpa teks lain, tanpa code fence) '
    'dengan bentuk persis:\n'
    '{"narrative": string, "actor_deltas": [{"actor_id": string, '
    '"mood": int 1..3, "energy": int 1..5, "safety": int 1..5, '
    '"social": int 1..5, "esteem": int 1..5, "location": string, '
    '"ticking_clock": string}], "relation_deltas": [{"source_actor_id": '
    'string, "target_actor_id": string, "trust": int -5..5, "affinity": '
    'int -5..5, "tension": int 0..5, "bond_event": string}], '
    '"new_anchor": null atau {"summary": string, "severity": int 1..5}, '
    '"updated_arc_summary": string, "suggested_choices": [string]}\n'
    'Field actor_deltas dan relation_deltas boleh berupa daftar kosong. '
    "Nilai None dihilangkan dari JSON."
)


def _build_static_prefix(
    conn: sqlite3.Connection, scenario_id: str
) -> str:
    """Rakit zona prefiks statis; deterministik per skenario.

    Aktor diurutkan berdasarkan actor_id agar byte-for-byte identik
    antar-giliran.
    """
    scen = conn.execute(
        "SELECT title, premise, world_rules FROM scenarios WHERE scenario_id = ?",
        (scenario_id,),
    ).fetchone()

    parts = [_ROLE_RULES_ID]
    if scen is not None:
        parts.append(f"JUDUL Skenario: {scen['title']}")
        if scen["premise"]:
            parts.append(f"PREMISE: {scen['premise']}")
        if scen["world_rules"]:
            parts.append(f"ATURAN DUNIA: {scen['world_rules']}")

    actor_rows = conn.execute(
        """SELECT actor_id, name, role, traits, backstory
        FROM actor_cores WHERE scenario_id = ?
        ORDER BY actor_id""",
        (scenario_id,),
    ).fetchall()
    if actor_rows:
        lines = ["DAFTAR AKTOR CORE (satu-satunya aktor yang sah):"]
        for a in actor_rows:
            traits = json.loads(a["traits"]) if a["traits"] else []
            lines.append(
                f"- {a['actor_id']} | {a['name']} | peran: {a['role']} | "
                f"trait: {', '.join(traits) or '-'} | latar: {a['backstory'] or '-'}"
            )
        parts.append("\n".join(lines))

    parts.append(_CONTRACT_ID)
    return "\n\n".join(parts)


# ── Zona Sufiks Dinamis ─────────────────────────────────────

def _fmt_actor_states(states: list) -> str:
    if not states:
        return "(belum ada state aktor tercatat)"
    lines = []
    for s in states:
        line = (
            f"{s.actor_id}: mood {s.mood} | energi {s.energy} | aman {s.safety} | "
            f"sosial {s.social} | hormat {s.esteem} | lokasi: {s.location or '-'}"
        )
        if s.ticking_clock:
            line += f" | jam: {s.ticking_clock}"
        lines.append(line)
    return "\n".join(lines)


def _fmt_relation_edges(edges: list) -> str:
    if not edges:
        return "(belum ada relasi tercatat)"
    lines = []
    for e in edges:
        lines.append(
            f"{e.source_actor_id} -> {e.target_actor_id}: "
            f"trust {e.trust} | affinity {e.affinity} | tension {e.tension}"
            + (f" | peristiwa: {e.bond_event}" if e.bond_event else "")
        )
    return "\n".join(lines)


def _fmt_anchors(anchors: list) -> str:
    if not anchors:
        return "(belum ada jangkar kausal aktif)"
    lines = []
    for a in anchors:
        lines.append(f"[S{a.severity}] {a.summary} (berasal dari {a.origin_node_id})")
    return "\n".join(lines)


def _build_dynamic_suffix(
    conn: sqlite3.Connection,
    *,
    scenario_id: str,
    parent_node_id: str,
    user_action: str,
) -> str:
    """Rakit zona sufiks dinamis, memangkas diri bila melewati anggaran."""
    parent_row = conn.execute(
        "SELECT turn_index, narrative, arc_summary FROM nodes WHERE node_id = ?",
        (parent_node_id,),
    ).fetchone()
    turn_index = (parent_row["turn_index"] + 1) if parent_row else 1
    rng_seed_row = conn.execute(
        "SELECT rng_seed FROM scenarios WHERE scenario_id = ?",
        (scenario_id,),
    ).fetchone()
    rng_seed = rng_seed_row["rng_seed"] if rng_seed_row and rng_seed_row["rng_seed"] else 42

    pulse = generate_sim_pulse(
        rng_seed=rng_seed, node_id=parent_node_id, turn_index=turn_index
    )

    states, edges = get_node_state(conn, parent_node_id)
    anchors = get_lineage_anchors(conn, parent_node_id, limit=MAX_ACTIVE_ANCHORS)

    # 2 narasi bersih terakhir dari garis keturunan (tanpa JSON delta)
    lineage_asc = list(reversed(get_lineage(conn, parent_node_id)))
    window_ids = lineage_asc[-LAST_NARRATIVE_WINDOW:]
    recent_lines = []
    if window_ids:
        placeholders = ",".join("?" * len(window_ids))
        recent_rows = conn.execute(
            f"""SELECT node_id, turn_index, user_action, narrative FROM nodes
            WHERE node_id IN ({placeholders})""",
            window_ids,
        ).fetchall()
        recent_nodes = sorted(recent_rows, key=lambda n: n["turn_index"])
        for n in recent_nodes:
            if n["narrative"]:
                suffix = f" (pilihan sebelumnya: {n['user_action']})" if n["user_action"] else ""
                recent_lines.append(f"- {n['narrative']}{suffix}")

    # ── Rakit blok (dalam urutan prioritas anggaran) ──────────
    arc_summary = (parent_row["arc_summary"] or "") if parent_row else ""
    if est_tokens(arc_summary) > ARC_SUMMARY_TOKEN_CAP:
        # Pangkas per kata: ambil sebanyak kata yang masih muat di plafon.
        words = arc_summary.split()
        kept = 0
        for i in range(1, len(words) + 1):
            if est_tokens(" ".join(words[:i])) > ARC_SUMMARY_TOKEN_CAP:
                break
            kept = i
        arc_summary = " ".join(words[:kept]) + " ..."

    blocks = [
        ("STATE AKTOR TERKINI\n", _fmt_actor_states(states)),
        ("MATRIKS RELASI\n", _fmt_relation_edges(edges)),
        ("SIM PULSE & JAM BERDENGUNG\n",
         f"{pulse.directive} | {pulse.ticking_clock}"),
        ("JANGKAR KAUSAL AKTIF (maks 10, urut severity)\n", _fmt_anchors(anchors)),
        ("RINGKASAN ARC\n", arc_summary or "(belum ada ringkasan)"),
        ("NARASI TERAKHIR (2 giliran bersih)\n",
         "\n".join(recent_lines) if recent_lines else "(giliran pertama)"),
        ("AKSI PENGGUNA SAAT INI\n", user_action),
    ]

    # ── Pemangkas Anggaran: buang jangkar mulai bawah, lalu
    #    narasi, lalu arc_summary — kecuali blok wajib terakhir ─
    while est_tokens("\n\n".join(b[1] for b in blocks)) > BUDGET_DYNAMIC_TOKENS:
        anchor_block = blocks[3]
        anchor_lines = anchor_block[1].splitlines()
        if len(anchor_lines) > 0 and "belum ada jangkar" not in anchor_block[1]:
            del anchor_lines[-1]
            blocks[3] = (anchor_block[0],
                         "\n".join(anchor_lines) if anchor_lines
                         else "(dipangkas karena anggaran token)")
            continue
        narrative_block = blocks[5]
        narrative_lines = narrative_block[1].splitlines()
        if narrative_lines:
            del narrative_lines[-1]
            blocks[5] = (narrative_block[0],
                         "\n".join(narrative_lines) if narrative_lines
                         else "(dipangkas karena anggaran token)")
            continue
        if blocks[4][1] != "(belum ada ringkasan)":
            blocks[4] = (blocks[4][0], "(ringkasan arc dipangkas karena anggaran token)")
            continue
        break  # semua blok opsional habis; biarkan blok wajib utuh

    return "\n\n".join(f"{hdr}{body}" for hdr, body in blocks)


# ── API Utama ────────────────────────────────────────────────

def compile_context(
    conn: sqlite3.Connection,
    *,
    scenario_id: str,
    parent_node_id: str,
    user_action: str,
) -> CompiledContext:
    """Kompilasi paket konteks O(1) <= 2.200 token untuk satu giliran.

    Return: CompiledContext berisi list `messages` siap kirim.
    """
    static = _build_static_prefix(conn, scenario_id)
    dynamic = _build_dynamic_suffix(
        conn, scenario_id=scenario_id,
        parent_node_id=parent_node_id, user_action=user_action,
    )

    messages = [
        {"role": "system", "content": static},
        {"role": "user", "content": dynamic},
    ]
    total = est_tokens(static) + est_tokens(dynamic)
    return CompiledContext(messages=messages, estimated_input_tokens=total)
