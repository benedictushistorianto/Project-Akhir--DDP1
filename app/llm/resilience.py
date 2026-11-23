"""
app/llm/resilience.py — Pipa Ketahanan JSON 4 Lapis + Safe Fallback

4 lapis (lapis 1 di sisi klien, lapis 2-4 di sini):
  1. Constrained decoding   -> response_format json_object (client.py)
  2. Pembersih + json-repair -> buang tag `...`,
     `<|channel>thought`, dan code fence; perbaiki JSON cacat
     memakai `json_repair`.
  3. Pydantic v2 (extra="forbid") -> clamp deterministik semua angka.
  4. Maksimal 1x self-healing retry -> tambahkan koreksi instruksi ke
     pesan user; gagal lagi -> Deterministic Safe Fallback.

Deterministic Safe Fallback (HTTP 200, is_fallback=True):
- Narasi terselamatkan (2 giliran narasi bersih terakhir) atau pesan
  ramah bila timeout.
- Status lama DIPERTAHANKAN tanpa mutasi (delta nol).
- UI menampilkan lencana peringatan kuning.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

import json_repair

from app.llm.client import LLMResult, MockLLMAdapter
from app.schemas import LLMConfig, TurnResponse

# ── Lapis 2: Pembersih ───────────────────────────────────────

_THINK_OPEN = chr(60) + "think" + chr(62)
_THINK_CLOSE = chr(60) + "/think" + chr(62)
_THINK_RE = re.compile(
    re.escape(_THINK_OPEN) + r".*?" + re.escape(_THINK_CLOSE),
    re.DOTALL,
)
_CHANNEL_TAG = "<|channel>thought"
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def clean_llm_text(raw: str) -> str:
    """Buang artefak berpikir dan code fence; sisakan teks JSON."""
    text = _THINK_RE.sub("", raw)
    if _CHANNEL_TAG in text:
        # Ambil semua konten SETELAH tag channel thinking (buang bagian thinking-nya)
        after = text.split(_CHANNEL_TAG, 1)[1]
        # Cari awal JSON '{' setelah channel tag; jika tidak ada, pakai seluruh sisa
        json_start = after.find("{")
        text = after[json_start:] if json_start != -1 else after
    fence = _FENCE_RE.search(text)
    if fence:
        text = fence.group(1)
    return text.strip()


def _extract_json_span(text: str) -> str:
    """Ambil rentang `{...}` pertama hingga kurung tertutup terakhir."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return text
    return text[start : end + 1]


# ── Lapis 2+3: Parse + Pydantic ─────────────────────────────

def parse_turn_response(raw: str) -> tuple[TurnResponse | None, str | None]:
    """Uji lapis 2 lalu 3. Return (TurnResponse|None, error|None)."""
    text = clean_llm_text(raw)
    span = _extract_json_span(text)

    # Coba langsung, lalu json-repair untuk JSON cacat
    for candidate in (span, None):
        if candidate is not None:
            try:
                data = json.loads(candidate)
                return TurnResponse.model_validate(data), None
            except (json.JSONDecodeError, Exception):
                pass
        repaired = json_repair.repair_json(span)
        try:
            data = json.loads(repaired)
            return TurnResponse.model_validate(data), None
        except Exception as e:  # ValidationError / JSONError
            if candidate is None:
                return None, f"parse gagal (repair pun gagal): {e}"

    return None, "JSON tak dapat ditagihkan ke TurnResponse"


# ── Lapis 4 + Safe Fallback ──────────────────────────────────

@dataclass
class TurnOutcome:
    """Hasil akhir satu giliran setelah pipa ketahanan."""

    turn_response: TurnResponse
    is_fallback: bool
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    note: str = ""


def deterministic_safe_fallback(
    rescued_narrative: str = "",
    *,
    prompt_tokens: int = 0,
    latency_ms: int = 0,
) -> TurnResponse:
    """Buat TurnResponse aman: status lama dipertahankan, delta nol."""
    narrative = (
        rescued_narrative
        if rescued_narrative
        else "Koneksi ke model terputus. Silakan ulangi aksi ini; "
             "status skenario tidak berubah."
    )
    return TurnResponse(
        narrative=narrative,
        actor_deltas=[],
        relation_deltas=[],
        new_anchor=None,
        updated_arc_summary="",
        suggested_choices=[],
    )


_RETRY_HINT = (
    "\n\nPERBAIKAN: Kembalikan HANYA objek JSON valid sesuai kontrak "
    "(tanpa tag thinking, tanpa code fence, tanpa teks lain)."
)


def run_turn_pipeline(
    client,
    messages: list[dict[str, str]],
    config: LLMConfig,
    *,
    rescued_narrative: str = "",
) -> TurnOutcome:
    """Jalankan pipa 4 lapis; maksimal 1x retry, lalu safe fallback.

    `client` dapat OpenAICompatClient atau MockLLMAdapter (antarmuka
    `complete(messages, config) -> LLMResult` yang sama).
    """
    last_error = ""
    for attempt in (1, 2):
        retry_messages = (
            messages
            if attempt == 1
            else messages[:-1]
            + [{**messages[-1], "content": messages[-1]["content"] + _RETRY_HINT}]
        )
        # Lapis 1: constrained decoding di payload (di klient)
        result: LLMResult = client.complete(retry_messages, config)
        if not result.ok:
            last_error = result.error
            continue  # Lapis 4: satu-satunya kesempatan retry

        # Lapis 2+3
        resp, err = parse_turn_response(result.raw_text)
        if resp is not None:
            return TurnOutcome(
                turn_response=resp,
                is_fallback=False,
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                latency_ms=result.latency_ms,
            )
        last_error = err or "respons kosong"

    # Lapis 4 habis -> Deterministic Safe Fallback
    fb = deterministic_safe_fallback(rescued_narrative)
    return TurnOutcome(
        turn_response=fb,
        is_fallback=True,
        prompt_tokens=0,
        completion_tokens=0,
        latency_ms=0,
        note=f"safe fallback setelah 2 upaya: {last_error}",
    )


# ── Utilitas tes ─────────────────────────────────────────────

def make_mock_client(corrupt: bool = False):
    """Shortcut untuk uji: MockLLMAdapter deterministik."""
    return MockLLMAdapter(corrupt=corrupt)
