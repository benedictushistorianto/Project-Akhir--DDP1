# Claude API $100 USD Budget Playbook — Whenyhh.ai

Panduan operasional ini menjaga saldo **Claude API ($100 USD pay-as-you-go)** cukup dari Hari 1 (23 Nov 2026) sampai pengumpulan final (10 Des 2026) tanpa kehabisan kredit di minggu terakhir.

## 1. Pengaman Wajib di Anthropic Console (Hari 1)

- Setel **Hard Spend Limit** workspace ke **$95 USD** (menyisakan penyangga $5 USD dari penundaan pencatatan billing).
- Aktifkan notifikasi email pada ambang **$25**, **$50**, dan **$75 USD**.
- Jangan pernah membagikan satu kunci API mentah di repositori GitHub publik atau mengirimnya lewat chat terbuka; simpan lokal di environment variable shell.

## 2. Alokasi Anggaran 4 Fase (17 Hari Aktif)

| Fase | Rentang Tanggal | Alokasi Target | Sisa Saldo Minimal | Fokus Belanja Token |
|------|-----------------|----------------|--------------------|----------------------|
| **Fase 1: Fondasi & Schema Freeze** | Hari 1-4 (23-26 Nov) | ~$15 USD | >= $85 USD | Plan Mode `schemas.py` & `schema.sql` (Opus `medium`/Sonnet `high`), scaffold + `connection.py` (Sonnet `medium`). |
| **Fase 2: Mesin Inti & E2E** | Hari 5-9 (27 Nov-1 Des) | ~$35 USD | >= $50 USD | `dag_repo.py`, `state_mutator.py`, `context_compiler.py`, `resilience.py` (Sonnet `high`); routers & `conftest.py` (Sonnet `medium`). |
| **Fase 3: Cockpit UI, Tests & Offline** | Hari 10-13 (2-5 Des) | ~$30 USD | >= $20 USD | Draf awal 3-Pane Cockpit + Cytoscape `dag_view.js`/`relation_view.js` (Sonnet `high`); `telemetry.js`, drawer responsif, 6 suite `pytest` (Sonnet `medium`). |
| **Fase 4: Feature Freeze, Bug Bash & Cadangan** | Hari 14-17 (6-9 Des) | ~$15-$20 USD | >= $5 USD | Perbaikan bug terfokus (Sonnet `medium`) + darurat Opus `high` hanya jika bug membandel. |

*Target laju harian rata-rata: **$4-$5 USD/hari** (maksimal $8 USD pada hari puncak integrasi/UI).*

## 3. Matriks Model & Effort (Pay-As-You-Go)

| Jenis Pekerjaan | Model & Effort | Aturan Hemat |
|-----------------|----------------|--------------|
| Rancangan `schemas.py` / `schema.sql` atau bug gagal 2× di Sonnet | **Opus (`medium` / `high`)** | Hanya di Plan Mode atau investigasi sempit; langsung turun ke Sonnet saat menulis implementasi. |
| Algoritma inti (`dag_repo`, `context_compiler`, `resilience`) & UI awal | **Sonnet (`high`)** | Berikan berkas target eksplisit agar tidak memindai seluruh repo. |
| FastAPI routers, `pytest` suites, iterasi UI/CSS, bug fix biasa | **Sonnet (`medium`)** | **Setelan default untuk ~80% seluruh proyek.** |
| Refactor kecil, merapikan docstring, format komentar, ringkasan PR | **Haiku (`medium`)** atau **Sonnet (`low`)** | Paling irit untuk tugas mekanis berulang. |
| Skenario seed panjang (`app/seeds/*.json`), naskah FAQ, `TERMS.md`, `README.md` | **Offload ke Gemini / LM Studio ($0 Claude)** | Jangan membakar saldo API berbayar untuk mengarang prosa panjang. |

## 4. Enam Kebiasaan Wajib di Claude Code (API Mode)

1. **Wajib `/clear` setelah 1 fitur (1-3 berkas):** Pada API pay-as-you-go, setiap giliran menagih ulang seluruh riwayat sesi. Sesi 5 giliran jauh lebih murah dan akurat daripada sesi 35 giliran.
2. **Jalankan `/cost` setiap selesai 1 fitur:** Catat pengeluaran harian; jika 1 fitur ringan menembus $2-$3 USD, segera evaluasi apakah konteks terlalu gemuk atau model terlalu berat.
3. **Sebutkan nama berkas secara eksplisit di prompt:** Tulis *"Baca hanya `app/schemas.py` dan `app/engine/dag_repo.py`"* daripada membiarkan agen menjelajah seluruh folder.
4. **Jalankan tes terfokus lebih dulu:** Gunakan `pytest tests/test_dag_immutability.py -v` saat iterasi, baru jalankan `pytest -v` penuh sekali sebelum commit.
5. **Hindari `effort=max`:** Selain mahal (token berpikir berlipat), `max` sering menghasilkan *over-engineering* yang menyulitkan pemahaman kode tim DDP1.
6. **Manfaatkan jendela 5 menit Prompt Caching:** Kerjakan 1 fitur secara fokus berurutan sampai selesai lalu `/clear`, alih-alih meninggalkan sesi terbuka berjam-jam dan melanjutkan percakapan lama yang *cache*-nya sudah kedaluwarsa.
