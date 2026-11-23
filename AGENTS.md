# AGENTS.md — Whenyhh.ai

## Project

- **What this is:** Aplikasi web lokal visualisasi skenario bercabang, simulasi keputusan *what-if*, dan *roleplay* interaktif berbasis Externalized State Engine (SQLite + Git-DAG) berplafon input O(1) (<= 2.200 token/giliran).
- **Who it is for:** Mahasiswa dan masyarakat umum, pemangku kebijakan/peneliti (simulasi eksploratif non-preskriptif), serta novelis/kreator digital (Proyek Kelompok DDP1 Fasilkom UI, tenggat 10 Desember 2026).

## Commands

*(Seluruh perintah di bawah berstatus unverified sampai scaffold awal dibuat dan dijalankan.)*

- `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload` — wajib bind ke `127.0.0.1` (bukan `0.0.0.0`) agar server LLM lokal tidak terbuka ke jaringan kampus.
- `pytest -v` — menjalankan suite deterministik bebas GPU melalui `app.dependency_overrides` dan `MockLLMAdapter`.
- `./tailwindcss -i ./static/css/input.css -o ./static/css/app.css --minify` — kompilasi CSS offline menggunakan Tailwind v4 Standalone CLI (tanpa Node.js/npm).
- Variabel Ollama wajib sebelum demo GPU 8GB + OBS: `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`, `OLLAMA_CONTEXT_LENGTH=4096`.

## Read first — when relevant

- Scope produk dan acceptance criteria: `docs/PRD-Whenyhh-ai-MVP.md`
- Arsitektur, skema SQLite, dan rencana fitur: `docs/TechDesign-Whenyhh-ai-MVP.md`
- Ringkasan produk dan batasan v1: `agent_docs/project_brief.md`
- Stack, runtime Ollama/LM Studio/BYOM, dan perintah: `agent_docs/tech_stack.md`
- Konvensi kode, anti-slop UI, dan alur Git aman tim: `agent_docs/code_patterns.md`
- Matriks pengujian dan alur pengguna wajib: `agent_docs/testing.md`
- Disiplin anggaran Claude API $100 USD (model/effort): `agent_docs/claude_api_budget.md`

Baca hanya dokumen yang relevan dengan tugas saat ini agar hemat token API. Progres kerja, keputusan aktif, dan blocker dicatat di `MEMORY.md`.

## Gotchas

- **Tanpa Node.js dan tanpa ORM:** Frontend murni HTML/JS polos + aset lokal `static/vendor/`; database murni `sqlite3` standar Python (jangan tambah React, Vite, SQLAlchemy, atau SQLModel).
- **SQLite WAL & Kunci Tulis:** Setel `PRAGMA journal_mode=WAL` saat init; setel `synchronous=NORMAL`, `busy_timeout=5000`, `foreign_keys=ON`, `cache_size=-16000` di setiap koneksi; bungkus semua transaksi tulis dengan `BEGIN IMMEDIATE`.
- **Plafon O(1) & KV Prefix Cache:** Blok prefiks statis (`messages[0]`) harus identik *byte-for-byte* antar-giliran pada skenario yang sama; total input wajib <= 2.200 token; jangan masukkan JSON delta atau *Heartbeat* ke *sliding window* 2 giliran terakhir.
- **Pydantic Strict Schema Lintas Provider:** Gunakan `ConfigDict(extra="forbid")` tanpa `minimum`/`maximum`/`maxLength` di JSON Schema; lakukan seluruh *clamping* angka (`mood` 1..3, `trust`/`affinity` -5..+5, `tension` 0..5) di `@field_validator` Python.
- **Thinking Mode Model Lokal:** Untuk Qwen3/Qwen3.5 pada Ollama kirim `think: false` (bukan `/no_think` dan bukan `model_kwargs`); selalu bersihkan tag `<think>...</think>` dan `<|channel>thought` sebelum `json-repair`.
- **Anti-HTTP 500 saat LLM Gagal:** Maksimal 1x *self-healing retry* lalu jatuh ke *Deterministic Safe Fallback* (state lama dipertahankan + lencana kuning di UI).
- **Cytoscape Relasi Asimetris:** Gunakan `'curve-style': 'bezier'` dan `'target-arrow-shape': 'triangle'` agar panah `A -> B` dan `B -> A` terpisah.
- **UI Anti-AI-Slop:** Dilarang keras aksen ungu/indigo, font Inter/Geist, ikon emoji fungsional (hanya Lucide outline), gradien neon, kartu 3-kolom identik, em-dash/middle-dot pada teks UI, atau absennya `prefers-reduced-motion: reduce`.
- **Disiplin Biaya Claude API $100 USD & Mode Belajar DDP1:** Jangan baca seluruh repo jika tidak perlu; batasi suntingan ke 1-3 berkas per sesi; jalankan uji terfokus (`pytest tests/test_<target>.py -v`) sebelum full suite; setelah selesai menulis kode, wajib sertakan ringkasan 3-5 baris dalam Bahasa Indonesia sederhana agar seluruh anggota tim paham sebelum commit/PR.

## Protected areas

- Jaga kunci API BYOM, kunci Anthropic API, `.env`, dan berkas `*.db` tetap di luar commit Git dan log server (`X-LLM-API-Key` hanya hidup di memori/`sessionStorage` peramban, 0 baris di SQLite).
- Pertahankan perubahan *working tree* rekan tim yang tidak terkait; jangan mengubah `app/schemas.py` setelah Schema Freeze (Hari 2) tanpa persetujuan eksplisit pengguna dan pembaruan `tests/`.
- Dalam ruang lingkup yang sudah disetujui, lanjutkan implementasi lokal, pengujian `pytest`, dan perbaikan bug tanpa meminta izin di setiap suntingan berkas.
- Minta konfirmasi pengguna sebelum melakukan `git push --force`, reset riwayat Git, penghapusan data persisten, pengiriman request ke API eksternal berbayar, atau perubahan struktur kontrak bersama.

## AI features

- **Model can see:** Paket hasil *Dynamic Context Compiler* <= 2.200 token (`world_rules`, `actor_cores`, `actor_states`, `relation_edges`, *Sim Pulse*, maks 10 *Jangkar Kausal* garis keturunan aktif, `arc_summary`, 2 giliran narasi bersih terakhir, dan aksi pengguna saat ini).
- **Never send:** Kunci API (`X-LLM-API-Key`), data pribadi warga/PII nyata (pada mode BYOM cloud), berkas sistem, atau seluruh isi tabel SQLite mentah.
- **AI can do:** Read-only context input -> mengembalikan JSON terstruktur `TurnResponse` (prosa + delta kecil). AI tidak memiliki akses tulis langsung ke SQLite atau eksekusi alat otonom.
- **Needs approval:** Persetujuan aktif modal T&C (UU PDP & SE Menkominfo 9/2023) sebelum sesi pertama; pemilihan penyedia BYOM cloud pihak ketiga oleh pengguna.
- **How to verify behavior:** `pytest tests/test_context_compiler_o1.py tests/test_llm_resilience.py -v` (unverified sampai suite dibuat).
- **Fallback:** *Deterministic Safe Fallback* — tampilkan narasi terselamatkan (atau pesan ramah jika *timeout*), pertahankan status lama tanpa mutasi, dan tampilkan lencana peringatan kuning di UI (HTTP 200).

## Done means

Selesaikan fitur sesuai ruang lingkup yang disetujui, jalankan `pytest -v` (dan cek peramban/console untuk perubahan `static/`), perbaiki kegagalan yang timbul, tulis ringkasan alur kode 3-5 baris dalam Bahasa Indonesia sederhana, lalu perbarui `MEMORY.md` setelah progres atau keputusan penting. Laporkan berkas berubah, perintah yang benar-benar dijalankan, hasil uji, dan blocker konkret bila ada.
