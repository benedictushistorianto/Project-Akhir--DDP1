# Whenyhh.ai

Workbench visualisasi skenario bercabang dengan Git-DAG, simulasi keputusan *what-if*, dan roleplay interaktif berbasis Externalized State Engine (SQLite + LLM lokal).

**Proyek Kelompok DDP1 — Fasilkom UI | Deadline: 10 Desember 2026**

---

## Fitur Utama

- **Git-DAG Imutabel** — setiap giliran (turn) menciptakan simpul baru; cabang bisa di-fork kapan saja
- **Context Compiler O(1)** — input LLM selalu ≤ 2.200 token terlepas panjang skenario
- **4-Layer JSON Resilience** — constrained decoding → pembersih think-tag → json-repair → Pydantic guard → Deterministic Safe Fallback
- **Relasi Aktor Asimetris** — trust, affinity, tension A→B berbeda dari B→A, divisualisasi Cytoscape bezier
- **Multi-Provider LLM** — Ollama lokal, LM Studio, Groq, OpenRouter, atau BYOM cloud (kunci API ephemeral di sessionStorage)
- **Ekspor JSON + Markdown** — seluruh skenario bisa diunduh tanpa internet
- **Offline-first** — semua aset vendor lokal di `static/vendor/`, tanpa CDN

---

## Instalasi (3 Perintah)

```bash
# 1. Buat virtual environment dan install dependensi
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt   # Windows
# atau: .venv/bin/pip install -r requirements.txt  (Linux/Mac)

# 2. Jalankan server (bind lokal, tidak terbuka ke jaringan)
.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 3. Buka di peramban
# http://127.0.0.1:8000
```

> **Catatan:** Server harus bind ke `127.0.0.1` (bukan `0.0.0.0`) agar tidak terbuka ke jaringan kampus saat demo OBS.

---

## Menjalankan Tes

```bash
.venv\Scripts\python.exe -m pytest -v
# Target: 73 passed, 0 failed
```

---

## Kompilasi CSS (opsional, Tailwind v4 Standalone)

Jika Tailwind v4 CLI sudah diunduh ke root proyek:

```bash
./tailwindcss -i ./static/css/input.css -o ./static/css/app.css --minify
```

Tanpa langkah ini, server akan menyajikan `input.css` langsung (cukup untuk development).

---

## Konfigurasi LLM

| Provider | Base URL Default | Model Default | Kunci API |
|---|---|---|---|
| `mock` | — | — | Tidak perlu (untuk demo/tes) |
| `ollama` | `http://127.0.0.1:11434/v1` | `qwen2.5:7b` | Tidak perlu |
| `lmstudio` | `http://127.0.0.1:1234/v1` | `local-model` | Tidak perlu |
| `groq` | `https://api.groq.com/openai/v1` | `llama-3.1-8b-instant` | Diperlukan |
| `openrouter` | `https://openrouter.ai/api/v1` | model `:free` | Diperlukan |
| `byom` | URL kustom Anda | Nama model Anda | Opsional |

**Variabel lingkungan Ollama untuk GPU 8GB + OBS:**
```bash
OLLAMA_FLASH_ATTENTION=1
OLLAMA_KV_CACHE_TYPE=q8_0
OLLAMA_CONTEXT_LENGTH=4096
```

---

## Struktur Proyek

```
whenyhh.ai/
├── app/
│   ├── db/           # connection.py (WAL + PRAGMA), schema.sql
│   ├── engine/       # dag_repo.py, state_mutator.py, context_compiler.py, sim_pulse.py
│   ├── llm/          # client.py (OpenAI-compat), resilience.py (4-layer pipeline)
│   ├── routers/      # scenarios.py, turns.py, system.py
│   ├── seeds/        # 3 seed JSON Bahasa Indonesia
│   ├── schemas.py    # Pydantic v2 (FROZEN setelah Hari 2)
│   └── main.py
├── static/
│   ├── css/input.css # Token CSS + layout cockpit
│   ├── js/           # app.js, api.js, dag_view.js, relation_view.js, telemetry.js
│   ├── vendor/       # 7 lib JS offline (Cytoscape, Plotly, Marked, dll.)
│   └── index.html
├── tests/            # 73 tes pytest (0 failed)
├── docs/             # PRD + TechDesign
├── agent_docs/       # Panduan tim
├── TERMS.md          # Syarat & Ketentuan (UU PDP + SE Menkominfo 9/2023)
├── MEMORY.md         # Riwayat keputusan proyek
└── AGENTS.md         # Aturan untuk coding agent
```

---

## Skenario Bawaan

| Skenario | Deskripsi | Aktor |
|---|---|---|
| Kampus Anti-Scam | Mahasiswa baru vs jaringan penipuan beasiswa | 4 aktor |
| Kebijakan Parkir Kampus | Rapat komite parkir kampus UI | 5 aktor |
| Misteri Pelabuhan 1928 | Fiksi sejarah: investigasi pelabuhan kolonial | 5 aktor |

---

## Lisensi & Kontak

Proyek ini dibuat untuk keperluan akademik (DDP1 Fasilkom UI). Lihat `TERMS.md` untuk syarat penggunaan lengkap.
