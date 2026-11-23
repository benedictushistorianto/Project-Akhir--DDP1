# Memory

Perbarui berkas ini setelah keputusan besar, penyelesaian fase, atau penemuan bug penting. Jaga tetap ringkas. Ini adalah riwayat proyek bersama tim, terpisah dari memori otomatis pribadi alat coding.

## Current State

- **Current task:** Phase 1-3 selesai 100%. Backend, engine, LLM pipeline, dan UI cockpit berfungsi penuh. Siap Phase 4.
- **Current phase:** Phase 4 (Feature Freeze + Demo + Submisi)
- **Next step:** (1) Jalankan `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload` dan coba UI di browser. (2) Uji demo offline (Wi-Fi mati). (3) Rekam video YouTube ≤15 menit. (4) `git push` ke GitHub publik.
- **Blocked by:** none

## Decisions

- [2026-11-23] Memilih arsitektur Single-Origin lokal (`127.0.0.1:8000`) berbasis Python FastAPI + Uvicorn + `sqlite3` standar (WAL + `STRICT` + Recursive CTE) + Zero-Build HTML/JS agar komponen utama 100% Python, biaya operasional Rp0, dan tanpa beban Node.js/ORM.
- [2026-11-23] Memisahkan seluruh memori skenario (`Core` vs `State`, relasi asimetris, *Jangkar Kausal*, pohon Git-DAG imutabel) keluar dari konteks LLM menuju *Dynamic Context Compiler* O(1) <= 2.200 token input.
- [2026-11-23] Menggunakan gaya desain *developer cockpit* 3-pane terinspirasi GitKraken dengan pagar Anti-AI-Slop (charcoal `#14161A`/`#1B1E24`, 1 aksen teal `#1F9D8B`, IBM Plex Sans + JetBrains Mono, Lucide outline icons, wajib `prefers-reduced-motion`).
- [2026-11-23] Menunda login/auth, *cloud hosting*, *three-way merge* kompleks, audio/TTS, generator gambar, dan perintah Git lanjutan (`rebase`/`bisect`) ke v2 agar MVP tuntas sebelum tenggat 10 Desember 2026 pukul 23:59 WIB.
- [2026-11-23] Export endpoint menerima `format=json|md|markdown` (tambah `markdown` alias untuk kompatibilitas `api.js`).
- [2026-11-23] `app.css` dibangun mandiri tanpa Tailwind CLI: `@import "tailwindcss"` diganti reset CSS inline (modern-normalize + Preflight ekuivalen). Script `scripts/build_css.py` tersedia. File committed siap pakai.

## AI / Tooling Decisions

- [2026-11-23] Product LLM default: **Ollama lokal** (`http://127.0.0.1:11434/v1`) dengan `qwen2.5:7b` / `qwen3:8b` (`OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`, `OLLAMA_CONTEXT_LENGTH=4096`) untuk ruang napas OBS 1080p di GPU 8GB VRAM.
- [2026-11-23] Product LLM sekunder: **LM Studio** (`http://127.0.0.1:1234/v1`), preset **BYOM Cloud Gratis** (Groq, Gemini AI Studio, OpenRouter `:free`; kunci *ephemeral* di `sessionStorage` + header `X-LLM-API-Key`), dan **`MockLLMAdapter`** untuk `pytest`.
- [2026-11-23] Pipa ketahanan JSON 4 lapis: *constrained decoding* + pembersih `<think>` + `json-repair` + Pydantic v2 (`extra="forbid"`) + maks 1x *retry* menuju *Deterministic Safe Fallback*.
- [2026-11-23] `clean_llm_text()` fix: `<|channel>thought` Qwen — split dari sisi kanan (ambil konten setelah tag), cari `{` pertama sebagai awal JSON.

## Known Issues / Open Decisions

- Open decision (TBD 1): Konfirmasi jumlah final anggota kelompok (3 orang atau 4 orang) untuk penyesuaian pembagian Jalur 3 dan Jalur 4.
- Open decision (TBD 2): Putuskan apakah tim ingin menambahkan `ruff` sebagai linter Python di CI atau cukup `pytest -v`.
- `/api/llm/models` mengembalikan `{"models":[], "error":"..."}` saat Ollama offline — perilaku benar (error ditangani gracefully, bukan 500).

## Environment

- Python 3.14.10, `pytest -v`: **73 passed, 0 failed** (2.26s)
- Smoke test in-process: **12/12 endpoint OK** (healthz, readyz, scenarios, graph, turns, fork, checkout, llm/test, llm/models, export json, export md, root /)
- `app.css`: 14.5 KB mandiri (reset + custom CSS, tanpa Tailwind CLI)
- `static/vendor/`: 7 lib offline (cytoscape, dagre, plotly, marked, dompurify, lucide)
- File proyek: 68 file, ~5.5 MB (termasuk vendor JS)

## Completed

- [x] Phase 1 (Hari 1-4): Initial scaffold + Core engine + routers + seeds — `app/db/`, `app/engine/dag_repo.py`, `app/engine/state_mutator.py`, `app/routers/`, `app/schemas.py` (FROZEN), `app/main.py`, 3 seed JSON Bahasa Indonesia, 7 test suites. Total: **49 passed**.
- [x] Phase 2 (Hari 5-9): Context Compiler O(1) + SimPulse + LLM Gateway + 4-Layer Resilience — `app/engine/context_compiler.py`, `app/engine/sim_pulse.py`, `app/llm/client.py`, `app/llm/resilience.py`, bug fix `<|channel>thought`, integrasi end-to-end ke `/api/turns`, endpoint `/api/llm/models` + `/api/llm/test`. Total: **73 passed**.
- [x] Phase 3 (Hari 10): UI Cockpit 3-pane — `static/index.html` (T&C modal, fork modal, LLM config modal), `static/css/app.css` (mandiri), `static/js/` (5 file: api, app, dag_view, relation_view, telemetry), `static/vendor/` (7 lib offline), `TERMS.md`, `README.md`, root route `/`.
- [ ] Phase 4: Feature Freeze, uji demo offline (Wi-Fi mati), video YouTube <= 15 menit, dan submisi GitHub publik
