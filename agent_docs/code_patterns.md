# Code Patterns — Whenyhh.ai

Konvensi spesifik proyek ini diturunkan dari Tech Design dan dirancang agar aman bagi tim 3-4 mahasiswa DDP1 yang bekerja paralel.

## Architecture & Folder Ownership (Anti-Konflik Git)

- Pola utama: **Layered Modular Monolith** (Router -> Engine/LLM -> SQLite Repository -> Zero-Build Static UI).
- Jaga logika domain (`app/engine/`) 100% terpisah dari lapisan HTTP (`app/routers/`) dan UI (`static/`).
- Kepemilikan berkas eksklusif untuk mencegah konflik Git:
  - Bersama (beku Hari 2): `app/schemas.py`, `requirements.txt`
  - Jalur 1 (DB & DAG): `app/db/`, `app/engine/dag_repo.py`, `app/engine/state_mutator.py`
  - Jalur 2 (Compiler & LLM): `app/engine/context_compiler.py`, `app/engine/sim_pulse.py`, `app/llm/`
  - Jalur 3 (API, Seeds, Tests): `app/main.py`, `app/routers/`, `app/seeds/`, `tests/`
  - Jalur 4 (UI & Legal): `static/`, `TERMS.md`

## Data And State

- **SQLite Connections:** Gunakan *connection factory* di `app/db/connection.py` dengan `check_same_thread=False`, PRAGMA per-koneksi wajib (`synchronous=NORMAL`, `busy_timeout=5000`, `foreign_keys=ON`, `cache_size=-16000`), dan bungkus transaksi tulis dengan `BEGIN IMMEDIATE`.
- **Immutability:** Jangan pernah `UPDATE` narasi, `actor_states`, atau `relation_edges` pada simpul `node_id` yang sudah dikomit; setiap giliran menciptakan baris `node_id` baru.
- **Lineage Isolation:** Penelusuran riwayat dan *Jangkar Kausal* wajib memakai kueri `WITH RECURSIVE` dari `head_node_id` ke akar agar cabang A dan cabang B tidak pernah saling mencemari.
- **Determinism:** *Sim Pulse* dan *Ticking Clock* wajib memakai instance lokal `random.Random(f"{rng_seed}:{parent_node_id}:{turn_index}")`, bukan global `random`.

## Errors And Validation

- Validasi seluruh input API dan output LLM dengan Pydantic v2 (`ConfigDict(extra="forbid")`).
- Jangan menaruh `ge`/`le`/`max_length` di definisi Field `TurnResponse` yang dikirim ke JSON Schema LLM; lakukan *clamping* secara eksplisit di `@field_validator` Python.
- Di `state_mutator.py`, abaikan `actor_id` yang tidak terdaftar di `actor_cores` (anti-halusinasi ID) tanpa melempar error.
- Gunakan `httpx.AsyncClient` di dalam fungsi `async def` (jangan pernah memakai `requests` sinkron yang memblokir *event loop* Uvicorn).
- Di frontend, selalu render teks Markdown dari LLM via `DOMPurify.sanitize(marked.parse(text))`; dilarang memasukkan HTML mentah dengan `innerHTML`.

## Naming & Style

- File Python & modul: `snake_case.py`; kelas & model Pydantic: `PascalCase`; fungsi & variabel Python: `snake_case`; konstanta & env var: `UPPER_SNAKE_CASE`.
- File JS: `snake_case.js` (`dag_view.js`, `relation_view.js`, `telemetry.js`); fungsi/variabel JS: `camelCase`; token CSS: `--kebab-case` di `static/css/input.css`.
- Pesan commit: *Conventional Commits* ringkas (`feat(dag): ...`, `fix(llm): ...`, `test(compiler): ...`).

## UI Cockpit & Anti-AI-Slop Rules

- Ikuti 3 dial desain: Variance 3, Motion 2 (`<= 150ms`, `transform`/`opacity` saja, wajib `@media (prefers-reduced-motion: reduce)`), Density 8 (garis tipis `1px` hairline, angka tabular `JetBrains Mono`).
- Palet tunggal non-ungu: permukaan `#14161A` / `#1B1E24` / `#232730`, border `#2E333E`, teks `#E6E8EC` / `#9AA3B2`, aksen primer `#1F9D8B` (Teal), warna jalur *swimlane* fungsional (`#2DD4BF`, `#38BDF8`, `#F59E0B`, `#FB7185`).
- Satu paket ikon saja: Lucide Icons *outline* `16-20px` dengan `currentColor`; 0 emoji fungsional pada tombol/label; tanpa em-dash, en-dash, atau middle-dot pada teks UI.

## Safe Git & DDP1 Learning Convention

- Alur 5 langkah (bisa 100% lewat GitHub Desktop): (1) Pull `main`, (2) buat *feature branch*, (3) edit folder sendiri + jalankan `pytest -v`, (4) commit & push, (5) buka PR dengan 3 baris penjelasan manual cara kerja kode.
- Setelah menulis atau mengubah fungsi, agen wajib menampilkan ringkasan 3-5 baris dalam Bahasa Indonesia sederhana agar mahasiswa paham sebelum melakukan commit.
