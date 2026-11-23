# Tech Stack — Whenyhh.ai

Last verified: 2026-11 (berdasarkan Tech Design; perintah lokal masih unverified sampai scaffold dijalankan)

## Stack

| Area | Choice | Notes |
|------|--------|-------|
| Frontend | Zero-Build HTML/JS + Cytoscape.js ^3.2 (`cytoscape-dagre` v4.1.0) + Plotly-basic + `marked` + `DOMPurify` + Lucide Icons | Tanpa Node.js/npm/Vite; seluruh `.min.js` disalin ke `static/vendor/` untuk mode offline penuh. |
| Backend | Python 3.11+ (FastAPI + Uvicorn + Pydantic v2 + `httpx` + `json-repair`) | Memenuhi aturan komponen utama Python DDP1; server *Single-Origin* di `127.0.0.1:8000`. |
| Database | SQLite standar (`sqlite3`, WAL mode, tabel `STRICT`, `BEGIN IMMEDIATE`, Recursive CTE) | Nol instalasi eksternal, nol ORM berat, portabel satu berkas `whenyhh.db` (masuk `.gitignore`). |
| Auth | Not applicable | Aplikasi lokal pengguna tunggal; tidak ada login/akun di MVP. |
| Styling | Tailwind CSS v4 (Play CDN saat dev Hari 1-12 -> Standalone CLI `static/css/app.css` Hari 13) | Gaya *developer cockpit* 3-pane (charcoal `#14161A`/`#1B1E24`, 1 aksen teal `#1F9D8B`, IBM Plex Sans + JetBrains Mono). |
| Deployment | Local-First Single-Origin + Public GitHub Repository + GitHub Actions CI (`pytest`) | Biaya Rp0; deliverable DDP1 berupa tautan repo GitHub publik dan video demo YouTube <= 15 menit. |

## Commands

*(Seluruh perintah direncanakan dari Tech Design — status: unverified sampai scaffold awal dibuat.)*

- Setup: `python -m venv .venv && pip install -r requirements.txt`
- Dev: `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
- Test: `pytest -v`
- Typecheck: Not configured (open decision)
- Lint/format: Not configured (open decision: `ruff` TBD)
- Build: `./tailwindcss -i ./static/css/input.css -o ./static/css/app.css --minify` *(Tailwind v4 Standalone CLI, Hari 13)*
- Browser/device check: Buka `http://127.0.0.1:8000` di Chrome/Edge (1080p dan lebar 768px), cek Console = 0 error, uji *click-to-fork* Cytoscape, dan uji mode offline (Wi-Fi mati).

## AI Runtime

- **Provider/runtime (Product AI):**
  - Default lokal: **Ollama** (`http://127.0.0.1:11434/v1`), model `qwen2.5:7b` atau `qwen3:8b` (`OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`, `OLLAMA_CONTEXT_LENGTH=4096`, plafon aman ~6,0-6,2 GB VRAM untuk ruang napas OBS 1080p).
  - Opsional lokal: **LM Studio** (`http://127.0.0.1:1234/v1`; saat rekaman OBS jalankan mode *headless* `lms server start` dan tutup GUI desktop).
  - Opsional BYOM gratis (untuk tim/penguji tanpa GPU 8GB): **Groq** (`https://api.groq.com/openai/v1`), **Gemini AI Studio** (`https://generativelanguage.googleapis.com/v1beta/openai/`), **OpenRouter `:free`**.
  - Pengujian/offline tanpa GPU: **`MockLLMAdapter`**.
- **Coding Agent Tooling ($100 USD Claude API + Pendamping Gratis):**
  - Utama: **Claude Code** via Claude API ($100 USD pay-as-you-go, hard cap $95 USD; lihat `agent_docs/claude_api_budget.md`). Default **Sonnet `medium`**, wajib `/clear` tiap fitur.
  - Pendamping hemat biaya: **Gemini** untuk naskah `app/seeds/*.json`, FAQ, `TERMS.md`, dan *second opinion*; **LM Studio** lokal (`http://localhost:1234/v1`) untuk eksperimen offline dan *unit test* sederhana.
- **Model can see (Product AI):**
  - Public: Aturan inti skenario (`world_rules`), 3 skenario *seed* bawaan.
  - User-owned: `actor_cores`, `actor_states`, `relation_edges`, *Sim Pulse*, maks 10 *Jangkar Kausal* garis keturunan aktif, `arc_summary`, 2 giliran narasi bersih terakhir, dan aksi pengguna saat ini (total <= 2.200 token).
  - Never send: Header `X-LLM-API-Key`, data pribadi warga/PII nyata (pada BYOM cloud), berkas lokal sistem, atau isi SQLite mentah.
- **Tools/actions:** Read-only context input -> structured JSON output (`TurnResponse`). Tidak ada tool execution otonom atau akses tulis langsung ke database.
- **Approval gates:** Persetujuan aktif modal T&C pada kunjungan pertama; pemilihan eksplisit penyedia BYOM cloud di modal Pengaturan Model.
- **Retention/training setting to verify:** Mode lokal Ollama/LM Studio = 0% retensi pihak ketiga. Mode BYOM cloud wajib menampilkan lencana privasi (tier gratis Gemini dan Mistral menyatakan konten dapat dipakai melatih model — verifikasi kebijakan terbaru penyedia sebelum rilis).
- **Fallback:** Pipa ketahanan 4 lapis (`response_format` -> pembersih `<think>` + `json-repair` -> Pydantic v2 -> maks 1x *retry*) berakhir pada *Deterministic Safe Fallback* (narasi terselamatkan + delta nol + lencana kuning di UI, HTTP 200).

## Important Patterns

- **Data fetching:** Frontend memakai wrapper tipis `static/js/api.js` (`fetch` ke origin sama `/api/*`), melampirkan `X-LLM-API-Key` hanya dari `sessionStorage`/memori saat mode BYOM aktif.
- **State management:** Sumber kebenaran tunggal (*Single Source of Truth*) berada di SQLite (`nodes`, `actor_states`, `relation_edges`, `causal_anchors`); UI hanya merender DTO hasil respons API.
- **Forms/validation:** Validasi payload API menggunakan Pydantic v2 (`extra="forbid"`) dengan *clamping* deterministik di `@field_validator`; form UI menampilkan error *inline* di bawah input.
- **Error handling:** Endpoint `/api/turns` menangani kegagalan LLM secara anggun menuju *Deterministic Safe Fallback* (HTTP 200 + `is_fallback: true`); ID tak ditemukan mengembalikan HTTP 404; payload tak valid HTTP 422.
- **Logging/monitoring:** Catat `prompt_tokens`, `completion_tokens`, dan latensi di tabel `nodes` untuk grafik Plotly; saring total header `X-LLM-API-Key` agar tidak pernah tercatat di log atau database.
