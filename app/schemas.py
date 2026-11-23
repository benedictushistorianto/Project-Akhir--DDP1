"""
app/schemas.py — Kontrak Pydantic v2 Bersama (TARGET BEKU HARI 2)

Semua model memakai ConfigDict(extra="forbid") agar JSON asing ditolak.
Tidak ada ge/le/max_length di level Field (supaya JSON Schema yang dikirim
ke LLM kompatibel dengan semua provider). Validasi rentang angka dilakukan
seluruhnya oleh @field_validator Python di sisi server.

Alur singkat:
1. LLM mengembalikan JSON yang diparse jadi TurnResponse.
2. state_mutator.py membaca ActorStateDelta dan RelationDelta dari
   TurnResponse, lalu menerapkan perubahan ke SQLite (dengan clamping).
3. Frontend menerima NodeDTO sebagai respons API /api/turns.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


# ── Kontrak Output LLM ──────────────────────────────────────

class ActorStateDelta(BaseModel):
    """Perubahan status satu aktor yang dikembalikan LLM."""
    model_config = ConfigDict(extra="forbid")

    actor_id: str
    mood: int | None = None
    energy: int | None = None
    safety: int | None = None
    social: int | None = None
    esteem: int | None = None
    location: str | None = None
    ticking_clock: str | None = None

    @field_validator("mood", mode="before")
    @classmethod
    def clamp_mood(cls, v: int | None) -> int | None:
        if v is None:
            return v
        return max(1, min(3, int(v)))

    @field_validator("energy", "safety", "social", "esteem", mode="before")
    @classmethod
    def clamp_needs(cls, v: int | None) -> int | None:
        if v is None:
            return v
        return max(1, min(5, int(v)))


class RelationDelta(BaseModel):
    """Perubahan relasi berarah dari source ke target."""
    model_config = ConfigDict(extra="forbid")

    source_actor_id: str
    target_actor_id: str
    trust: int | None = None
    affinity: int | None = None
    tension: int | None = None
    bond_event: str | None = None

    @field_validator("trust", "affinity", mode="before")
    @classmethod
    def clamp_trust_affinity(cls, v: int | None) -> int | None:
        if v is None:
            return v
        return max(-5, min(5, int(v)))

    @field_validator("tension", mode="before")
    @classmethod
    def clamp_tension(cls, v: int | None) -> int | None:
        if v is None:
            return v
        return max(0, min(5, int(v)))


class CausalAnchorDelta(BaseModel):
    """Jangkar kausal baru yang diusulkan oleh LLM."""
    model_config = ConfigDict(extra="forbid")

    summary: str
    severity: int = 1

    @field_validator("severity", mode="before")
    @classmethod
    def clamp_severity(cls, v: int) -> int:
        return max(1, min(5, int(v)))


class TurnResponse(BaseModel):
    """Kontrak JSON keseluruhan yang dikembalikan LLM setiap giliran.

    Field ini HARUS datar dan tanpa additional properties agar
    kompatibel dengan constrained decoding semua provider.
    """
    model_config = ConfigDict(extra="forbid")

    narrative: str
    actor_deltas: list[ActorStateDelta] = []
    relation_deltas: list[RelationDelta] = []
    new_anchor: CausalAnchorDelta | None = None
    updated_arc_summary: str = ""
    suggested_choices: list[str] = []


# ── Konfigurasi LLM (dari UI / API) ─────────────────────────

class LLMConfig(BaseModel):
    """Konfigurasi provider LLM yang dikirim frontend."""
    model_config = ConfigDict(extra="forbid")

    provider: str = "mock"
    base_url: str = ""
    model_name: str = ""
    temperature: float = 0.7
    max_tokens: int = 1024

    @field_validator("temperature", mode="before")
    @classmethod
    def clamp_temperature(cls, v: float) -> float:
        return max(0.0, min(2.0, float(v)))

    @field_validator("max_tokens", mode="before")
    @classmethod
    def clamp_max_tokens(cls, v: int) -> int:
        return max(64, min(4096, int(v)))


# ── DTO untuk Respons API ────────────────────────────────────

class ActorCoreDTO(BaseModel):
    """DTO aktor inti (read-only dari actor_cores)."""
    model_config = ConfigDict(extra="forbid")

    actor_id: str
    name: str
    role: str = ""
    traits: list[str] = []
    backstory: str = ""


class ActorStateDTO(BaseModel):
    """DTO snapshot status aktor pada satu simpul."""
    model_config = ConfigDict(extra="forbid")

    actor_id: str
    mood: int = 2
    energy: int = 3
    safety: int = 3
    social: int = 3
    esteem: int = 3
    location: str = ""
    ticking_clock: str = ""


class RelationEdgeDTO(BaseModel):
    """DTO relasi berarah pada satu simpul."""
    model_config = ConfigDict(extra="forbid")

    source_actor_id: str
    target_actor_id: str
    trust: int = 0
    affinity: int = 0
    tension: int = 0
    bond_event: str = ""


class CausalAnchorDTO(BaseModel):
    """DTO Jangkar Kausal."""
    model_config = ConfigDict(extra="forbid")

    anchor_id: str
    origin_node_id: str
    summary: str
    severity: int = 1
    is_resolved: bool = False


class NodeDTO(BaseModel):
    """DTO simpul Git-DAG (dikembalikan oleh endpoint /api/turns)."""
    model_config = ConfigDict(extra="forbid")

    node_id: str
    scenario_id: str
    branch_id: str
    parent_id: str | None = None
    turn_index: int = 0
    user_action: str = ""
    narrative: str = ""
    arc_summary: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    is_fallback: bool = False
    actor_states: list[ActorStateDTO] = []
    relation_edges: list[RelationEdgeDTO] = []
    new_anchor: CausalAnchorDTO | None = None
    suggested_choices: list[str] = []


class BranchDTO(BaseModel):
    """DTO cabang skenario."""
    model_config = ConfigDict(extra="forbid")

    branch_id: str
    scenario_id: str
    name: str = "main"
    head_node_id: str | None = None
    color: str = "#2DD4BF"


class ScenarioDTO(BaseModel):
    """DTO skenario lengkap."""
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    title: str
    premise: str = ""
    actor_cores: list[ActorCoreDTO] = []
    branches: list[BranchDTO] = []


class GraphDTO(BaseModel):
    """DTO graf DAG lengkap untuk satu skenario."""
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    nodes: list[NodeDTO] = []
    branches: list[BranchDTO] = []
    head_node_id: str | None = None
    causal_anchors: list[CausalAnchorDTO] = []


# ── Request Bodies ───────────────────────────────────────────

class TurnRequest(BaseModel):
    """Payload yang dikirim frontend untuk menjalankan satu giliran."""
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    parent_node_id: str
    branch_id: str
    user_action: str
    llm_config: LLMConfig = LLMConfig()


class ForkRequest(BaseModel):
    """Payload untuk membuat cabang baru dari simpul tertentu."""
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    from_node_id: str
    new_branch_name: str


class CheckoutRequest(BaseModel):
    """Payload untuk checkout ke simpul/cabang tertentu."""
    model_config = ConfigDict(extra="forbid")

    branch_id: str
    target_node_id: str | None = None
