# Technical Design Document: Whenyhh.ai MVP

## How We'll Build It

### Recommended Approach: Single-Origin Python Web App (FastAPI + SQLite + Zero-Build HTML/JS)

Berdasarkan PRD **Whenyhh.ai**, kewajiban komponen utama Python (DDP1 Fasilkom UI), anggaran operasional aplikasi Rp0, anggaran pengembangan **Claude API $100 USD (pay-as-you-go)**, tenggat 17 hari aktif, serta kekhawatiran utama tim terkait **kesulitan penggunaan Git dan pemahaman kode**, jalur paling optimal adalah arsitektur **monolit modular lokal tanpa build tool frontend**.

**Primary Recommendation: FastAPI + Uvicorn + `sqlite3` (WAL/STRICT) + HTML/JS Polos + Cytoscape.js + Ollama/BYOM**
- **Why it's perfect for you:**
  1. **100% logika inti ada di Python polos yang terbaca** (`sqlite3` standar tanpa ORM rumit, Pydantic v2 yang jelas kontraknya) sehingga seluruh anggota tim mudah memahami dan menjelaskan isi kode di video presentasi.
  2. **Zero-Build Frontend:** Tidak butuh Node.js, npm, Vite, atau Webpack. Menjalankan seluruh aplikasi (backend + UI) cukup dengan satu perintah `uvicorn app.main:app --host 127.0.0.1 --port 8000`.
  3. **Kepemilikan berkas terpisah untuk mencegah konflik Git:** 4 direktori kerja eksklusif (`app/db` & `dag_repo`, `app/llm` & `context_compiler`, `app/routers` & `tests`, `static/`) membuat anggota tim jarang menyentuh berkas yang sama sekaligus menghemat biaya token input Claude API karena agen hanya membaca 1-3 berkas per sesi.
  4. **Ramah Claude API $100 USD + Gemini/LM Studio:** Berkas tipis dan terstruktur rapi menjaga sesi Claude Code tetap singkat (wajib `/clear` setelah tiap fitur), sehingga dana $100 USD cukup leluasa dari Hari 1 sampai Hari 17.
- **What it costs:** Rp0 untuk seluruh stack/runtime produk + plafon maksimal $100 USD untuk Claude API (hard cap $95 USD di Anthropic Console).
- **Time to learn:** 1-2 hari untuk memahami alur dasar FastAPI endpoint, kueri SQLite, dan alur Git aman via GitHub Desktop.
- **Limitations to know:** Aplikasi hanya berjalan lokal di komputer pengguna (`127.0.0.1`), tidak dirancang untuk ribuan pengguna serentak di internet, dan tampilan antarmuka bergaya GitKraken dibangun memakai HTML/JS modular + Cytoscape.js alih-alih komponen React siap pakai.

### Alternative Options Compared

#### 1. Pilihan Tumpukan UI & Backend
| Option | Pros | Cons | Cost | Time to MVP |
|--------|------|------|------|-------------|
| **FastAPI + Uvicorn + Zero-Build HTML/JS + Cytoscape.js** *(Dipilih)* | Interaksi klik simpul Git-DAG & panah bezier mulus tanpa reload halaman; zero Node.js build; arsitektur Client-Server bernilai tinggi di rubrik "hal baru di luar kelas". | Butuh 1 anggota mengurus HTML/JS dasar dan CSS Tailwind. | Rp0 | 2,5 minggu |
| **NiceGUI (100% Python di atas FastAPI)** | Seluruh kode tetap Python sehingga sangat mudah dibaca tim pemula. | Kustomisasi penuh kanvas Cytoscape swimlane & DOMPurify tetap memerlukan injeksi JS, dokumentasi lebih kecil. | Rp0 | 2 minggu |
| **Streamlit (100% Python)** | Prototipe paling cepat (1-2 hari). | Model *full-script rerun* membuat interaksi klik-node DAG terasa kaku dan tata letak 3-pane cockpit sulit presisi. | Rp0 | 1,5 minggu |
| **PyQt6 (Desktop GUI)** | Berjalan native tanpa browser. | Kode boilerplate graf interaktif sangat panjang, kurva belajar Qt curam, rawan beda tampilan Windows vs macOS antar-anggota. | Rp0 | 4+ minggu |

#### 2. Pilihan Runtime LLM Lokal (GPU 8GB VRAM)
| Option | Pros | Cons | Cost | Cocok Untuk |
|--------|------|------|------|-------------|
| **Ollama (Background Daemon)** *(Default Utama)* | Lisensi MIT; tanpa GUI Electron sehingga hemat VRAM saat merekam OBS 1080p; ganti model otomatis dari dropdown UI; dukungan `OLLAMA_KV_CACHE_TYPE=q8_0`. | Penyetelan parameter GGUF visual lebih sederhana dibanding LM Studio. | Rp0 | Demo utama & operasional harian di PC GPU 8GB. |
| **LM Studio (Opsi Sekunder / Eksperimen)** | Antarmuka visual bagus untuk mencari GGUF dan memantau VRAM; mendukung `lms server start` (headless daemon `llmster`). | Aplikasi desktop GUI-nya memakan RAM/VRAM tambahan jika tidak ditutup saat rekaman OBS. | Rp0 | Eksperimen model di PC & opsi backend bagi coding agent. |
| **BYOM Cloud Gratis (Groq / Gemini / OpenRouter)** | Berjalan di laptop tanpa GPU (0 MB VRAM); Groq sangat cepat (~320-500 t/s estimasi). | Butuh internet; ada batas kuota harian (misal Groq 200K TPD, OpenRouter 50 RPD); tier gratis Gemini/Mistral melatih dari data prompt. | Rp0 | Rekan tim/Asdos tanpa GPU & cadangan darurat saat rekaman. |

#### 3. Pilihan Persistensi Basis Data
| Option | Pros | Cons | Cost | Cocok Untuk |
|--------|------|------|------|-------------|
| **SQLite standar (`sqlite3` + WAL + `STRICT`)** *(Dipilih)* | Bawaan Python (0 instalasi server); mendukung *Recursive CTE* untuk penelusuran DAG; mudah dipahami mahasiswa semester awal; 100% lokal. | Tidak cocok untuk penulisan konkuren ratusan pengguna *cloud* (bukan kebutuhan MVP). | Rp0 | MVP lokal & proyek DDP1. |
| **SQLAlchemy / SQLModel ORM** | Abstraksi objek otomatis. | Menambah lapisan magis (*session lifecycle*, *detached instance error*) yang sering membingungkan pemula dan memicu bug `StaticPool` saat uji `pytest`. | Rp0 | Proyek berskala besar dengan migrasi kompleks. |

---

## Project Setup Checklist

### Step 1: Persiapan Akun & Perangkat Lunak Lokal (Hari 1)
Tidak diperlukan akun hosting *cloud* atau layanan basis data berbayar. Cukup siapkan:
- [ ] **GitHub** (akun gratis seluruh anggota + 1 repositori publik) — `https://github.com`
- [ ] **GitHub Desktop** (sangat disarankan bagi anggota yang baru belajar Git agar commit/branch/PR visual dan minim salah perintah) — `https://desktop.github.com`
- [ ] **Anthropic Console Spend Guardrail:** Setel *Workspace/Monthly Spend Limit* ke **$95 USD** dan peringatan email pada **$25, $50, dan $75 USD** sebelum memulai Claude Code dengan API key $100.
- [ ] **Python 3.11+** (pastikan `sqlite3.sqlite_version >= 3.37` untuk dukungan tabel `STRICT`)
- [ ] **Ollama** (di PC dengan GPU 8GB VRAM) — `https://ollama.com`
- [ ] **LM Studio** (opsional di PC untuk eksperimen GGUF atau penghubung coding agent) — `https://lmstudio.ai`
- [ ] **Akun Groq gratis** (opsional bagi rekan tim tanpa GPU sebagai preset BYOM tercepat) — `https://console.groq.com`

### Step 2: Konfigurasi Wajib Ollama untuk GPU 8GB VRAM + Ruang Napas OBS (Hari 1)
Setel tiga variabel lingkungan sistem sebelum menjalankan `ollama serve` agar konsumsi VRAM aman di bawah batas konservatif ~6,0-6,2 GB:
```bash
# Linux / macOS (atau tambahkan ke System Environment Variables di Windows)
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
export OLLAMA_CONTEXT_LENGTH=4096

# Unduh model utama yang aman saat merekam OBS 1080p
ollama pull qwen2.5:7b
# Opsional: model cerdas alternatif (wajib kirim think=False dari backend)
ollama pull qwen3:8b
# Opsional: cadangan ringan untuk laptop RAM/VRAM kecil
ollama pull qwen3.5:4b
```

### Step 3: Setup AI Coding Assistant — Strategi Claude API $100 USD (Hari 1)
- [ ] **Utama — Claude Code (API $100 Pay-As-You-Go):**
  - Default model: **Claude Sonnet (`effort=medium`)** untuk ~80% tugas (router, unit test, iterasi UI).
  - Naikkan ke **Sonnet (`effort=high`)** hanya untuk algoritma inti (`dag_repo.py`, `context_compiler.py`, `resilience.py`, dan draf pertama UI Cockpit 3-Pane).
  - Gunakan **Opus (`medium`/`high`)** ketat hanya di *Plan Mode* untuk `app/schemas.py` / `schema.sql` dan bug buntu setelah 2× gagal di Sonnet.
  - Gunakan **Haiku** (atau lempar ke **Gemini / LM Studio**) untuk konten mekanis (`app/seeds/*.json`, `TERMS.md`, `README.md`).
  - Wajib cek `/cost` setelah tiap fitur dan jalankan **`/clear`** setelah selesai 1 tugas (1-3 berkas) agar tagihan token per giliran tidak membengkak. Rincian lengkap di `agent_docs/claude_api_budget.md`.
- [ ] **Opsional — Gemini (CLI / Antigravity):** Fokus pada penulisan narasi panjang 3 skenario *seed* Bahasa Indonesia, naskah FAQ/T&C, dan *second opinion* arsitektur ($0 terhadap saldo Claude).
- [ ] **Opsional — Koneksi LM Studio Lokal:** Untuk eksperimen uji coba gratis atau pembuatan *unit test* tambahan di endpoint `http://localhost:1234/v1`.

### Step 4: Inisialisasi Proyek & Aset Offline (Hari 1-2)
```bash
git clone https://github.com/<org-atau-user>/whenyhh-ai.git
cd whenyhh-ai

python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
```

**Isi `requirements.txt` (minimalis dan stabil):**
```text
fastapi>=0.115,<1.0
uvicorn[standard]>=0.32,<1.0
pydantic>=2.9,<3.0
httpx>=0.27,<1.0
json-repair>=0.30,<1.0
pytest>=8.3,<9.0
```

**Struktur Folder Repositori Modular (Kepemilikan Eksklusif Anti-Konflik Git):**
```text
whenyhh-ai/
├── app/
│   ├── main.py                  # Entry point FastAPI, StaticFiles, lifespan init_db (Anggota 3)
│   ├── schemas.py               # Kontrak Pydantic v2 bersama — DIBEKUKAN HARI 2 (Bersama)
│   ├── db/
│   │   ├── connection.py        # Factory SQLite WAL, PRAGMA wajib, BEGIN IMMEDIATE (Anggota 1)
│   │   └── schema.sql           # 7 tabel STRICT + indeks DAG (Anggota 1)
│   ├── engine/
│   │   ├── dag_repo.py          # Recursive CTE lineage, commit node, fork_branch (Anggota 1)
│   │   ├── state_mutator.py     # Core vs State, clamping relasi asimetris, jangkar (Anggota 1)
│   │   ├── context_compiler.py  # Dynamic Context Compiler O(1) <= 2.200 token (Anggota 2)
│   │   └── sim_pulse.py         # Generator Sim Pulse & Ticking Clock ber-seed (Anggota 2)
│   ├── llm/
│   │   ├── client.py            # Klien OpenAI-compatible (Ollama/LM Studio/BYOM) (Anggota 2)
│   │   └── resilience.py        # Pipa 4 lapis (no-think, json-repair, Pydantic, fallback) (Anggota 2)
│   ├── routers/
│   │   ├── scenarios.py         # List, load seed, export JSON/Markdown (Anggota 3)
│   │   ├── turns.py             # Eksekusi giliran, fork, checkout, payload graf (Anggota 3)
│   │   └── system.py            # /healthz, /readyz, /api/llm/test, /api/llm/models (Anggota 3)
│   └── seeds/
│       ├── kampus_anti_scam.json
│       ├── kebijakan_parkir.json
│       └── misteri_pelabuhan_1928.json
├── static/
│   ├── index.html               # Cockpit 3-Pane + Modal T&C + Modal BYOM + Modal FAQ (Anggota 4)
│   ├── css/
│   │   ├── input.css            # Sumber Tailwind v4 + token warna anti-slop (Anggota 4)
│   │   └── app.css              # Hasil kompilasi Tailwind v4 Standalone CLI (offline)
│   ├── js/
│   │   ├── api.js               # Wrapper fetch() + header X-LLM-API-Key ephemeral (Anggota 4)
│   │   ├── dag_view.js          # Cytoscape + cytoscape-dagre swimlane click-to-fork (Anggota 4)
│   │   ├── relation_view.js     # Cytoscape bezier panah asimetris A->B & B->A (Anggota 4)
│   │   ├── telemetry.js         # Grafik Plotly-basic token O(1) vs O(N^2) (Anggota 4)
│   │   └── app.js               # State UI, DOMPurify markdown render, T&C gate (Anggota 4)
│   └── vendor/                  # Salinan lokal .min.js agar 100% offline
├── tests/                       # 6 suite pytest deterministik + MockLLMAdapter (Anggota 3)
├── docs/
│   ├── PRD-Whenyhh-ai-MVP.md
│   └── TechDesign-Whenyhh-ai-MVP.md
├── agent_docs/                  # Panduan terstruktur untuk agen coding & anggaran API $100
├── .github/workflows/ci.yml     # GitHub Actions otomatis jalankan pytest pada tiap PR
├── AGENTS.md
├── CLAUDE.md
├── GEMINI.md
├── MEMORY.md
├── REVIEW-CHECKLIST.md
├── TERMS.md                     # Naskah lengkap T&C 3 segmen + rujukan Indonesia
├── LICENSE                      # Lisensi MIT
└── requirements.txt
```

---

## Building Your Features

### Feature 1: Externalized State Engine dan Git-DAG Imutabel

**Complexity:** Medium

**Files to create:**
- `app/db/schema.sql` — Definisi 7 tabel `STRICT` (`scenarios`, `actor_cores`, `branches`, `nodes`, `actor_states`, `relation_edges`, `causal_anchors`) plus indeks `idx_nodes_parent`, `idx_nodes_branch_turn`, dan `idx_anchors_origin`.
- `app/db/connection.py` — *Connection factory* yang mengeksekusi `PRAGMA journal_mode=WAL` saat inisialisasi serta `PRAGMA synchronous=NORMAL`, `PRAGMA busy_timeout=5000`, `PRAGMA foreign_keys=ON`, `PRAGMA cache_size=-16000` di setiap koneksi, dilengkapi *context manager* transaksi `BEGIN IMMEDIATE`.
- `app/engine/dag_repo.py` — Fungsi `get_lineage(conn, node_id)` menggunakan `WITH RECURSIVE`, `commit_turn(...)`, dan `fork_branch(conn, scenario_id, from_node_id, new_branch_name)`.
- `app/engine/state_mutator.py` — Fungsi murni Python yang membaca state induk, menerapkan `ActorStateDelta` dan `RelationDelta` secara terpisah untuk `(source, target)`, memvalidasi `actor_id` terhadap `actor_cores` (mengabaikan ID hasil halusinasi), serta melakukan *clamping* deterministik.

**API Endpoints:**
- `GET /api/scenarios/{scenario_id}/graph` — Mengembalikan `nodes`, `edges`, `branches`, `head_node_id`, dan daftar `causal_anchors` pada garis keturunan aktif.
- `POST /api/branches/fork` — Membuat cabang baru dari `from_node_id` tanpa menyentuh simpul cabang asal.
- `POST /api/branches/checkout` — Memindahkan `head_node_id` tampilan ke simpul atau cabang pilihan dan mengembalikan state + relasi + jangkar pada titik tersebut.

**Test with:** `pytest tests/test_dag_immutability.py tests/test_state_and_relations.py -v`

---

### Feature 2: Dynamic Context Compiler O(1) dan Telemetri Token

**Complexity:** Medium

**Files to create:**
- `app/engine/context_compiler.py` — Merakit larik `messages` baru dari SQLite dengan plafon ketat **<= 2.200 token input**:
  1. **Zona Prefiks Statis (~700 token, `messages[0]` role `system`):** Aturan inti *roleplay* (`scenario-and-roleplay-v1-5-id` tanpa *Heartbeat/changelog*) + kontrak JSON `TurnResponse` + daftar `actor_cores` yang diurutkan deterministik berdasarkan `actor_id` agar identik *byte-for-byte* lintas giliran (*KV prefix cache hit*).
  2. **Zona Sufiks Dinamis (<= 1.500 token, `messages[1]` role `user`):** `actor_states` terkini + matriks `relation_edges` + direktif `sim_pulse` & *Ticking Clock* + maksimal 10 *Jangkar Kausal* aktif khusus garis keturunan ini (urut `severity DESC, origin_node_id DESC`) + `arc_summary` (<= 240 token) + *sliding window* hanya 2 giliran narasi bersih terakhir (tanpa JSON delta) + aksi pengguna saat ini.
  3. **Penghitung & Pemangkas Anggaran:** Menggunakan estimasi konservatif Bahasa Indonesia (~1,35 token/kata atau `len(text) // 3`) untuk memangkas `arc_summary` dan jumlah jangkar bila total mendekati 2.200 token.
- `app/engine/sim_pulse.py` — Menggunakan `random.Random(f"{rng_seed}:{parent_node_id}:{turn_index}")` agar dinamika *Sim Pulse* dan *Ticking Clock* deterministik dan dapat direproduksi per cabang.
- `static/js/telemetry.js` — Merender grafik garis `Plotly.newPlot()` (bundel `plotly-basic`) yang membandingkan `prompt_tokens` aktual Whenyhh.ai terhadap kurva proyeksi *chat-skill* O(N^2) sepanjang giliran.

**Test with:** `pytest tests/test_context_compiler_o1.py -v` (menjalankan simulasi 100 giliran berturut-turut dengan `MockLLMAdapter`).

---

### Feature 3: Gerbang LLM Lokal 8GB, BYOM Rp0, dan Ketahanan JSON 4 Lapis

**Complexity:** Medium-Hard

**Files to create:**
- `app/schemas.py` — Kontrak Pydantic v2 datar (`TurnResponse`, `ActorStateDelta`, `RelationDelta`, `LLMConfig`) dengan `ConfigDict(extra="forbid")` dan tanpa batas `minimum`/`maximum` di level JSON Schema (seluruh *clamping* dilakukan oleh `@field_validator` Python agar kompatibel dengan semua penyedia *strict schema*).
- `app/llm/client.py` — Klien asinkron berbasis `httpx.AsyncClient` ke endpoint OpenAI-compatible (`/v1/chat/completions` dan `/v1/models`), dengan preset URL:
  - Ollama Lokal: `http://127.0.0.1:11434/v1` (kirim `think: false` untuk keluarga Qwen3/Qwen3.5)
  - LM Studio Lokal: `http://127.0.0.1:1234/v1`
  - Groq Free: `https://api.groq.com/openai/v1`
  - Gemini AI Studio: `https://generativelanguage.googleapis.com/v1beta/openai/`
  - OpenRouter Free: `https://openrouter.ai/api/v1`
  - Mock Offline: tanpa panggilan HTTP.
- `app/llm/resilience.py` — Implementasi **Resilience Pipeline 4 Lapis**:
  1. *Constrained decoding* (`response_format` `json_schema`, *fallback* otomatis ke `json_object` jika HTTP 400 dari penyedia).
  2. Penghapusan tag `<think>...</think>`, `<|channel>thought...`, dan pagar Markdown, dilanjutkan perbaikan sintaks oleh `json_repair.loads()`.
  3. Validasi ketat `TurnResponse.model_validate()`.
  4. Maksimal 1x *self-healing retry* memakai ringkasan `exc.errors(include_url=False)`; bila tetap gagal atau `httpx.TimeoutException`, keluarkan **Deterministic Safe Fallback** (narasi teks yang berhasil diselamatkan atau pesan ramah + delta kosong + bendera `is_fallback: true`).

**API Endpoints:**
- `POST /api/turns` — Menerima `scenario_id`, `parent_node_id`, `branch_id`, `user_action`, `llm_config` (plus header opsional `X-LLM-API-Key`), menjalankan siklus Compiler -> LLM Resilience -> Mutator -> SQLite Commit, lalu mengembalikan `NodeDTO` + telemetri token.
- `GET /api/llm/models` — Mengambil daftar model terpasang dari Ollama/LM Studio lokal.
- `POST /api/llm/test` — Uji koneksi 1 prompt mikro dan mengembalikan status + latensi (ms).

**Test with:** `pytest tests/test_llm_resilience.py tests/test_api_contracts.py -v`

---

### Feature 4: Antarmuka Cockpit 3-Pane Anti-AI-Slop, 3 Skenario Bawaan, FAQ, T&C, dan Ekspor

**Complexity:** Medium

**Files to create:**
- `app/seeds/*.json` — 3 skenario siap pakai berbahasa Indonesia (`kampus_anti_scam.json`, `kebijakan_parkir.json`, `misteri_pelabuhan_1928.json`).
- `static/index.html` & `static/js/app.js` — Tata letak 3-pane bergaya GitKraken, modal Persetujuan Aktif T&C pada kunjungan pertama (`sessionStorage` flag `whenyhh_tc_accepted`), modal Pengaturan BYOM, halaman/modal FAQ 3 segmen (memuat tautan resmi Healing119.id, CekRekening.id, IASC OJK), serta rendering narasi aman via `DOMPurify.sanitize(marked.parse(text))`.
- `static/js/dag_view.js` — Kanvas **Cytoscape.js + `cytoscape-dagre` v4.1.0** dengan jalur *swimlane* cabang berwarna terpisah, label ID simpul monospasi (`S01`, `S03b`), dan menu klik-simpul ("Pindah ke Simpul / Checkout" dan "Fork Cabang Baru dari Sini").
- `static/js/relation_view.js` — Kanvas **Cytoscape.js** untuk graf relasi berarah asimetris memakai `'curve-style': 'bezier'` dan `'target-arrow-shape': 'triangle'` agar panah `A -> B` dan `B -> A` melengkung terpisah dan berwarna sesuai sentimen (`Trust >= +2` hijau-teal `#2DD4BF`, netral `#64748B`, `Tension >= 3` amber/merah `#F59E0B`/`#FB7185`).
- `app/routers/scenarios.py` — Endpoint `GET /api/scenarios/{id}/export?format=json|md` untuk unduhan lokal.

**Test with:** `pytest tests/test_seed_scenarios.py -v` + verifikasi manual visual di browser (desktop 1080p dan responsif 768px) tanpa error konsol.

---

## Design Implementation

### Matching Your PRD Vision: Cockpit GitKraken-Inspired, Anti-AI-Slop

**Aturan Visual Wajib (`craftwork-design` + `anti-ai-slop-uiux`):**
- **Dilarang keras:** Aksen ungu/indigo (`#6366f1`/`#8b5cf6`), gradien neon, judul `bg-clip-text`, font Inter/Geist sebagai judul utama, ikon emoji di tombol/menu, kartu 3-kolom identik, `hover:scale-105`, atau em-dash/middle-dot pada teks UI yang terlihat.
- **Satu paket ikon:** Lucide Icons (`static/vendor/lucide.min.js`) gaya *outline* `16px-20px` dengan `stroke="currentColor"`.

#### Design System Tokens (`static/css/input.css`)
```css
@import "tailwindcss";

:root {
  /* 60-30-10 Neutral Dark Charcoal Surface (no pure #000) */
  --bg-canvas: #14161A;
  --bg-panel: #1B1E24;
  --bg-elevated: #232730;
  --border-hairline: #2E333E;

  /* Text (WCAG AA >= 4.5:1 on #1B1E24) */
  --text-primary: #E6E8EC;
  --text-secondary: #9AA3B2;
  --text-muted: #707A8C;

  /* Single Brand Accent (Non-Purple Teal) */
  --accent-primary: #1F9D8B;
  --accent-primary-hover: #25B4A0;

  /* Functional Semantic & DAG Swimlane Colors */
  --lane-main: #2DD4BF;
  --lane-branch-2: #38BDF8;
  --lane-branch-3: #F59E0B;
  --lane-branch-4: #FB7185;
  --status-warn: #D97706;
  --status-danger: #E11D48;

  /* Typography */
  --font-sans: "IBM Plex Sans", "Plus Jakarta Sans", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
}

/* Mandatory Accessibility Motion Guard */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

#### Tailwind v4 Zero-Node Build & Offline Polish
- **Hari 1-12 (Prototipe cepat):** Boleh memakai Play CDN `<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>` agar cepat iterasi.
- **Hari 13 (Kompilasi Offline Final):** Unduh biner **Tailwind CSS v4 Standalone CLI** (tanpa Node.js) dan jalankan sekali untuk menghasilkan `static/css/app.css`, lalu hapus tag CDN agar 100% berjalan saat Wi-Fi mati:
  ```bash
  ./tailwindcss -i ./static/css/input.css -o ./static/css/app.css --minify
  ```

#### Mobile & Tablet Responsiveness
- **Desktop (`>= 1024px`):** Grid 3-pane penuh (`230px | 1fr | 340px`) dengan pemisah garis tipis `1px solid var(--border-hairline)`.
- **Tablet & Mobile (`< 1024px` / `< 768px`):** Pane tengah tampil penuh; tombol bilah atas membuka Pane Kiri (Cabang & Jangkar) dan Pane Kanan (Inspektor Relasi/State/Token) sebagai panel laci (*slide-over drawer*) dengan transisi `transform 150ms ease-out`.

---

## Database & Data Storage

### Local-First SQLite (`whenyhh.db`)
- **Tool:** Modul bawaan `sqlite3` Python (tanpa instalasi server eksternal, biaya Rp0).
- **Concurrency & Safety:** Mode `WAL` + `busy_timeout=5000` + `foreign_keys=ON` + transaksi tulis `BEGIN IMMEDIATE` + tabel `STRICT`.
- **Backup & Portability:** Satu berkas `whenyhh.db` di lokal (wajib masuk `.gitignore` agar data tes tidak mencemari GitHub). Pengguna dapat mengekspor skenario utuh ke JSON/Markdown lewat tombol Ekspor di UI.
- **Relasi Inti:**
  - `scenarios` 1 -> N `actor_cores` (identitas permanen lintas cabang)
  - `scenarios` 1 -> N `branches` -> `head_node_id`
  - `nodes` membentuk pohon DAG melalui `parent_id -> nodes(node_id)`
  - `actor_states` (PK: `node_id, actor_id`) dan `relation_edges` (PK: `node_id, source_actor_id, target_actor_id`) terikat pada setiap `node_id` sehingga *checkout* dan *fork* bersifat instan dan imutabel.
  - `causal_anchors` terikat pada `origin_node_id` dan disaring melalui *Recursive CTE* garis keturunan aktif.

---

## Product AI Features

- **Use cases:** Generasi prosa adegan Bahasa Indonesia dan pembaruan status/relasi/jangkar kausal terstruktur (`TurnResponse`).
- **Data sensitivity:** Lokal sepenuhnya (privat) pada mode Ollama/LM Studio; data publik/non-PII saja pada mode BYOM gratis *cloud*.
- **Provider options:** Ollama lokal (default, `http://127.0.0.1:11434/v1`), LM Studio (`http://127.0.0.1:1234/v1`), BYOM OpenAI-compatible (Groq, Gemini AI Studio, OpenRouter `:free`), dan `MockLLMAdapter`.
- **Data boundary:** Hanya paket *Dynamic Context Compiler* (<= 2.200 token) yang dikirim ke endpoint LLM; tidak ada akses tulis langsung ke database atau berkas lokal.
- **Retention/training setting:** Mode lokal 0% retensi pihak ketiga. Untuk mode BYOM, UI menampilkan lencana peringatan privasi khusus (tier gratis Gemini dan Mistral melatih dari prompt; pengguna dilarang mengirim data pribadi sesuai UU PDP No. 27/2022).
- **Structured outputs:** Skema Pydantic datar `TurnResponse` (`extra="forbid"`) + sakelar *no-think* spesifik-model + pipa ketahanan 4 lapis (`json-repair` + 1x *retry* + *Deterministic Safe Fallback*).
- **Tool permissions:** Read-only context input, zero autonomous tool execution, zero destructive database access.
- **Latency/cost targets:** Biaya Rp0; target latensi lokal <= 6 detik per giliran (narasi ~180 kata + delta ~90 token pada ~40-57 t/s di GPU 8GB).
- **Failure fallback:** Narasi diselamatkan (atau pesan ramah jika *timeout*) + state lama dipertahankan (*no-op delta*) + lencana kuning di UI; tidak pernah melempar HTTP 500.
- **User confirmation:** Persetujuan aktif modal T&C sebelum sesi pertama; konfirmasi eksplisit saat memilih penyedia BYOM *cloud*.
- **Eval set:** 6 suite `pytest` (>= 34 uji deterministik) yang memverifikasi jalur normal, asimetri relasi, isolasi jangkar antar-cabang, ketahanan 5 pola JSON rusak, nol kebocoran API key, dan uji stres 100 giliran O(1).
- **Telemetry:** `prompt_tokens`, `completion_tokens`, dan latensi disimpan lokal di tabel `nodes` untuk grafik Plotly; `X-LLM-API-Key` dilarang keras masuk log atau database.

---

## Builder Exit Review

**Not applicable for MVP.** Whenyhh.ai tidak menggunakan platform *no-code/hosted AI builder* (seperti Lovable, Bolt, atau Replit) sehingga tidak ada risiko *vendor lock-in*. Seluruh kode sumber berada langsung di repositori GitHub milik tim sejak Hari 1 dan berjalan lokal murni dengan Python standar.

---

## Agent Orchestration Decision & Mitigasi Kesulitan Git/Pemahaman Kode

Untuk mencegah *over-engineering* dan langsung menjawab kekhawatiran terbesar tim (**kesulitan penggunaan Git & kode yang belum dipahami**), kita menerapkan orkestrasi sederhana dengan pagar belajar wajib:

| Need | Pattern |
|------|---------|
| Pembangunan modul fitur MVP | **Satu lead coding agent** (Claude Code via API $100, opsional Gemini / LM Studio) membaca `CLAUDE.md`, dibatasi menyunting 1-3 berkas per sesi sesuai kepemilikan anggota. |
| Mencegah kebingungan kode anggota tim | **Mode "Jelaskan Dulu" di `CLAUDE.md`:** Setelah menulis fungsi, agen wajib mencetak ringkasan alur logika 3-5 baris dalam Bahasa Indonesia sederhana agar mahasiswa paham sebelum melakukan commit. |
| Mencegah konflik Git & kepanikan terminal | **Alur Git Aman 5 Langkah (CLI atau GitHub Desktop)** + kepemilikan folder eksklusif antar-anggota + pembekuan `app/schemas.py` pada Hari ke-2. |

### Alur Git Aman Harian Tim (Bisa 100% Lewat GitHub Desktop)
1. **Sebelum mulai kerja:** Klik *Fetch origin* -> *Pull* pada cabang `main` agar salinan lokal terbaru.
2. **Buat cabang fitur sendiri:** Klik *New Branch* dengan nama jelas, misal `feat/dag-repo` atau `feat/ui-cytoscape` (jangan pernah edit langsung di `main`).
3. **Edit hanya berkas di folder milik sendiri** dan jalankan `pytest -v` sebelum commit.
4. **Commit & Push:** Tulis pesan ringkas bergaya konvensional (misal `feat(dag): tambah fungsi fork_branch`) lalu klik *Publish/Push branch*.
5. **Buka Pull Request (PR) + 3 Baris Penjelasan Manual:** Tulis 3 kalimat buatan sendiri tentang cara kerja kode tersebut, tunggu CI hijau (`pytest` lulus) dan 1 persetujuan rekan tim, lalu klik *Squash and merge*.

---

## AI Assistance Strategy (Anggaran Claude API $100 USD)

### Which AI Tool & Model for What
| Task | Recommended Tool & Model | Effort | Budget Role |
|------|--------------------------|--------|-------------|
| Kontrak inti (`app/schemas.py`, `schema.sql`) & bug buntu (>2× gagal) | **Claude Code — Opus** (Plan Mode) | `medium` / `high` | Maks ~$12-$15 total proyek |
| Algoritma kritis (`dag_repo.py`, `context_compiler.py`, `resilience.py`) & draf awal Cockpit UI | **Claude Code — Sonnet** | `high` | Inti kualitas (~$35 total) |
| Routers FastAPI, `pytest` suites, iterasi JS/CSS, bug fix standar | **Claude Code — Sonnet** *(Default 80% kerja)* | `medium` | Workhorse hemat (~$30 total) |
| Refactor kecil, docstring, ringkasan PR | **Claude Code — Haiku** / Sonnet `low` | `low` / `medium` | Sangat murah (~$5 total) |
| Skenario seed panjang (`app/seeds/*.json`), FAQ, `TERMS.md`, `README.md` | **Gemini** (atau **LM Studio** lokal) | — | **Menghemat $15-$20 saldo Claude API** |

*(Alokasi lengkap per fase dan kontrol biaya harian tersedia di `agent_docs/claude_api_budget.md`.)*

### Deterministic Verification Loops (Closed-Loop untuk Agen)
1. **Self-Healing Backend Loop:** Setiap suntingan pada `app/` wajib diikuti `pytest -v`. Jika gagal, agen membaca *traceback* lengkap, membedakan apakah kesalahan ada di kode atau skema, memperbaiki maksimal 1-3 berkas terkait, lalu menjalankan `pytest -v` ulang hingga 0 kegagalan.
2. **Generate-Render-Inspect-Refine UI Loop:** Setiap perubahan di `static/` wajib diverifikasi dengan membuka `http://127.0.0.1:8000`, memeriksa tab Console browser (harus 0 error JS), menguji klik-simpul Cytoscape (desktop 1080p dan lebar 768px), dan menjalankan checklist Anti-AI-Slop sebelum commit.

### Exact Verification Commands
```bash
# Setup environment lokal
python -m venv .venv && pip install -r requirements.txt

# Jalankan server lokal Single-Origin (development & demo)
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Jalankan seluruh suite uji deterministik (tanpa GPU / tanpa API key)
pytest -v

# Kompilasi CSS produksi offline (Tailwind v4 Standalone CLI — dijalankan Hari ke-13)
./tailwindcss -i ./static/css/input.css -o ./static/css/app.css --minify
```

---

## Deployment & Distribution Plan

### Recommended Distribution: Local-First Single-Origin + Public GitHub Repository
Sesuai rubrik DDP1 Fasilkom UI (deliverable berupa tautan Repositori GitHub publik dan Video Demonstrasi YouTube <= 15 menit), aplikasi tidak memerlukan hosting *cloud* berbayar.

1. **Cara Menjalankan oleh Asdos/Penguji (3 Perintah di `README.md`):**
   ```bash
   git clone https://github.com/<org-atau-user>/whenyhh-ai.git && cd whenyhh-ai
   python -m venv .venv && pip install -r requirements.txt
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
   Lalu buka `http://127.0.0.1:8000` (langsung bisa dicoba memakai **Mock Mode** tanpa instalasi tambahan, **Ollama/LM Studio** lokal, atau **BYOM Groq/Gemini** gratis).
2. **Checklist Pra-Rekam Video Demo OBS 1080p (Hari 15-16):**
   - Pastikan `OLLAMA_KV_CACHE_TYPE=q8_0` dan `OLLAMA_CONTEXT_LENGTH=4096` aktif; pakai `qwen2.5:7b` atau `qwen3:8b` (`think=False`).
   - Tutup aplikasi desktop berat (termasuk GUI LM Studio jika memakai Ollama) agar ruang VRAM >= 1,6 GB aman untuk OBS NVENC.
   - Siapkan preset Groq Free sebagai cadangan instan 1-klik bila laptop perekam mengalami lonjakan beban CPU/GPU.

---

## Cost Breakdown

> **Note:** Verifikasi ulang tarif token terbaru Anthropic API dan ketentuan paket gratis penyedia BYOM langsung pada situs masing-masing sebelum digunakan; harga dan kuota dapat berubah sewaktu-waktu. Last verified: 2026-11.

### Development & Demo Phase (MVP)
| Service / Tool | Tier | Estimated Cost | Notes |
|----------------|------|----------------|-------|
| Python, FastAPI, Uvicorn, SQLite, Pydantic, Pytest | Open-Source | Rp0 | 100% lokal |
| Cytoscape.js, dagre, Plotly-basic, Tailwind v4 CLI, DOMPurify, Lucide | Open-Source (MIT/Apache) | Rp0 | Disimpan lokal di `static/vendor/` |
| Ollama / LM Studio + Model Lokal 7B-8B | Gratis (Lokal) | Rp0 | Memanfaatkan GPU 8GB VRAM milik pengguna |
| GitHub Public Repo + GitHub Actions CI | Free Tier | Rp0 | Menit CI gratis melimpah untuk repo publik |
| Groq / Gemini AI Studio / OpenRouter `:free` (BYOM opsional) | Free Tier | Rp0 | Tanpa kartu kredit; patuhi batas kuota harian & aturan privasi |
| **Total Biaya Operasional Aplikasi** | | **Rp0** | **100% sesuai batas operasional PRD** |
| **Claude API (Pay-As-You-Go) — Alat Vibe-Coding** | API Kredit | **<= $95 USD** (plafon $100 USD) | Dialokasikan 4 fase (Fase 1 ~$15, Fase 2 ~$35, Fase 3 ~$30, Fase 4/Cadangan ~$15-$20) |

---

## Scaling Path (Pasca-DDP1 / v2)

Checkpoint berikut bersifat ilustratif apabila proyek dilanjutkan di luar mata kuliah DDP1:
- **Tahap Penggunaan Lokal Lanjutan (1 pengguna, > 500 simpul):** Tambahkan *virtual scrolling* pada daftar simpul pane kiri dan indeks komposit tambahan pada SQLite bila kueri graf melebihi 100ms.
- **Tahap Web Multi-User (v2, 100+ pengguna):** Migrasikan `sqlite3` ke PostgreSQL dengan skema relasional yang identik, tambahkan autentikasi sesi, *rate limiting* per pengguna, serta *queue* asinkron untuk panggilan LLM.

## Important Limitations

1. **Batas VRAM Fisik 8GB saat Rekaman Layar:** Model 12B-14B akan tumpah ke RAM dan melambat hingga < 11 token/detik.
   - *Workaround:* Kunci rekomendasi default pada `qwen2.5:7b` / `qwen3:8b` dengan `q8_0` KV cache dan `num_ctx=4096`.
2. **Ketidakstabilan Format JSON Model Kecil (< 7B) & Thinking Mode:** Model kecil kadang menyelipkan teks ekstra atau membuang waktu di blok `<think>`.
   - *Workaround:* Nonaktifkan *thinking* via parameter API (`think: false`), bersihkan tag via regex, perbaiki sintaks lewat `json-repair`, dan sediakan *Deterministic Safe Fallback*.
3. **Risiko Pembengkakan Tagihan API pada Sesi Panjang:** Pada Claude API *pay-as-you-go*, seluruh riwayat chat dikirim ulang di setiap giliran.
   - *Workaround:* Hard cap $95 USD di Anthropic Console, wajib `/clear` tiap selesai 1-3 berkas, default Sonnet `medium`, dan alihkan tugas konten teks panjang ke Gemini/LM Studio.
4. **Bias Simulasi Agen LLM:** Keluaran simulasi kebijakan atau sosial tidak merepresentasikan distribusi statistik opini publik nyata.
   - *Workaround:* Modal persetujuan aktif T&C, lencana non-preskriptif, dan halaman FAQ dengan rujukan resmi Indonesia (Healing119.id, CekRekening.id, IASC OJK).

## Learning Resources (Ramah Mahasiswa DDP1)

1. **GitHub Desktop Dasar (untuk yang belum terbiasa CLI Git):** `https://docs.github.com/en/desktop`
2. **FastAPI Tutorial Resmi (Bab First Steps & Request Body):** `https://fastapi.tiangolo.com/tutorial/`
3. **Python `sqlite3` Dokumentasi Resmi:** `https://docs.python.org/3/library/sqlite3.html`
4. **Cytoscape.js Dokumentasi Inti & Gaya Panah Bezier:** `https://js.cytoscape.org/`
5. **Pytest Getting Started:** `https://docs.pytest.org/en/stable/getting-started.html`

## Open Questions

- **TBD 1:** Apakah tim beranggotakan 3 orang atau 4 orang? (Jika 3 orang, Anggota 3 dan 4 berbagi tanggung jawab `static/js/telemetry.js` dan skenario *seed* ketiga; arsitektur dan perintah tetap sama).
- **TBD 2:** Apakah seluruh anggota ingin menambahkan `ruff` (linter/formatter Python ringan) ke CI, atau cukup `pytest -v` dulu agar langkah awal tetap sederhana?

## Success Checklist

### Before Starting Development (Hari 1-2)
- [ ] Spend limit $95 USD & alert ($25/$50/$75) aktif di Anthropic Console.
- [ ] Repositori GitHub publik dibuat, `LICENSE` (MIT) & `.gitignore` (mengecualikan `.venv/`, `.env`, `*.db`) terpasang.
- [ ] Seluruh anggota berhasil clone repo (via GitHub Desktop atau CLI) dan menjalankan `pytest` dasar.
- [ ] `app/schemas.py` disepakati dan dibekukan pada Hari ke-2.
- [ ] Ollama dengan `qwen2.5:7b` terverifikasi berjalan lancar pada `num_ctx=4096` dan `q8_0` KV cache di PC 8GB VRAM.

### During Development (Hari 3-13)
- [ ] Setiap anggota bekerja di cabang fitur sendiri sesuai folder eksklusif dan menyertakan 3 baris penjelasan manual pada tiap PR.
- [ ] Gerbang Integrasi End-to-End tercapai pada Hari ke-9 (Selasa, 1 Desember 2026) dengan sisa saldo Claude API >= $45 USD.
- [ ] Aset JS vendor diunduh ke `static/vendor/` dan `app.css` dikompilasi dengan Tailwind v4 Standalone CLI pada Hari ke-13.

### Before Launch (Hari 14-17)
- [ ] Feature Freeze keras pada Hari ke-14 (Minggu, 6 Desember 2026).
- [ ] Minimal 34 uji `pytest` lulus 100% di lokal dan GitHub Actions CI.
- [ ] Uji demo offline penuh (Wi-Fi mati) lulus tanpa error konsol dan tanpa HTTP 500.
- [ ] Video demonstrasi YouTube (13-14 menit) menampilkan seluruh anggota tim secara bergantian dan siap dikumpulkan sebelum 10 Desember 2026 pukul 23:59 WIB.

## Definition of Technical Success

Implementasi teknis Whenyhh.ai dinyatakan berhasil apabila:
- Berjalan mulus di `http://127.0.0.1:8000` dengan 0 HTTP 500 baik pada mode Ollama lokal, LM Studio, BYOM gratis, maupun Mock offline.
- Membuktikan secara deterministik lewat `pytest` bahwa input prompt tetap <= 2.200 token hingga giliran S100 dan cabang Git-DAG terisolasi penuh.
- Lulus audit visual Anti-AI-Slop dan aksesibilitas WCAG AA + `prefers-reduced-motion`.
- Total biaya Claude API tetap di bawah plafon $100 USD dan seluruh anggota tim mampu menjelaskan alur kode di modul masing-masing pada repositori GitHub publik.

---
*Technical Design for: Whenyhh.ai*
*Approach: Single-Origin Python Web App (FastAPI + SQLite WAL + Zero-Build HTML/JS)*
*Estimated Time to MVP: 17 hari kerja aktif + 1 hari buffer (23 Nov - 10 Des 2026)*
*Estimated Cost: Rp0 operasional aplikasi + <= $95 USD Claude API (plafon $100 USD)*

---
## Handoff Context
<!-- Summary for the next workflow step. Keep this block with the saved document. -->
- Stage: techdesign
- App name: Whenyhh.ai
- User level: A (A = vibe coder, B = developer, C = in-between)
- Target platform: Web lokal Single-Origin (http://127.0.0.1:8000)
- Budget: Rp0 operasional aplikasi + $100 USD Claude API (pay-as-you-go, hard cap $95 USD) untuk vibe-coding
- Timeline: 17 hari kerja aktif + 1 hari buffer (23 Nov - 10 Des 2026 pukul 23:59 WIB)
- AI in product scope: yes
- Chosen stack: Frontend Zero-Build HTML/JS + Cytoscape.js + cytoscape-dagre v4.1.0 + Plotly-basic + marked + DOMPurify + Lucide Icons; Styling Tailwind CSS v4 (Play CDN dev -> Standalone CLI app.css offline); Backend Python 3.11+ FastAPI + Uvicorn + Pydantic v2 + httpx + json-repair; Database SQLite bawaan (sqlite3 WAL + STRICT + BEGIN IMMEDIATE + Recursive CTE); Product AI Ollama lokal 8GB VRAM (default qwen2.5:7b / qwen3:8b, q8_0 KV cache) + LM Studio + BYOM OpenAI-compatible (Groq/Gemini/OpenRouter) + MockLLMAdapter; Deployment lokal Single-Origin + GitHub Public Repo (tanpa Auth, Payments, atau Cloud Hosting)
- AI coding tool: Claude Code via Claude API ($100 USD pay-as-you-go; default Sonnet medium, Opus Plan Mode/blocker, Haiku mekanis), opsional Gemini (konten/review), opsional LM Studio lokal
- Constraints: Komponen utama wajib Python (DDP1); VRAM 8GB berbagi dengan OBS Studio 1080p (~6,0-6,2 GB aman); 100% offline-ready; zero Node.js build; API key BYOM ephemeral di sessionStorage + X-LLM-API-Key (0 baris di DB); kepatuhan UU PDP No. 27/2022 & SE Menkominfo No. 9/2023; desain cockpit GitKraken anti-AI-slop (charcoal + teal, bebas ungu/Inter/emoji, wajib prefers-reduced-motion); mitigasi kesulitan Git & pemahaman kode tim; jaga saldo Claude API <= $95 USD
- Decisions: Pembagian folder eksklusif anti-konflik Git + alur GitHub Desktop 5 langkah + 3 baris penjelasan manual di tiap PR; pembekuan app/schemas.py di Hari ke-2; 4-layer JSON resilience pipeline dengan max 1x retry ke Deterministic Safe Fallback; 6 suite pytest deterministik (>= 34 uji) via app.dependency_overrides; protokol hemat Claude API (/clear per fitur, /cost check, offload konten panjang ke Gemini)
- Open questions: Jumlah pasti anggota tim (3 atau 4 orang); apakah perlu menambahkan linter ruff ke CI atau cukup pytest
- Research status: Completed (Deep Research report verified and integrated)
- Source files: research-Whenyhh-ai.md, docs/PRD-Whenyhh-ai-MVP.md -> docs/TechDesign-Whenyhh-ai-MVP.md
---

```json
{
  "schemaVersion": 1,
  "documentType": "techdesign",
  "appName": "Whenyhh.ai",
  "stack": {
    "frontend": "Zero-Build HTML/JS + Cytoscape.js (cytoscape-dagre v4.1.0) + Plotly-basic + marked + DOMPurify + Lucide Icons",
    "backend": "Python 3.11+ (FastAPI + Uvicorn + Pydantic v2 + httpx + json-repair)",
    "database": "SQLite (sqlite3 standar, WAL mode, STRICT tables, Recursive CTE)",
    "styling": "Tailwind CSS v4 (Play CDN saat dev -> Standalone CLI static/css/app.css untuk offline)",
    "deployment": "Local-First Single-Origin (http://127.0.0.1:8000) + Public GitHub Repository"
  },
  "commands": {
    "setup": "python -m venv .venv && pip install -r requirements.txt",
    "dev": "uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload",
    "test": "pytest -v",
    "typecheck": "",
    "lint": "",
    "build": "./tailwindcss -i ./static/css/input.css -o ./static/css/app.css --minify"
  },
  "aiScope": "in-app AI"
}
```
