# Project Brief — Whenyhh.ai

## Product

- **One-line vision:** Workbench web lokal visualisasi skenario bercabang, simulasi keputusan *what-if*, dan *roleplay* interaktif berbasis Externalized State Engine O(1) yang bebas amnesia konteks dan bebas pajak *changelog*.
- **Target users:**
  1. Mahasiswa dan masyarakat umum (latihan negosiasi, keputusan, dan literasi anti-penipuan tanpa risiko nyata).
  2. Pemangku kebijakan dan peneliti (eksplorasi *what-if* non-preskriptif lintas pemangku kepentingan secara lokal/privat).
  3. Novelis dan kreator digital (eksplorasi cabang plot panjang 50-100+ giliran secara imersif).
- **Primary user outcome:** Menjalankan simulasi bercabang berbahasa Indonesia secara gratis di komputer lokal, melihat pergeseran relasi asimetris (`A -> B` berbeda dari `B -> A`) dan *Jangkar Kausal* per cabang, melakukan *click-to-fork* di pohon Git-DAG untuk membandingkan konsekuensi, dan memverifikasi efisiensi token O(1).

## Scope

- **Must ship (P0):**
  - Externalized State Engine (`Core` vs `State`, relasi berarah asimetris, *Jangkar Kausal* terisolasi via Recursive CTE) dan Git-DAG imutabel (*commit*, *click-to-checkout*, *click-to-fork*).
  - *Dynamic Context Compiler* berplafon O(1) <= 2.200 token input ramah *KV prefix cache* + panel Telemetri Token Plotly.
  - Gerbang LLM Lokal 8GB VRAM (Ollama default, LM Studio opsional), BYOM cloud gratis (Groq, Gemini, OpenRouter; kunci *ephemeral*), `MockLLMAdapter`, dan Pipa Ketahanan JSON 4 Lapis menuju *Deterministic Safe Fallback*.
  - Antarmuka *cockpit* 3-pane Anti-AI-Slop bergaya GitKraken, 3 skenario *seed* siap pakai, halaman FAQ, modal persetujuan aktif T&C Indonesia (UU PDP, SE Menkominfo 9/2023, rujukan Healing119.id & IASC OJK), dan ekspor lokal JSON/Markdown.
- **Not in v1 (Out of Scope):**
  - Login, akun multi-user, dan *cloud hosting*.
  - *Three-way merge* dua cabang kompleks beserta resolusi konflik otomatis.
  - Audio/TTS, *speech-to-text*, dan generator gambar karakter.
  - Perintah Git lanjutan (`rebase`, `bisect`, `cherry-pick`, `stash`).
  - Sistem pembayaran dan langganan.

## Principles

- Selesaikan alur inti dan tes deterministik `pytest` sebelum mempercantik detail sekunder.
- Pilih teknologi sederhana tanpa *build toolchain* rumit agar 100% tim DDP1 paham setiap baris kode yang mereka kerjakan.
- Aplikasi wajib 100% bisa didemokan secara offline (Wi-Fi mati) pada Hari 13 sebelum *Feature Freeze* Hari 14.
- Pertahankan biaya operasional aplikasi Rp0, jaga penggunaan Claude API pengembangan <= $95 USD (dari plafon $100 USD), dan penuhi tenggat keras Kamis, 10 Desember 2026 pukul 23:59 WIB.

## AI Position

- **AI is used for:** Menulis prosa adegan Bahasa Indonesia alami dan memancarkan perubahan status/relasi/jangkar kausal terstruktur (`TurnResponse` JSON delta).
- **AI is not used for:** Menyimpan memori persisten, menghitung *clamping* angka status, menentukan keputusan kebijakan publik secara otomatis, memberi layanan medis/psikologis/hukum/finansial, atau memutasi basis data secara langsung.
- **Human approval required for:** Persetujuan aktif modal T&C sebelum memulai sesi pertama; aktivasi pengiriman data ke penyedia BYOM cloud pihak ketiga; interpretasi dan keputusan akhir atas hasil simulasi kebijakan (*human-in-the-loop*).
