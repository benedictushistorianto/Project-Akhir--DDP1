# Memory

Perbarui berkas ini setelah keputusan besar, penyelesaian fase, atau penemuan bug penting. Jaga tetap ringkas. Ini adalah riwayat proyek bersama tim, terpisah dari memori otomatis pribadi alat coding.

## Current State

- Current task: Lanjutkan Phase 1 — bangun `dag_repo.py`, `state_mutator.py`, dan router skenario/turn
- Current phase: Phase 1 - Foundation & Contract (Hari 1-4: 23 Nov - 26 Nov 2026)
- Next step: Implementasi `app/engine/dag_repo.py` (Recursive CTE lineage, commit_turn, fork_branch), `app/engine/state_mutator.py`, dan router `app/routers/scenarios.py` + `app/routers/turns.py`
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
- Catatan lingkungan: `python -m venv .venv`, `pip install -r requirements.txt`, dan `pytest -v` sudah terverifikasi jalan (Python 3.14.10, 18 passed, 0 failed).

## Completed

- [x] Phase 1 (Hari 1): Initial scaffold — `.gitignore`, `requirements.txt`, `pyproject.toml`, `.github/workflows/ci.yml`, `app/schemas.py` (kontrak Pydantic v2 lengkap dengan clamping), `app/db/schema.sql` (7 tabel STRICT + 3 indeks), `app/db/connection.py` (WAL + PRAGMA wajib + write_transaction), `app/main.py` (FastAPI lifespan + StaticFiles), `app/routers/system.py` (/healthz, /readyz), `static/index.html` + `static/css/input.css`, `tests/conftest.py` + 3 suite awal (18 passed). Semua `__init__.py` untuk package `app`, `app/db`, `app/engine`, `app/llm`, `app/routers`, `tests`.
- [ ] Phase 1: Core engine (`dag_repo.py`, `state_mutator.py`) dan router skenario/giliran
- [ ] Phase 2: Externalized State Engine (`dag_repo.py`, `state_mutator.py`, `context_compiler.py` O(1), `sim_pulse.py`)
- [ ] Phase 2: LLM Gateway & 4-Layer JSON Resilience (`client.py`, `resilience.py`) + Integrasi End-to-End (Hari 9)
- [ ] Phase 3: Antarmuka Cockpit 3-Pane (Cytoscape Git-DAG, Relasi Bezier, Plotly Telemetri, 3 Seed Scenarios, FAQ, T&C, Ekspor JSON/MD)
- [ ] Phase 3: Suite uji `pytest` (>= 34 uji termasuk stres 100 giliran O(1)) dan kompilasi offline `app.css` + `static/vendor/`
- [ ] Phase 4: Feature Freeze, uji demo offline (Wi-Fi mati), video YouTube <= 15 menit, dan submisi GitHub publik
