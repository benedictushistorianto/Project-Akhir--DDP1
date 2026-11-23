# Memory

Perbarui berkas ini setelah keputusan besar, penyelesaian fase, atau penemuan bug penting. Jaga tetap ringkas. Ini adalah riwayat proyek bersama tim, terpisah dari memori otomatis pribadi alat coding.

## Current State

- Current task: Phase 1 selesai secara fungsional; selanjutnya Phase 2 (Context Compiler O(1) + LLM Gateway + Resilience Pipeline)
- Current phase: Phase 1 DONE -> mulai Phase 2 (Hari 5-9: 27 Nov - 1 Des 2026)
- Next step: Implementasi `app/engine/context_compiler.py` (Dynamic Context Compiler O(1) <= 2.200 token), `app/engine/sim_pulse.py`, `app/llm/client.py` (OpenAI-compatible), `app/llm/resilience.py` (4-layer pipeline), dan suite `test_context_compiler_o1.py` + `test_llm_resilience.py`
- Blocked by: none

## Decisions

- [2026-11-23] Memilih arsitektur Single-Origin lokal (`127.0.0.1:8000`) berbasis Python FastAPI + Uvicorn + `sqlite3` standar (WAL + `STRICT` + Recursive CTE) + Zero-Build HTML/JS agar komponen utama 100% Python, biaya operasional Rp0, dan tanpa beban Node.js/ORM.
- [2026-11-23] Memisahkan seluruh memori skenario (`Core` vs `State`, relasi asimetris, *Jangkar Kausal*, pohon Git-DAG imutabel) keluar dari konteks LLM menuju *Dynamic Context Compiler* O(1) <= 2.200 token input.
- [2026-11-23] Menggunakan gaya desain *developer cockpit* 3-pane terinspirasi GitKraken dengan pagar Anti-AI-Slop (charcoal `#14161A`/`#1B1E24`, 1 aksen teal `#1F9D8B`, IBM Plex Sans + JetBrains Mono, Lucide outline icons, wajib `prefers-reduced-motion`).
- [2026-11-23] Menunda login/auth, *cloud hosting*, *three-way merge* kompleks, audio/TTS, generator gambar, dan perintah Git lanjutan (`rebase`/`bisect`) ke v2 agar MVP tuntas sebelum tenggat 10 Desember 2026 pukul 23:59 WIB.
- [2026-11-23] Menetapkan kepemilikan folder eksklusif, alur Git aman 5 langkah (mendukung GitHub Desktop), dan ringkasan penjelasan kode manual di tiap PR untuk memitigasi kesulitan Git dan menjaga pemahaman kode seluruh anggota DDP1.

## AI / Tooling Decisions

- [2026-11-23] Product LLM default: **Ollama lokal** (`http://127.0.0.1:11434/v1`) dengan `qwen2.5:7b` / `qwen3:8b` (`OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`, `OLLAMA_CONTEXT_LENGTH=4096`) untuk ruang napas OBS 1080p di GPU 8GB VRAM.
- [2026-11-23] Product LLM sekunder: **LM Studio** (`http://127.0.0.1:1234/v1`), preset **BYOM Cloud Gratis** (Groq, Gemini AI Studio, OpenRouter `:free`; kunci *ephemeral* di `sessionStorage` + header `X-LLM-API-Key`), dan **`MockLLMAdapter`** untuk `pytest`.
- [2026-11-23] Vibe-Coding Budget: **$100 USD Claude API (pay-as-you-go)** untuk 17 hari — hard cap Console $95 USD, alokasi per fase ($15 / $35 / $30 / $15-$20 cadangan), default **Sonnet `medium`**, **Sonnet `high`** untuk modul inti/UI awal, **Opus** hanya untuk Plan Mode skema & bug buntu, serta wajib `/clear` setelah tiap fitur (`agent_docs/claude_api_budget.md`).
- [2026-11-23] Offloading Hemat API: Tugas penulisan konten panjang (`app/seeds/*.json`, FAQ, `TERMS.md`, `README.md`) dan *second opinion* dialihkan ke **Gemini** atau **LM Studio** lokal.
- [2026-11-23] Pipa ketahanan JSON 4 lapis: *constrained decoding* + pembersih `<think>` + `json-repair` + Pydantic v2 (`extra="forbid"`) + maks 1x *retry* menuju *Deterministic Safe Fallback*.

## Known Issues / Open Decisions

- Open decision (TBD 1): Konfirmasi jumlah final anggota kelompok (3 orang atau 4 orang) untuk penyesuaian pembagian Jalur 3 dan Jalur 4.
- Open decision (TBD 2): Putuskan apakah tim ingin menambahkan `ruff` sebagai linter Python di CI atau cukup `pytest -v`.
- Catatan lingkungan: `python -m venv .venv`, `pip install -r requirements.txt`, dan `pytest -v` sudah terverifikasi jalan (Python 3.14.10, **49 passed**, 0 failed, 0.71s).

## Completed

- [x] Phase 1 (Hari 1a): Initial scaffold — `.gitignore`, `requirements.txt`, `pyproject.toml`, `.github/workflows/ci.yml`, `app/schemas.py` (kontrak Pydantic v2 lengkap dengan clamping), `app/db/schema.sql` (7 tabel STRICT + 3 indeks), `app/db/connection.py` (WAL + PRAGMA wajib + write_transaction), `app/main.py` (FastAPI lifespan + StaticFiles), `app/routers/system.py` (/healthz, /readyz), `static/index.html` + `static/css/input.css`, `tests/conftest.py` + 3 suite awal (18 passed).
- [x] Phase 1 (Hari 1b): Core engine + routers + seeds — `app/engine/dag_repo.py` (get_lineage Recursive CTE, commit_turn, fork_branch, checkout_branch, get_graph, load_seed_scenario), `app/engine/state_mutator.py` (apply_turn_deltas + clamping ganda + anti-halusinasi actor_id), `app/routers/scenarios.py` (GET list/detail/graph/export JSON+MD), `app/routers/turns.py` (POST /api/turns mock, POST fork, POST checkout), 3 seed JSON Bahasa Indonesia (`kampus_anti_scam`, `kebijakan_parkir`, `misteri_pelabuhan_1928`), seed auto-loading di lifespan, `tests/test_engine_integration.py` + `tests/test_seed_scenarios.py` + extended `tests/test_api_contracts.py`. Total: **49 passed, 0 failed** (0.71s).
- [ ] Phase 2: Externalized State Engine (`dag_repo.py`, `state_mutator.py`, `context_compiler.py` O(1), `sim_pulse.py`)
- [ ] Phase 2: LLM Gateway & 4-Layer JSON Resilience (`client.py`, `resilience.py`) + Integrasi End-to-End (Hari 9)
- [ ] Phase 3: Antarmuka Cockpit 3-Pane (Cytoscape Git-DAG, Relasi Bezier, Plotly Telemetri, 3 Seed Scenarios, FAQ, T&C, Ekspor JSON/MD)
- [ ] Phase 3: Suite uji `pytest` (>= 34 uji termasuk stres 100 giliran O(1)) dan kompilasi offline `app.css` + `static/vendor/`
- [ ] Phase 4: Feature Freeze, uji demo offline (Wi-Fi mati), video YouTube <= 15 menit, dan submisi GitHub publik
