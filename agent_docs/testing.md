# Testing — Whenyhh.ai

## Required Before Completion

- [ ] Seluruh tes `pytest` yang relevan lulus (0 failed, 0 skipped tanpa alasan).
- [ ] Perubahan UI pada `static/` sudah diperiksa di peramban (desktop 1080p dan lebar 768px) dengan 0 error Console.
- [ ] Untuk Hari 13+, kompilasi `static/css/app.css` berhasil dan mode offline penuh (Wi-Fi mati) terverifikasi.
- [ ] Tidak ada pengujian yang dilemahkan atau dihapus demi mendapatkan hasil hijau.
- [ ] Bukti perintah dan hasil uji dilaporkan di respons akhir.

## Commands

*(Status saat ini: unverified sampai scaffold dan suite `tests/` dibuat.)*

- All tests: `pytest -v`
- Single test file: `pytest tests/test_<nama>.py -v`
- Single test function: `pytest tests/test_<nama>.py -k "<nama_uji>" -v`
- Typecheck: Not configured
- Lint/format: Not configured
- Build CSS offline: `./tailwindcss -i ./static/css/input.css -o ./static/css/app.css --minify`
- Browser/device check: Jalankan `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`, buka `http://127.0.0.1:8000`, cek tab Console & Network DevTools, uji desktop 1080p dan 768px.

## What To Test

| Change type | Minimum check |
|-------------|---------------|
| Pure logic (`state_mutator`, `sim_pulse`, `context_compiler`) | Unit test `pytest` terisolasi |
| DB & API flow (`dag_repo`, `routers`, `schemas`) | Integration test FastAPI `TestClient` + SQLite `tmp_path` + `app.dependency_overrides` |
| UI behavior (`static/index.html`, `dag_view.js`, `relation_view.js`, `telemetry.js`) | Pemeriksaan manual di peramban (Console 0 error, klik simpul DAG, panah bezier, *drawer* 768px) + Audit Anti-AI-Slop |
| AI / Resilience (`client.py`, `resilience.py`, `context_compiler.py`) | Suite `test_llm_resilience.py` & `test_context_compiler_o1.py` (100 giliran) + verifikasi 0 baris API key di SQLite |

## 6 Mandatory Pytest Suites (Target >= 34 Uji Deterministik)

1. `tests/test_dag_immutability.py` (>= 6 uji): Akar S0, komit berantai, *fork* di S2 tanpa mengubah S3-S5 cabang asal, kueri *Recursive CTE*, penolakan `parent_id` fiktif/siklis.
2. `tests/test_state_and_relations.py` (>= 7 uji): `actor_cores` imutabel, relasi asimetris (`A -> B` tidak mengubah `B -> A`), *clamping* rentang angka, isolasi *Jangkar Kausal* antar-cabang.
3. `tests/test_context_compiler_o1.py` (>= 5 uji): Uji stres 100 giliran memakai `MockLLMAdapter` — input S10/S50/S100 selalu <= 2.200 token, `messages[0]` identik *byte-for-byte*, 0 JSON delta masuk *sliding window*.
4. `tests/test_llm_resilience.py` (>= 6 uji): JSON valid lolos, JSON + `<think>...</think>` + pagar Markdown pulih di Lapis 2, koma/kurung cacat pulih via `json-repair` tanpa *retry*, error skema pulih via 1x *retry*, gagal beruntun / *timeout* masuk *Deterministic Safe Fallback* (HTTP 200).
5. `tests/test_api_contracts.py` (>= 7 uji): Status kode endpoint (`200`, `201`, `404`, `422`), 0 baris `X-LLM-API-Key` di seluruh tabel SQLite, `/healthz` dan `/readyz`.
6. `tests/test_seed_scenarios.py` (>= 3 uji): Integritas kunci asing untuk 3 skenario bawaan (`kampus_anti_scam.json`, `kebijakan_parkir.json`, `misteri_pelabuhan_1928.json`).

## Core User Journeys to Verify Manually

1. **First-Visit T&C Gate:** Buka `http://127.0.0.1:8000` di tab *Incognito* -> input diblokir sampai kotak persetujuan T&C dicentang -> klik setuju -> workbench terbuka.
2. **Branching & Asymmetric Relations:** Muat skenario *Kebijakan Parkir Kampus* -> jalankan 3 giliran -> klik simpul `S02` di kanvas Git-DAG -> pilih *Fork Cabang Baru* -> ambil pilihan berbeda -> pastikan panah `A -> B` dan `B -> A` terpisah dan *Jangkar Kausal* antar-cabang tidak bercampur.
3. **BYOM & Fallback Safety:** Ganti model ke Mock / Ollama / Groq via modal Pengaturan -> klik *Uji Koneksi* -> simulasikan server mati/timeout -> pastikan UI menampilkan lencana kuning *Deterministic Safe Fallback* tanpa HTTP 500.
4. **Offline Readiness & Export:** Matikan Wi-Fi (Hari 13+) -> muat ulang halaman -> pastikan seluruh graf dan CSS tampil tanpa error jaringan -> uji ekspor berkas JSON dan Markdown lokal.

## AI Checks

- **Direct prompt:** Aksi valid menghasilkan `TurnResponse` valid, narasi Bahasa Indonesia alami, dan memperbarui `nodes`/`actor_states`/`relation_edges`.
- **Bad/indirect prompt:** Input pengguna mencoba memerintahkan AI memanipulasi skor ke +999 atau menyuntikkan `<script>alert(1)</script>` -> angka dipangkas oleh `@field_validator` dan HTML disanitasi oleh `DOMPurify`.
- **Hallucinated ID check:** LLM mengembalikan `actor_id` yang tidak terdaftar di `actor_cores` -> diabaikan secara aman oleh `state_mutator.py`.
- **Failure case:** JSON terpotong, berbungkus `<think>`, atau `httpx.TimeoutException` -> dipulihkan oleh pipa 4 lapis menuju *Deterministic Safe Fallback* (HTTP 200, 0 crash).
- **Data check:** `X-LLM-API-Key` terverifikasi tidak muncul di respons API, log terminal, maupun seluruh tabel SQLite.
