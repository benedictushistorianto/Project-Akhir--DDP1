"""
app/llm/client.py — Klien LLM OpenAI-Compatible

Satu antarmuka tipis (`LLMClient`) untuk semua runtime:
- Ollama lokal      : http://127.0.0.1:11434/v1
- LM Studio lokal   : http://127.0.0.1:1234/v1
- BYOM cloud (Groq, Gemini AI Studio, OpenRouter :free)
- MockLLMAdapter    : deterministik untuk pytest

Aturan ketat:
- Kunci API (`X-LLM-API-Key`) DIHARUSKAN tidak masuk log atau database.
- Qwen3/Qwen3.5 pada Ollama: kirim `think: false` (bukan /no_think,
  bukan model_kwargs).
- `MockLLMAdapter` memakai `random.Random` dengan seed dari konten pesan
  agar outputnya deterministik dan stabil antar-panggilan berulang.
"""

from __future__ import annotations

import json
import random
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.schemas import LLMConfig

# Baris state di konteks compiler berbentuk "actor_id: mood N | energi ..."
_STATE_LINE_RE = re.compile(r"^(\S+): mood \d", re.MULTILINE)

# ── Hasil Perambatan ─────────────────────────────────────────

@dataclass
class LLMResult:
    """Hasil satu panggilan LLM (belum diparse)."""

    ok: bool
    raw_text: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    error: str = ""


# ── Preset Provider ──────────────────────────────────────────

PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "ollama": {"base_url": "http://127.0.0.1:11434/v1", "model_name": "qwen2.5:7b"},
    "lmstudio": {"base_url": "http://127.0.0.1:1234/v1", "model_name": "local-model"},
}

# Nama model Qwen yang wajib dikirim `think: false` ke Ollama.
_QWEN_MODELS = ("qwen3", "qwen3.5", "qwen2.5")


def _is_qwen(model_name: str) -> bool:
    return any(model_name.lower().startswith(p) for p in _QWEN_MODELS)


# ── Klien OpenAI-Compatible ─────────────────────────────────

class OpenAICompatClient:
    """Klien httpx tipis untuk endpoint OpenAI-compatible.

    Sengaja tanpa dependensi `openai` agar ringan dan tanpa Node.js;
    cukup POST `{base_url}/chat/completions`.
    """

    def __init__(self, config: LLMConfig, api_key: str = ""):
        self.config = config
        self.api_key = api_key

    def complete(
        self,
        messages: list[dict[str, str]],
        config: LLMConfig,
        *,
        timeout_s: float = 30.0,
        extra_body: dict[str, Any] | None = None,
    ) -> LLMResult:
        base_url = config.base_url or PROVIDER_PRESETS.get(
            config.provider, PROVIDER_PRESETS["ollama"]
        )["base_url"]
        model = config.model_name or PROVIDER_PRESETS.get(
            config.provider, {}
        ).get("model_name", "qwen2.5:7b")

        # Lapis 1 — constrained decoding via response_format (JSON mode).
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "response_format": {"type": "json_object"},
        }
        # Qwen3/Qwen3.5 pada Ollama: paksa non-thinking mode.
        if config.provider == "ollama" and _is_qwen(model):
            payload["think"] = False
        if extra_body:
            payload.update(extra_body)

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            # Header khusus proyek: kunci hanya di memori, tidak pernah dilog.
            headers["X-LLM-API-Key"] = self.api_key
            headers["Authorization"] = f"Bearer {self.api_key}"

        t0 = time.perf_counter()
        try:
            with httpx.Client(timeout=timeout_s) as client:
                resp = client.post(
                    f"{base_url.rstrip('/')}/chat/completions",
                    json=payload,
                    headers=headers,
                )
            latency_ms = int((time.perf_counter() - t0) * 1000)
            if resp.status_code != 200:
                return LLMResult(
                    ok=False, error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                    latency_ms=latency_ms,
                )
            data = resp.json()
            raw_text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return LLMResult(
                ok=True,
                raw_text=raw_text,
                prompt_tokens=int(usage.get("prompt_tokens", 0)),
                completion_tokens=int(usage.get("completion_tokens", 0)),
                latency_ms=latency_ms,
            )
        except (httpx.HTTPError, KeyError, ValueError) as e:
            latency_ms = int((time.perf_counter() - t0) * 1000)
            return LLMResult(
                ok=False,
                error=f"{type(e).__name__}: {e}",
                latency_ms=latency_ms,
            )


# ── MockLLMAdapter (pytest & offline) ───────────────────────

class MockLLMAdapter:
    """Klien deterministik tanpa jaringan untuk pengujian.

    - Seed dari hash konten pesan terakhir -> sama input, sama output.
    - Mode "corrupt" (set `corrupt = True`) sengaja mengembalikan JSON
      rusak agar suite uji bisa memverifikasi pipa ketahanan 4 lapis
      dan Deterministic Safe Fallback.
    """

    def __init__(self, corrupt: bool = False, latency_ms: int = 10):
        self.corrupt = corrupt
        self.fixed_latency_ms = latency_ms

    def complete(
        self,
        messages: list[dict[str, str]],
        config: LLMConfig,
        *,
        timeout_s: float = 30.0,
        extra_body: dict[str, Any] | None = None,
    ) -> LLMResult:
        seed_src = messages[-1]["content"] if messages else ""
        rng = random.Random(f"mock:{config.provider}:{seed_src}")

        # Ambil actor_ids dari blok "STATE AKTOR TERKINI" bila ada.
        # Baris state punya pola "actor_id: mood N | ...".
        actor_ids = _STATE_LINE_RE.findall(seed_src)

        if self.corrupt:
            # JSON "valid" secara sintaks tapi punya properti asing ->
            # lolos json-repair lalu DITOLAK Pydantic (extra="forbid"),
            # sehingga benar-benar menguji jalur Lapis 3 & Safe Fallback.
            raw = '{"narrative": "x", "properti_asing": 1}'
        else:
            mood = rng.randint(1, 3)
            delta_obj: dict[str, Any] = {
                "narrative": (
                    f"[mock] Skenario berlanjut. Pengguna memilih: "
                    f"{seed_src[-120:]}. Konsekuensi terukur dan konsisten."
                ),
                "actor_deltas": [
                    {"actor_id": actor_ids[0], "mood": mood}
                ] if actor_ids else [],
                "relation_deltas": [],
                "new_anchor": None,
                "updated_arc_summary": "Skenario berjalan (mock).",
                "suggested_choices": [
                    "Lanjutkan dialog", "Ubah pendekatan",
                    "Minta pendapat aktor lain",
                ],
            }
            # Bungkus dengan tag thinking (dibuka DAN ditutup) agar
            # pipa pembersih benar-benar diuji
            think_open = chr(10) + chr(60) + "think" + chr(62) + chr(10)
            think_close = chr(10) + chr(60) + "/think" + chr(62)
            raw = (
                think_open
                + "merenung sejenak"
                + think_close
                + json.dumps(delta_obj, ensure_ascii=False)
                + think_close
            )
        return LLMResult(
            ok=True,
            raw_text=raw,
            prompt_tokens=0,
            completion_tokens=0,
            latency_ms=self.fixed_latency_ms,
        )


def make_client(config: LLMConfig, api_key: str = ""):
    """Pilih klien sesuai provider. `mock` -> MockLLMAdapter."""
    if config.provider == "mock":
        return MockLLMAdapter()
    return OpenAICompatClient(config, api_key=api_key)
