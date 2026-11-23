# Memory

Perbarui berkas ini setelah keputusan besar, penyelesaian fase, atau penemuan bug penting. Jaga tetap ringkas. Ini adalah riwayat proyek bersama tim, terpisah dari memori otomatis pribadi alat coding.

## Current State

- Current task: Initial project scaffold, repo setup, dan verifikasi environment lokal (Phase 1 - Hari 1)
- Current phase: Phase 1 - Foundation & Contract (Hari 1-4: 23 Nov - 26 Nov 2026)
- Next step: Pasang spend cap $95 di Anthropic Console, buat struktur folder, `.gitignore`, `requirements.txt`, `app/schemas.py` (target Schema Freeze Hari 2), serta verifikasi `pytest` dan Ollama lokal 8GB
- Blocked by: none (keputusan terbuka non-blocking: kepastian jumlah anggota 3 vs 4 orang dan penggunaan linter `ruff`)

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
- Catatan lingkungan: Seluruh perintah CLI (`setup`, `dev`, `test`, `build`) belum dijalankan di repo aktual (status: unverified).

## Completed

- [ ] Phase 1: Spend cap $95 di Anthropic Console, initial scaffold, `.gitignore`, CI GitHub Actions, dan Schema Freeze `app/schemas.py`
- [ ] Phase 1: Core SQLite WAL + `STRICT` data model (`schema.sql`, `connection.py`) dan verifikasi Ollama lokal
- [ ] Phase 2: Externalized State Engine (`dag_repo.py`, `state_mutator.py`, `context_compiler.py` O(1), `sim_pulse.py`)
- [ ] Phase 2: LLM Gateway & 4-Layer JSON Resilience (`client.py`, `resilience.py`) + Integrasi End-to-End (Hari 9)
- [ ] Phase 3: Antarmuka Cockpit 3-Pane (Cytoscape Git-DAG, Relasi Bezier, Plotly Telemetri, 3 Seed Scenarios, FAQ, T&C, Ekspor JSON/MD)
- [ ] Phase 3: Suite uji `pytest` (>= 34 uji termasuk stres 100 giliran O(1)) dan kompilasi offline `app.css` + `static/vendor/`
- [ ] Phase 4: Feature Freeze, uji demo offline (Wi-Fi mati), video YouTube <= 15 menit, dan submisi GitHub publik
