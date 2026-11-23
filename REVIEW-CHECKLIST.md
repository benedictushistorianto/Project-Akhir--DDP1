# Review Checklist

Jangan tandai pekerjaan selesai sebelum pemeriksaan yang relevan lulus.

## Basic Checks

- [ ] Diff terfokus pada 1-3 berkas sesuai kepemilikan modul dan tugas yang diminta.
- [ ] Tidak ada berkas rekan tim yang tidak terkait ikut tertimpa atau diformat ulang.
- [ ] Tidak ada API key (Anthropic/BYOM), `.env`, berkas `*.db`, atau log privat yang masuk ke commit Git.
- [ ] Tidak ada perubahan pada `app/schemas.py` pasca Schema Freeze tanpa persetujuan tim dan pembaruan tes.
- [ ] `pytest -v` lulus 100% (tidak ada tes yang dilewati atau dilemahkan demi hasil hijau).
- [ ] Perubahan UI di `static/` sudah dicek di peramban (desktop 1080p dan responsif 768px) dengan 0 error di Console.
- [ ] Ringkasan cara kerja kode (3-5 baris Bahasa Indonesia sederhana) siap ditulis di deskripsi PR agar seluruh anggota memahami kode.
- [ ] Sudah cek `/cost` di Claude Code dan lakukan `/clear` sebelum berpindah ke fitur baru.

## Security & Privacy

- [ ] Server Uvicorn tetap terikat ke `127.0.0.1` (bukan `0.0.0.0`) dan tanpa `CORSMiddleware` wildcard.
- [ ] Seluruh masukan API tervalidasi Pydantic v2 dan nilai numerik ter-*clamp* di sisi Python.
- [ ] Seluruh narasi LLM dirender melalui `DOMPurify.sanitize(marked.parse(...))` sebelum masuk DOM.
- [ ] Header `X-LLM-API-Key` hanya disimpan di memori/`sessionStorage` peramban dan terverifikasi 0 baris di SQLite maupun log terminal.
- [ ] Modal Persetujuan Aktif T&C (UU PDP & SE Menkominfo 9/2023 + rujukan Healing119.id & IASC OJK) tetap memblokir input sesi pertama sebelum dicentang.

## UI / UX Anti-AI-Slop Checks (Saat Mengubah `static/`)

- [ ] Tidak ada aksen ungu/indigo, teks judul gradien, font Inter/Geist sebagai display, atau ikon emoji fungsional (hanya Lucide outline).
- [ ] Tidak ada em-dash, en-dash, atau middle-dot pada teks UI yang terlihat.
- [ ] `prefers-reduced-motion: reduce` aktif dan transisi <= 150ms hanya pada `transform`/`opacity`.
- [ ] Tersedia state *loading* (skeleton), *empty*, *error inline*, dan lencana kuning *Deterministic Safe Fallback*.
- [ ] Kontras teks minimal WCAG AA (4.5:1 teks isi, 3:1 elemen UI) dan status relasi tidak mengandalkan warna saja (disertai angka skor).

## AI Checks

- [ ] Paket konteks *Dynamic Context Compiler* terverifikasi <= 2.200 token input dan prefiks statis (`messages[0]`) identik *byte-for-byte*.
- [ ] Tidak ada potongan JSON delta atau *Heartbeat* masuk ke *sliding window* 2 giliran terakhir.
- [ ] Keluaran LLM diperlakukan sebagai data tidak tepercaya (dibersihkan dari `<think>`, diperbaiki `json-repair`, divalidasi Pydantic, dan `actor_id` fiktif diabaikan).
- [ ] Uji jalur langsung (JSON valid), isolasi cabang, kegagalan (JSON rusak / *timeout* -> *Deterministic Safe Fallback*), dan uji stres 100 giliran lulus di `pytest`.
- [ ] Peringatan privasi tampil eksplisit untuk penyedia BYOM gratis yang melatih dari prompt (misal tier gratis Gemini/Mistral).

## Final Evidence

Laporan akhir wajib memuat:

- Daftar berkas yang diubah
- Perintah yang benar-benar dijalankan
- Hasil `pytest` / build CSS / pemeriksaan peramban
- Ringkasan alur logika kode (3-5 baris Bahasa Indonesia untuk anggota tim)
- Risiko atau blocker tersisa
