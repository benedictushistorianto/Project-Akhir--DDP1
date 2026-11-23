-- Whenyhh.ai — SQLite Schema (WAL + STRICT)
-- 7 tabel inti untuk Externalized State Engine dan Git-DAG imutabel.
-- Dijalankan sekali oleh init_db() pada lifespan FastAPI.

---------------------------------------------------------------
-- 1. scenarios: Metadata skenario (seed atau kustom)
---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scenarios (
    scenario_id  TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    premise      TEXT NOT NULL DEFAULT '',
    world_rules  TEXT NOT NULL DEFAULT '',
    rng_seed     INTEGER NOT NULL DEFAULT 42,
    created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;

---------------------------------------------------------------
-- 2. actor_cores: Identitas permanen karakter (tidak berubah
--    lintas giliran/cabang; satu skenario -> N aktor).
---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS actor_cores (
    actor_id     TEXT NOT NULL,
    scenario_id  TEXT NOT NULL REFERENCES scenarios(scenario_id),
    name         TEXT NOT NULL,
    role         TEXT NOT NULL DEFAULT '',
    traits       TEXT NOT NULL DEFAULT '[]',
    backstory    TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (actor_id, scenario_id)
) STRICT;

---------------------------------------------------------------
-- 3. branches: Cabang skenario (setiap skenario punya >= 1
--    cabang "main"). head_node_id menunjuk simpul aktif.
---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS branches (
    branch_id    TEXT PRIMARY KEY,
    scenario_id  TEXT NOT NULL REFERENCES scenarios(scenario_id),
    name         TEXT NOT NULL DEFAULT 'main',
    head_node_id TEXT,
    color        TEXT NOT NULL DEFAULT '#2DD4BF',
    created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;

---------------------------------------------------------------
-- 4. nodes: Simpul imutabel pohon Git-DAG.
--    parent_id NULL = simpul akar (S00).
---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS nodes (
    node_id        TEXT PRIMARY KEY,
    scenario_id    TEXT NOT NULL REFERENCES scenarios(scenario_id),
    branch_id      TEXT NOT NULL REFERENCES branches(branch_id),
    parent_id      TEXT REFERENCES nodes(node_id),
    turn_index     INTEGER NOT NULL DEFAULT 0,
    user_action    TEXT NOT NULL DEFAULT '',
    narrative      TEXT NOT NULL DEFAULT '',
    arc_summary    TEXT NOT NULL DEFAULT '',
    prompt_tokens  INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    latency_ms     INTEGER NOT NULL DEFAULT 0,
    is_fallback    INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;

CREATE INDEX IF NOT EXISTS idx_nodes_parent ON nodes(parent_id);
CREATE INDEX IF NOT EXISTS idx_nodes_branch_turn ON nodes(branch_id, turn_index);

---------------------------------------------------------------
-- 5. actor_states: Status dinamis aktor pada setiap simpul.
--    PK (node_id, actor_id) => snapshot imutabel per giliran.
---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS actor_states (
    node_id      TEXT NOT NULL REFERENCES nodes(node_id),
    actor_id     TEXT NOT NULL,
    mood         INTEGER NOT NULL DEFAULT 2,
    energy       INTEGER NOT NULL DEFAULT 3,
    safety       INTEGER NOT NULL DEFAULT 3,
    social       INTEGER NOT NULL DEFAULT 3,
    esteem       INTEGER NOT NULL DEFAULT 3,
    location     TEXT NOT NULL DEFAULT '',
    ticking_clock TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (node_id, actor_id)
) STRICT;

---------------------------------------------------------------
-- 6. relation_edges: Relasi berarah asimetris antar-aktor
--    pada setiap simpul. (A->B) terpisah dari (B->A).
---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS relation_edges (
    node_id          TEXT NOT NULL REFERENCES nodes(node_id),
    source_actor_id  TEXT NOT NULL,
    target_actor_id  TEXT NOT NULL,
    trust            INTEGER NOT NULL DEFAULT 0,
    affinity         INTEGER NOT NULL DEFAULT 0,
    tension          INTEGER NOT NULL DEFAULT 0,
    bond_event       TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (node_id, source_actor_id, target_actor_id)
) STRICT;

---------------------------------------------------------------
-- 7. causal_anchors: Jangkar Kausal terikat pada simpul asal.
--    Disaring melalui Recursive CTE lineage aktif.
---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS causal_anchors (
    anchor_id       TEXT PRIMARY KEY,
    scenario_id     TEXT NOT NULL REFERENCES scenarios(scenario_id),
    origin_node_id  TEXT NOT NULL REFERENCES nodes(node_id),
    summary         TEXT NOT NULL,
    severity        INTEGER NOT NULL DEFAULT 1,
    is_resolved     INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;

CREATE INDEX IF NOT EXISTS idx_anchors_origin ON causal_anchors(origin_node_id);
