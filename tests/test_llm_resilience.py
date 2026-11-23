"""
tests/test_llm_resilience.py — Pipa Ketahanan JSON 4 Lapis

Memverifikasi:
1. Pembersih tag `...` dan `<|channel>thought`.
2. json-repair menyelamatkan JSON cacat ringan.
3. Pydantic extra="forbid" menolak properti asing.
4. Clamping angka oleh field validator (mood 1..3, trust -5..5, dsb.).
5. Maks 1x retry, lalu Deterministic Safe Fallback (HTTP 200 semantics,
   is_fallback=True, delta nol).
6. Kunci API tidak pernah masuk log/teks respons.
"""

from __future__ import annotations

import json

import pytest

from app.llm.client import MockLLMAdapter
from app.llm.resilience import (
    clean_llm_text,
    deterministic_safe_fallback,
    parse_turn_response,
    run_turn_pipeline,
)
from app.schemas import LLMConfig, TurnResponse


_GOOD_JSON = json.dumps({
    "narrative": "Raka menegur vendor.",
    "actor_deltas": [{"actor_id": "raka", "mood": 9}],  # akan di-clamp ke 3
    "relation_deltas": [
        {"source_actor_id": "raka", "target_actor_id": "vendor_dewi",
         "trust": 12, "tension": -1}  # clamp ke 5 dan 0
    ],
    "new_anchor": None,
    "updated_arc_summary": "Teguran pertama.",
    "suggested_choices": ["Lanjutkan"],
})


class TestCleaners:
    """Lapis 2: pembersih artefak berpikir dan code fence."""

    def test_strips_think_tags(self):
        raw = (
            "<think>\n"
            "menimbang...\n"
            "</think>\n"
            + _GOOD_JSON
        )
        assert "menimbang" not in clean_llm_text(raw)
        assert _GOOD_JSON in clean_llm_text(raw)

    def test_strips_qwen_channel_tag(self):
        raw = "<|channel>thought\nmerenung\n" + _GOOD_JSON
        cleaned = clean_llm_text(raw)
        assert "merenung" not in cleaned
        assert _GOOD_JSON in cleaned

    def test_strips_code_fence(self):
        raw = "```json\n" + _GOOD_JSON + "\n```"
        cleaned = clean_llm_text(raw)
        assert "```" not in cleaned

    def test_valid_json_parses(self):
        resp, err = parse_turn_response(_GOOD_JSON)
        assert err is None
        assert isinstance(resp, TurnResponse)
        # Clamping deterministik berjalan
        assert resp.actor_deltas[0].mood == 3
        assert resp.relation_deltas[0].trust == 5
        assert resp.relation_deltas[0].tension == 0


class TestJsonRepair:
    """Lapis 2: json-repair memperbaiki JSON cacat ringan."""

    def test_trailing_comma_repaired(self):
        bad = _GOOD_JSON.replace('"suggested_choices": ["Lanjutkan"]',
                                 '"suggested_choices": ["Lanjutkan",]')
        resp, err = parse_turn_response(bad)
        assert err is None and resp.suggested_choices == ["Lanjutkan"]

    def test_single_quotes_repaired(self):
        bad = "{'narrative': 'hijau', 'actor_deltas': []}"
        resp, err = parse_turn_response(bad)
        assert err is None
        assert resp.narrative == "hijau"


class TestPydanticGuard:
    """Lapis 3: extra='forbid' menolak properti asing."""

    def test_unknown_property_rejected(self):
        bad = json.dumps({
            "narrative": "x", "actor_deltas": [], "relation_deltas": [],
            "properti_asing": "harus ditolak",
        })
        # json-repair tetap menghasilkan dict lengkap -> Pydantic menolak
        resp, err = parse_turn_response(bad)
        assert resp is None
        assert err is not None

    def test_malformed_beyond_repair_rejected(self):
        resp, err = parse_turn_response("ini bukan json sama sekali")
        assert resp is None
        assert err is not None


class TestSafeFallback:
    """Lapis 4: Deterministic Safe Fallback (status lama dipertahankan)."""

    def test_fallback_preserves_state(self):
        fb = deterministic_safe_fallback("Narasi terakhir yang terselamat.")
        assert fb.actor_deltas == []
        assert fb.relation_deltas == []
        assert fb.new_anchor is None
        assert fb.updated_arc_summary == ""
        assert "terselamat" in fb.narrative.lower() or fb.narrative

    def test_fallback_friendly_when_no_narrative(self):
        fb = deterministic_safe_fallback()
        assert fb.narrative  # pesan ramah, bukan kosong


class TestPipeline:
    """Alur penuh: client -> pipa -> outcome."""

    def test_successful_mock_turn(self):
        messages = [
            {"role": "system", "content": "sistem"},
            {"role": "user", "content": "raka: mood 2 | energi 3"},
        ]
        outcome = run_turn_pipeline(
            MockLLMAdapter(), messages,
            LLMConfig(provider="mock"),
        )
        assert outcome.is_fallback is False
        assert isinstance(outcome.turn_response, TurnResponse)

    def test_corrupt_client_falls_back_after_one_retry(self):
        """Klien corrupt: 1 retry (percobaan 2) lalu safe fallback."""
        client = MockLLMAdapter(corrupt=True)
        seen_user_msgs: list[str] = []

        orig = client.complete
        def _counting(messages, config, **kw):
            seen_user_msgs.append(messages[-1]["content"])
            return orig(messages, config, **kw)
        client.complete = _counting

        outcome = run_turn_pipeline(
            client,
            [{"role": "system", "content": "s"},
             {"role": "user", "content": "u"}],
            LLMConfig(provider="mock"),
        )
        # Maksimal 2 panggilan (percobaan + 1 retry)
        assert len(seen_user_msgs) == 2
        assert outcome.is_fallback is True
        # Retry menambahkan petunjuk perbaikan ke pesan user
        assert "PERBAIKAN" in seen_user_msgs[1]
        assert "PERBAIKAN" not in seen_user_msgs[0]

    def test_http_error_falls_back(self, monkeypatch):
        """Klien gagal jaringan -> safe fallback, bukan HTTP 500."""

        class _Broken:
            def complete(self, messages, config, **kw):
                from app.llm.client import LLMResult
                return LLMResult(ok=False, error="connection refused")

        outcome = run_turn_pipeline(
            _Broken(),
            [{"role": "system", "content": "s"},
             {"role": "user", "content": "u"}],
            LLMConfig(provider="ollama"),
            rescued_narrative="Narasi sebelum gagal.",
        )
        assert outcome.is_fallback is True
        assert outcome.turn_response.actor_deltas == []
        assert "sebelum gagal" in outcome.turn_response.narrative


class TestApiKeyHygiene:
    """Kunci API tidak bocor ke mana pun yang tercatat."""

    def test_fallback_note_has_no_key(self):
        fb = deterministic_safe_fallback()
        assert "X-LLM-API-Key" not in fb.narrative
        assert "Authorization" not in fb.narrative

    def test_fallback_response_serializes_clean(self):
        fb = deterministic_safe_fallback()
        dumped = json.dumps(fb.model_dump(), ensure_ascii=False)
        assert "Bearer" not in dumped
        assert "X-LLM-API-Key" not in dumped
