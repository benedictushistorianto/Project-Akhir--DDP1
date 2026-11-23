# Syarat & Ketentuan Penggunaan — Whenyhh.ai

**Versi:** 1.0 — 23 November 2026
**Proyek:** DDP1 Fasilkom UI (Deadline 10 Desember 2026)

---

## 1. Perlindungan Data Pribadi (UU PDP No. 27 Tahun 2022)

Aplikasi Whenyhh.ai dirancang dengan prinsip **Privacy by Design**:

- Seluruh data skenario, narasi aktor, relasi, dan Jangkar Kausal disimpan **hanya di perangkat lokal Anda** dalam file `whenyhh.db` (SQLite).
- Tidak ada telemetri, analitik, atau data pengguna yang dikirim ke server pengembang.
- Jika Anda mengaktifkan penyedia cloud (Groq, OpenRouter, Gemini AI Studio, atau BYOM lainnya), konten aksi dan narasi akan dikirim ke server penyedia tersebut sesuai kebijakan privasi masing-masing. Anda bertanggung jawab atas kesesuaian data yang dikirimkan dengan ketentuan penyedia.
- Data pribadi nyata (nama warga, NIK, data keuangan, rekam medis) **tidak boleh** dimasukkan ke dalam skenario. Gunakan nama dan data fiktif.

---

## 2. Keamanan Kunci API (SE Menkominfo No. 9 Tahun 2023)

- Kunci API yang Anda masukkan pada dialog konfigurasi LLM **hanya disimpan di `sessionStorage` peramban** dan hilang otomatis saat tab atau jendela peramban ditutup.
- Kunci tidak pernah ditulis ke basis data SQLite, file log server, atau dikirim ke pihak ketiga selain penyedia LLM yang Anda pilih secara eksplisit.
- Header `X-LLM-API-Key` hanya melintas di memori proses server selama durasi satu request; tidak pernah dilog.
- Tim pengembang **tidak memiliki akses** ke kunci API Anda dalam kondisi apapun.

---

## 3. Konten Simulasi & Disclaimer

Whenyhh.ai menghasilkan konten naratif secara otomatis menggunakan model bahasa besar (LLM). Harap diperhatikan:

- **Konten bersifat fiksi.** Output LLM tidak mencerminkan pandangan, opini, atau rekomendasi tim pengembang maupun Universitas Indonesia.
- **Bukan sumber informasi profesional.** Konten tidak boleh digunakan sebagai pengganti nasihat hukum, medis, keuangan, atau psikologis.
- **Topik sensitif:** Jika simulasi menyentuh topik kesehatan jiwa, kekerasan, atau krisis, segera hubungi layanan profesional:
  - **Hotline Kesehatan Jiwa Kemenkes:** 119 ext. 8 (Healing119.id)
  - **Into The Light Indonesia:** 119 ext. 8
- **Verifikasi rekening:** Untuk melaporkan rekening terduga penipuan, gunakan **CekRekening.id** atau laporkan ke IASC OJK melalui ojk.go.id.
- **Hak cipta konten yang dihasilkan:** Konten yang dihasilkan LLM pada sesi Anda menjadi tanggung jawab Anda sepenuhnya.

---

## 4. Batasan Penggunaan yang Diizinkan

Aplikasi ini **diizinkan** digunakan untuk:

- Eksplorasi skenario kebijakan publik yang bersifat edukatif dan non-preskriptif.
- Penulisan kreatif, pengembangan karakter, dan fiksi interaktif.
- Penelitian simulasi keputusan (what-if analysis) untuk keperluan akademik.
- Demo dan presentasi proyek kelompok DDP1.

Aplikasi ini **dilarang** digunakan untuk:

- Membuat atau menyebarkan disinformasi, hoaks, atau konten yang bertujuan menipu.
- Melanggar hak privasi orang lain (memasukkan data pribadi nyata tanpa izin).
- Menghasilkan konten yang melanggar hukum Indonesia, termasuk UU ITE.
- Tujuan komersial tanpa izin tertulis dari tim pengembang.

---

## 5. Disclaimer Teknis

- Aplikasi ini merupakan **prototipe penelitian** (Proyek DDP1) dan belum melalui audit keamanan penuh.
- Tidak ada jaminan ketersediaan layanan, keakuratan konten LLM, atau ketahanan dari bug.
- **Simpan ekspor JSON/MD** secara berkala untuk backup skenario penting Anda; tim pengembang tidak bertanggung jawab atas kehilangan data akibat kegagalan sistem.

---

## 6. Persetujuan

Dengan mengklik **"Saya Setuju dan Lanjutkan"** pada layar awal aplikasi, Anda menyatakan telah membaca, memahami, dan menyetujui seluruh syarat dan ketentuan di atas.

---

*Whenyhh.ai — Proyek Kelompok DDP1 Fasilkom UI | 2026*
