# Product Requirements Document: Whenyhh.ai MVP

## Product Overview

**App Name:** Whenyhh.ai
**Tagline:** Workbench visualisasi skenario bercabang, simulasi keputusan what-if, dan roleplay interaktif berarsitektur memori O(1) yang bebas amnesia konteks.
**Launch Goal:** Meraih skor maksimal pada seluruh enam kriteria rubrik Proyek Kelompok DDP1 Fasilkom UI (Gasal 2026/2027) dan menembus rekomendasi Asisten Dosen ke babak final 9 kelas, dibuktikan dengan 100% lulus minimal 34 uji otomatis `pytest`, uji stres 100 giliran tetap pada plafon input <= 2.200 token, serta demo lokal offline 15 menit tanpa crash.
**Target Launch:** Kamis, 10 Desember 2026 pukul 23:59 WIB (submisi dini ditargetkan Rabu, 9 Desember 2026).

## Who It's For

### Primary User 1: Mahasiswa dan Masyarakat Umum (Persona: Raka, 19 tahun)
Mahasiswa tahun pertama atau warga umum yang ingin berlatih menghadapi situasi berisiko tinggi (seperti negosiasi dana kepanitiaan, wawancara/sidang, atau mengenali jebakan rekayasa sosial dan penipuan daring) dalam lingkungan aman tanpa konsekuensi nyata. Terbiasa memakai aplikasi web dan chatbot AI, tetapi tidak ingin melakukan konfigurasi teknis rumit.

**Their Current Pain:**
- Platform AI chat biasa melupakan fakta dan janji dari awal percakapan setelah belasan giliran ("amnesia konteks").
- Tidak bisa membandingkan dua keputusan berbeda ("bagaimana jika tadi saya menolak tawaran ini?") secara visual di satu layar.
- Platform roleplay populer membatasi memori gratis, memasang iklan agresif, atau mewajibkan langganan berbayar.

**What They Need:**
- Ruang simulasi keputusan bercabang berbahasa Indonesia yang berjalan gratis di komputer sendiri.
- Visualisasi jelas tentang bagaimana tiap ucapan mengubah kepercayaan (`Trust`) dan ketegangan (`Tension`) lawan bicara.
- Batasan keselamatan yang jelas (bukan pengganti psikolog/konsultan) disertai rujukan layanan resmi Indonesia jika sedang mengalami krisis nyata.

### Primary User 2: Pemangku Kebijakan dan Peneliti (Persona: Ibu Nadia, 36 tahun)
Analis kebijakan kampus, staf instansi pemerintah, atau peneliti sosial yang perlu memetakan potensi gesekan antar-pemangku kepentingan sebelum sebuah rancangan kebijakan diumumkan.

**Their Current Pain:**
- Sulit menguji skenario *what-if* lintas kelompok kepentingan secara cepat sebelum masuk tahap survei atau uji publik.
- Ragu mengunggah draf kebijakan internal ke layanan AI *cloud* publik karena risiko kebocoran data dan kepatuhan UU PDP.

**What They Need:**
- Mode eksekusi 100% lokal (offline) agar naskah draf kebijakan tidak pernah keluar dari perangkat.
- Peta relasi asimetris antar-aktor dan perbandingan visual antara opsi kebijakan Cabang A dan Cabang B, lengkap dengan pagar etika non-preskriptif (*human-in-the-loop*).

### Primary User 3: Novelis dan Kreator Digital (Persona: Dimas, 24 tahun)
Penulis fiksi interaktif, novelis, atau *game master* yang menguji dinamika karakter, konsistensi bukti plot, dan cabang alur cerita panjang (50 hingga 100+ adegan).

**Their Current Pain:**
- Menggunakan *prompt skill* berbasis chat biasa menghabiskan anggaran token secara kuadratik karena LLM terus menulis ulang *changelog* dan *Heartbeat* di tiap giliran.
- Sulit melacak percabangan alur alternatif tanpa merusak garis cerita utama atau mencampur fakta dari cabang yang berbeda.

**What They Need:**
- Mesin percabangan bergaya Git (*click-to-fork* dan *checkout*) yang mengisolasi fakta penting (*Jangkar Kausal*) per cabang.
- Konsistensi karakter jangka panjang (*Core* tidak berubah, *State* berevolusi) dan ekspor naskah lokal ke JSON atau Markdown.

### Example User Story
"Meet Raka, seorang bendahara panitia kampus yang sedang menghadapi tekanan vendor dan tawaran dana talangan mencurigakan. Di chatbot AI biasa, simulasi latihan negosiasinya cepat melupakan syarat awal dan sulit diulang dari titik kritis. Dengan Whenyhh.ai, ia menjalankan skenario di komputer lokal, melihat grafik kepercayaan dua arah dengan ketua panitia dan vendor berubah tiap giliran, lalu mengklik simpul S03 di pohon Git-DAG untuk membuat cabang alternatif dan membandingkan hasil akhir kedua keputusannya."

## The Problem We're Solving

Simulasi skenario bercabang dan *roleplay* berbasis obrolan AI konvensional (termasuk pendekatan *chat-skill* seperti `scenario-and-roleplay-v1-5-id`) memaksa LLM merangkap sebagai penulis narasi sekaligus basis data memori. Karena riwayat obrolan bersifat menumpuk, setiap perubahan status atau cabang memicu penulisan ulang *changelog* (*Heartbeat* dan daftar cabang) yang menyebabkan konsumsi token tumbuh secara kuadratik `O(N^2)`. Setelah melewati 50 giliran, jendela konteks meluap, biaya token membengkak, dan model lokal kelas 8GB VRAM melambat drastis atau melupakan kejadian awal.

Whenyhh.ai menyelesaikan masalah ini secara arsitektural dengan memindahkan seluruh status dunia, karakter, relasi asimetris, *Jangkar Kausal*, dan pohon cabang Git-DAG ke **Externalized State Engine** berbasis Python + SQLite. LLM hanya bertugas menulis prosa adegan dan mengembalikan delta JSON ringkas, sehingga input per giliran terkunci pada plafon konstan `O(1)` (<= 2.200 token) dan memproyeksikan penghematan token kumulatif hingga 91,1% pada 100 giliran.

**Why Existing Solutions Fall Short:**
- **Character.AI:** Memori jangka panjang dipagar biaya langganan, tidak ada peta percabangan visual atau metrik relasi terstruktur, dan seluruh data berjalan di server tertutup.
- **AI Dungeon & NovelAI:** Kapasitas konteks besar berbayar bulanan dan antarmukanya bersifat linier, bukan perbandingan skenario bercabang multi-aktor.
- **SillyTavern:** Kurva konfigurasi teknis tinggi bagi pengguna umum, tidak punya kanvas Git-DAG bawaan, dan ekstensi RAG vektornya memecah *KV prefix cache*.
- **Twine & Ink:** 100% statis pra-tulis sehingga tidak bisa merespons input keputusan bebas secara dinamis.

## User Journey

### Discovery -> First Use -> Success

1. **Discovery Phase**
   - **How they find us:** Repositori GitHub publik, video demonstrasi YouTube (DDP1 Fasilkom UI), atau dibagikan di komunitas mahasiswa dan kreator.
   - **What catches their attention:** Peta cabang bergaya Git client yang bisa diklik langsung, bukti penghematan token O(1), dan kemampuan jalan gratis secara lokal di GPU 8GB VRAM maupun API gratis.
   - **Decision trigger:** Instalasi lokal cepat tanpa akun, tanpa kartu kredit, dan langsung memiliki 3 skenario bawaan berbahasa Indonesia.

2. **Onboarding (First 5 Minutes)**
   - **Land on:** `http://127.0.0.1:8000` menampilkan modal **Persetujuan Aktif (T&C dan Pemberitahuan Fiksi/Non-Preskriptif)** satu kali pada sesi pertama.
   - **First action:** Pengguna mencentang persetujuan, memilih salah satu dari 3 skenario bawaan (Mahasiswa/Anti-Scam, Kebijakan Kampus, atau Misteri Kreator), dan memeriksa status koneksi model lokal (Ollama) atau preset BYOM gratis di bilah atas.
   - **Quick win:** Dalam kurang dari 2 menit, pengguna menjalankan 2 giliran pertama dan langsung melihat simpul baru muncul di jalur Git-DAG beserta pergeseran panah relasi asimetris di panel kanan.

3. **Core Usage Loop**
   - **Trigger:** Pengguna ingin menguji konsekuensi pilihan berbeda terhadap dinamika relasi dan *Ticking Clock* skenario.
   - **Action:** Memasukkan aksi bebas atau memilih salah satu dari 3 saran aksi bercabang, atau mengklik simpul masa lalu di kanvas Git-DAG untuk melakukan *Checkout* atau *Fork Cabang Baru*.
   - **Reward:** Narasi Bahasa Indonesia alami muncul cepat tanpa menunggu penulisan ulang *changelog*, panah relasi `A -> B` dan `B -> A` berubah secara independen, dan inspektor token menunjukkan biaya input tetap datar <= 2.200 token.
   - **Investment:** Tersimpannya pohon cabang, *Jangkar Kausal* terisolasi, dan kemampuan mengekspor hasil ke JSON/Markdown lokal.

4. **Success Moment**
   - **"Aha!" moment:** Saat pengguna melakukan *click-to-fork* di simpul S03, mengambil keputusan berlawanan di Cabang B, lalu membandingkan langsung grafik tren `Trust`/`Tension` dan fakta kausal Cabang A vs Cabang B tanpa satu pun fakta awal yang terlupakan.
   - **Share trigger:** Menunjukkan grafik perbandingan token O(1) vs O(N^2) dan mengekspor ringkasan skenario ke Markdown.

## MVP Features

### Must Have for Launch

#### 1. Externalized State Engine dan Git-DAG Imutabel
- **What:** Mesin status berbasis Python + SQLite yang menyimpan identitas karakter permanen (`Core`) terpisah dari kondisi dinamis (`State`: *Needs* 1-5, *Mood* 1-3, lokasi, *Ticking Clocks*), graf relasi berarah asimetris (`Trust` -5..+5, `Affinity` -5..+5, `Tension` 0..5), serta *Jangkar Kausal* yang terisolasi per garis keturunan cabang (*Recursive CTE*). Setiap giliran disimpan sebagai simpul imutabel sehingga *checkout* dan *fork* tidak pernah menimpa sejarah lama.
- **User Story:** As a pengguna simulasi, I want to mengklik simpul giliran masa lalu untuk membuat cabang skenario baru tanpa merusak alur lama so that saya dapat membandingkan konsekuensi dua keputusan berbeda secara akurat.
- **Success Criteria:**
  - [ ] Mengirim aksi pada simpul aktif `S(n)` -> sistem membuat simpul baru `S(n+1)` dengan `parent_id = S(n)` dan merender simpul baru di kanvas Git-DAG dalam <= 500ms setelah respons LLM diterima.
  - [ ] Mengklik simpul lama `S02` lalu memilih "Fork Cabang Baru" -> sistem menciptakan `branch_id` baru yang menunjuk `parent_id = S02`, sementara seluruh simpul `S03..S(n)` di cabang asal tetap utuh 100%.
  - [ ] Perubahan `Trust` pada arah `A -> B` tidak mengubah nilai `B -> A`, dan seluruh nilai delta otomatis dipangkas (*clamped*) ke batas valid (`mood` 1..3, `needs` 1..5, `trust`/`affinity` -5..+5, `tension` 0..5).
  - [ ] *Jangkar Kausal* yang lahir di Cabang A tidak pernah muncul pada daftar jangkar atau prompt konteks saat pengguna aktif di Cabang B.
- **Priority:** P0 (Critical)

#### 2. Dynamic Context Compiler O(1) dan Panel Telemetri Token
- **What:** Pengompilasi konteks deterministik di Python yang merakit prompt berplafon tetap <= 2.200 token input per giliran (Zona Prefiks Statis ~700 token ramah *KV prefix cache* + Zona Sufiks Dinamis <= 1.500 token berisi state terkini, relasi aktif, *Sim Pulse* ber-seed, maks 10 jangkar kausal, ringkasan arc, dan 2 giliran narasi bersih tanpa JSON/Heartbeat). Dilengkapi panel telemetri Plotly yang membandingkan pemakaian token aktual terhadap kurva *chat-skill* tradisional.
- **User Story:** As a novelis atau penguji skenario panjang, I want to menjalankan puluhan hingga seratus giliran tanpa lonjakan token dan tanpa amnesia konteks so that simulasi tetap cepat dan stabil di GPU 8GB VRAM.
- **Success Criteria:**
  - [ ] Pada uji stres otomatis 100 giliran (`pytest` dengan `MockLLMAdapter`), estimasi token input pada S10, S50, dan S100 selalu <= 2.200 token.
  - [ ] Blok prefiks statis (`messages[0]`) identik *byte-for-byte* antar-giliran pada skenario yang sama agar *KV prefix cache* tidak batal.
  - [ ] Tidak ada potongan JSON delta atau blok *Heartbeat* yang masuk kembali ke *sliding window* dua giliran terakhir.
  - [ ] Tab Telemetri Token menampilkan grafik garis interaktif (*Plotly-basic*) yang memuat data token per giliran sepanjang garis keturunan aktif beserta garis perbandingan model *chat-skill* O(N^2).
- **Priority:** P0 (Critical)

#### 3. Gerbang LLM Lokal 8GB VRAM, BYOM Rp0, dan Ketahanan JSON 4 Lapis
- **What:** Klien tunggal OpenAI-compatible untuk menjalankan LLM lokal via **Ollama** (default, dengan `OLLAMA_KV_CACHE_TYPE=q8_0` dan sakelar non-thinking untuk Qwen3/Qwen3.5), **LM Studio** (opsional lokal), preset **BYOM Cloud Gratis** (Groq, Gemini AI Studio, OpenRouter `:free`), serta **Mock Mode** offline. Dilindungi pipa ketahanan 4 lapis: *constrained decoding* JSON schema -> pembersih tag `<think>` + `json-repair` -> validasi Pydantic v2 -> maksimal 1x *self-healing retry* menuju *Deterministic Safe Fallback*.
- **User Story:** As a mahasiswa dengan GPU 8GB atau rekan tim tanpa GPU, I want to mengganti model lokal atau API gratis langsung dari antarmuka web tanpa aplikasi crash ketika format keluaran model cacat so that semua orang bisa menguji dan mendemokan aplikasi secara gratis.
- **Success Criteria:**
  - [ ] Pengguna dapat memilih preset Ollama, LM Studio, Groq, Gemini, OpenRouter, atau Mock dari modal Pengaturan Model dan menjalankan tombol "Uji Koneksi" yang mengembalikan status valid beserta latensi (ms).
  - [ ] Kunci API BYOM hanya tersimpan di `sessionStorage` peramban, dikirim via header `X-LLM-API-Key`, dan terverifikasi 0 baris tersimpan di seluruh tabel SQLite maupun log server.
  - [ ] Ketika model memancarkan JSON berbungkus `<think>...</think>`, koma berlebih, atau kurung tak tertutup, pipa `json-repair` memulihkannya tanpa *retry* tambahan.
  - [ ] Ketika model gagal dua kali berturut-turut atau mengalami *timeout*, sistem tetap mengembalikan HTTP 200 dengan *Deterministic Safe Fallback* (status lama dipertahankan + lencana peringatan kuning di UI), bukan HTTP 500.
- **Priority:** P0 (Critical)

#### 4. Antarmuka Cockpit 3-Pane, 3 Skenario Bawaan, FAQ, T&C, dan Ekspor Lokal
- **What:** Antarmuka web responsif bergaya *developer cockpit* 3-panel (terinspirasi jalur *swimlane* cabang Git client seperti GitKraken) yang menyatukan daftar cabang & jangkar (kiri), kanvas Git-DAG + arena narasi (tengah), serta inspektor relasi asimetris *bezier*, status karakter, dan telemetri (kanan). Mencakup 3 skenario *seed* siap pakai (Mahasiswa/Anti-Scam, Kebijakan Parkir Kampus, Misteri Pelabuhan 1928), halaman `/faq`, modal persetujuan aktif T&C Indonesia (UU PDP, SE Menkominfo 9/2023, rujukan Healing119.id & IASC OJK), serta ekspor lokal JSON dan Markdown.
- **User Story:** As a pengguna dari tiga segmen berbeda, I want to langsung mencoba skenario relevan, memahami batasan etika AI, dan mengekspor hasil cabang skenario saya so that saya mendapatkan manfaat nyata sekaligus aman secara etika dan privasi.
- **Success Criteria:**
  - [ ] Pada kunjungan pertama, modal T&C memblokir input simulasi sampai pengguna mencentang kotak persetujuan aktif dan mengklik tombol setuju.
  - [ ] Ketiga skenario bawaan dapat dimuat dari daftar awal tanpa galat kunci asing dan seluruh narasi dirender melalui `DOMPurify.sanitize(marked.parse(...))` tanpa celah XSS.
  - [ ] Panel Relasi Asimetris merender panah dua arah terpisah (`curve-style: bezier`) untuk pasangan aktor yang sama dengan pewarnaan jelas sesuai skor `Trust`/`Tension`.
  - [ ] Pengguna dapat mengunduh berkas ekspor JSON (struktur lengkap DAG + state + jangkar) dan Markdown bersih (transkrip narasi cabang aktif) secara lokal.
- **Priority:** P0 (Critical)

### Nice to Have (If Time Allows)
- **Komparator Side-by-Side Cabang (`/diff` modal):** Tabel perbandingan berdampingan antara dua simpul/cabang yang menyoroti selisih skor relasi dan *Jangkar Kausal* yang berbeda.
- **Editor Skenario Kustom Sederhana:** Formulir ringkas di UI untuk membuat skenario baru (premis + 2-3 aktor *Core*) selain 3 skenario bawaan.
- **Impor JSON Skenario:** Memuat kembali berkas ekspor JSON hasil unduhan ke sesi baru.

## Out of Scope (Not in MVP)
- **Login, Akun Multi-User, dan Cloud Hosting:** Ditunda ke v2; MVP dirancang 100% lokal (`127.0.0.1:8000`) agar menjaga privasi data, menekan biaya ke Rp0, dan menghindari beban autentikasi yang tidak diminta rubrik.
- **Merge Dua Cabang Kompleks dan Resolusi Konflik Otomatis:** Ditunda ke v2; percabangan MVP berfokus pada *commit*, *checkout*, *fork*, dan perbandingan cabang tanpa algoritma *three-way merge* naratif.
- **Audio/TTS, Speech-to-Text, dan Generator Gambar Karakter:** Ditunda ke v2 agar tidak menghabiskan kuota VRAM 8GB yang diprioritaskan untuk LLM dan rekaman OBS.
- **Perintah Git Lanjutan (`rebase`, `bisect`, `cherry-pick`, `stash`):** Ditunda ke v2 agar basis kode tetap ringkas, stabil, dan dipahami penuh oleh seluruh anggota tim DDP1.
- **Sistem Pembayaran dan Langganan:** Not applicable untuk proyek akademik *open-source* lisensi MIT.

*Why we're waiting: Menjaga MVP tetap fokus, stabil, bebas bug saat demo offline, dan tuntas sebelum batas 10 Desember 2026.*

## How We'll Know It's Working

### Launch Success Metrics (Deadline 10 Desember 2026)
| Metric | Target | Measure |
|--------|--------|---------|
| Kelulusan Uji Otomatis (`pytest`) | 100% lulus (>= 34 uji di 6 suite) | Output terminal `pytest -v` dan status hijau GitHub Actions CI |
| Efisiensi Token Input O(1) | <= 2.200 token input hingga giliran S100 | Uji stres otomatis `test_context_compiler_o1.py` |
| Kestabilan Demo Offline 15 Menit | 0 crash (0 HTTP 500) selama demo lokal OBS 1080p | Gladi resik offline (Wi-Fi mati) + rekaman final YouTube |
| Keseimbangan Kontribusi Tim | 100% anggota memiliki PR ter-merge & riwayat commit aktif | Grafik kontributor dan riwayat commit repositori GitHub publik |
| Disiplin Biaya Vibe-Coding | Total pemakaian Claude API <= $95 USD dari plafon $100 USD | Pantauan `/cost` harian dan hard cap Anthropic Console |
| Target Kompetisi DDP1 | Rekomendasi Asdos ke babak final 9 kelas | Penilaian rubrik 6 kriteria DDP1 Fasilkom UI |

### Growth Metrics (Pasca-Rilis / Evaluasi Lanjutan)
| Metric | Target | Measure |
|--------|--------|---------|
| Adopsi Uji Coba Teman/Asdos | >= 5 penguji mencoba minimal 1 skenario bercabang | Catatan uji pengguna manual & isu GitHub |
| Ketahanan Lintas Model BYOM | Berhasil berjalan pada >= 3 model berbeda (Ollama 7B/8B, 4B, dan Groq) | Checklist pengujian matriks model di dokumentasi |

## Look & Feel

**Design Read (`craftwork-design`):**
`Reading this as: high-density interactive branching scenario and Git-DAG workbench for students, policy explorers, and creators, in a Data / dashboard (developer cockpit) language, with GitKraken-inspired multi-lane DAG swimlanes, asymmetric relation graphs, and monochrome outline icons.`

**Design Vibe:** Padat, presisi, analitis, gelap-netral, imersif.

**Design Dials (1-10):**
- **Variance: 3** (struktur 3-panel kerja yang konsisten dan terprediksi dengan proporsi tak simetris: 230px kiri, fleksibel tengah, 340px kanan).
- **Motion: 2** (transisi fungsional <= 150ms hanya pada `transform` dan `opacity`; wajib menghormati `prefers-reduced-motion: reduce`; tanpa animasi melayang atau *scale-up* kartu).
- **Density: 8** (*cockpit* berinformasi padat bergaya GitKraken: pemisah garis tipis `1px` hairline, minim kotak kartu bertumpuk, seluruh angka metrik dan ID simpul menggunakan font *tabular mono*).

**Visual Principles & Anti-AI-Slop Guardrails (`anti-ai-slop-uiux`):**
1. **Color (60-30-10, bebas ungu/indigo & bebas `#000` murni):** Permukaan dasar *charcoal* netral (`#14161A` kanvas utama, `#1B1E24` panel, `#232730` elemen aktif), garis pemisah `#2E333E`, teks utama `#E6E8EC` dan sekunder `#9AA3B2` (lolos kontras WCAG AA >= 4.5:1), serta **satu aksen primer non-ungu** (*Teal* `#1F9D8B` untuk aksi utama). Warna jalur *swimlane* cabang di DAG memakai palet fungsional kontras tinggi tanpa gradien neon atau efek *glow* (`#2DD4BF` cabang utama, `#38BDF8` cabang 2, `#F59E0B` cabang 3, `#FB7185` cabang 4).
2. **Typography (bebas Inter/Geist & bebas judul gradien):** **IBM Plex Sans** (atau **Plus Jakarta Sans**) untuk antarmuka dan prosa narasi (`max-w-prose` / ~65 karakter per baris untuk kenyamanan baca) dipadukan dengan **JetBrains Mono** untuk ID simpul (`S01`, `S12`), skor relasi, dan angka telemetri token. Maksimal 3 bobot huruf (`400`, `500`, `700`).
3. **Icons, Radius & Microcopy:** Satu paket ikon tunggal (**Lucide Icons** *outline* 16-20px, `currentColor`, **0 emoji fungsional**). Skala sudut (*radius*) terukur: `4px` badge/input, `6px` tombol, `8px` panel/modal (tanpa `rounded-2xl` seragam atau tombol pil gradien). Teks UI konkret dan lugas (misal "Fork dari S03", "Jalankan Giliran", "Uji Koneksi"), tanpa kata *hype*, tanpa em-dash/en-dash, dan tanpa *middle-dot* pada label antarmuka.
4. **Complete UI States:** Wajib memiliki *skeleton loading* saat LLM memproses giliran, *empty state* terarah saat skenario belum dipilih, pesan galat *inline* di bawah input, lencana kuning non-destruktif untuk *Deterministic Safe Fallback*, serta fokus papan ketik yang jelas.

**Key Screens/Pages:**
1. **Workbench Utama (`/`):** Layar *cockpit* 3-panel (Navigator Cabang & Jangkar di kiri, Pohon Git-DAG Swimlanes + Arena Narasi di tengah, Inspektor Relasi/State/Token di kanan).
2. **Modal Persetujuan T&C (First-Visit Gate):** Ringkasan 7 poin ketentuan penggunaan, batasan AI non-preskriptif, dan kotak centang persetujuan aktif.
3. **Modal Pengaturan Model (BYOM & Lokal):** Pemilih preset Ollama, LM Studio, Groq, Gemini, OpenRouter, atau Mock, input kunci *ephemeral*, dan tombol Uji Koneksi.
4. **Halaman FAQ & Etika (`/faq` atau Modal Penuh):** Jawaban terstruktur untuk 3 segmen pengguna beserta tautan resmi Healing119.id, CekRekening.id, dan IASC OJK.

### Simple Wireframe (Desktop >= 1024px; pada layar < 768px Pane Kiri & Kanan melipat ke Tab Drawer)
```text
+---------------------------------------------------------------------------------------------------+
| Whenyhh.ai | Skenario: [Kebijakan Parkir Kampus v] | Model: [Ollama: qwen2.5:7b] | [FAQ] [Ekspor] |
+---------------------+-----------------------------------------------+-----------------------------+
| PANE KIRI (230px)   | PANE TENGAH (Fleksibel ~50%)                  | PANE KANAN (340px)          |
|                     |                                               |                             |
| CABANG LOKAL        | [ATAS: KANVAS GIT-DAG SWIMLANES (Cytoscape)]  | [Relasi] [State] [Token]    |
| > main      (S04)   |   Cabang     Graf       Ringkasan Giliran     |                             |
|   opsi-b    (S03b)* |   main       (*)------- S01: Rapat awal       |  -- Graf Relasi Asimetris   |
|                     |                |                              |     [Komuter]               |
| [+ Fork dari HEAD]  |               (*)------ S02: Usul tarif       |      /    ^                 |
|                     |              /   \                            |  +2 /      \ -3             |
| ------------------- |   opsi-b   (*)   (*)--- S03: Tolak subsidi    |    v        \               |
| JANGKAR KAUSAL (3)  |             |     |                           |  [Keamanan]--[Kantin]       |
| [S01] Tenggat 5 mgg |   HEAD ->  (*)   (*)--- S04: Protes komuter   |    (panah bezier terpisah)  |
| [S02] Dana subsidi  |   *Klik node: Checkout / Fork dari simpul ini |                             |
|       terbatas      | --------------------------------------------- | --------------------------- |
|                     | [BAWAH: ARENA NARASI & INPUT AKSI]            | RINGKASAN STATE AKTOR       |
|                     | [S03b - opsi-b]                               | Komuter  | Mood: 2/3        |
|                     | Perwakilan mahasiswa komuter menurunkan       | Energi 3 | Aman 4 | Sos 3   |
|                     | suaranya saat melihat skema transisi...       |                             |
|                     |                                               | --------------------------- |
|                     | Opsi Lanjutan:                                | TELEMETRI O(1)              |
|                     | [1] Tawarkan uji coba 2 pekan                 | Input: 1.480 / 2.200 tok    |
|                     | [2] Minta kantin ikut menanggung biaya        | Status: Prefiks Cache Aktif |
|                     | [3] Tunda keputusan hingga survei kampus      |                             |
|                     | [Ketik aksi bebas Anda...]  [Jalankan Giliran]|                             |
+---------------------+-----------------------------------------------+-----------------------------+
```

## Technical Considerations

- **Platform:** Web lokal *Single-Origin* (`http://127.0.0.1:8000`) berbasis Python (FastAPI + Uvicorn + SQLite) dan HTML/JS ringan *zero-build*.
- **Responsive:** Dioptimalkan untuk layar desktop 1080p (target utama demo OBS & penggunaan *cockpit*), tetap dapat diakses pada layar `< 768px` dengan pelipatan pane kiri/kanan ke tombol laci (*drawer*).
- **Performance:** Muat halaman awal < 2 detik secara offline; kompilasi konteks & transaksi SQLite < 50ms per giliran; kecepatan inferensi lokal >= 25 token/detik pada GPU 8GB VRAM dengan model 7B/8B `Q4_K_M` dan *KV cache* `q8_0`.
- **Accessibility:** Kontras teks minimal WCAG 2.1 AA (4.5:1 teks isi, 3:1 elemen UI), navigasi fokus jelas, tidak bergantung pada warna semata untuk status relasi (disertai angka `+2`/`-3`), serta dukungan penuh `prefers-reduced-motion`.
- **Security/Privacy:** Server mengikat hanya ke `127.0.0.1` (bukan `0.0.0.0`); kunci API BYOM bersifat *ephemeral* di `sessionStorage` dan header `X-LLM-API-Key`; sanitasi wajib `DOMPurify` pada seluruh keluaran Markdown LLM; kepatuhan prinsip UU PDP No. 27/2022 & SE Menkominfo No. 9/2023.
- **Accounts, Payments & Cloud Hosting:** Not applicable for MVP (aplikasi lokal pengguna tunggal berlisensi MIT).

## AI / Automation Scope

- **Product AI:** In-app AI sebagai generator prosa adegan Bahasa Indonesia dan pemancar perubahan status terstruktur (`TurnResponse` JSON delta).
- **User Outcome:** Menghasilkan kelanjutan skenario realistis yang konsisten secara kausal terhadap aksi pengguna dan kondisi psikologis/relasi seluruh aktor, sambil menjaga beban token datar O(1).
- **Data Access:** AI hanya boleh membaca paket konteks yang dirakit *Dynamic Context Compiler* (aturan inti, `actor_cores`, `actor_states`, `relation_edges`, *Sim Pulse*, maks 10 *Jangkar Kausal* garis keturunan aktif, ringkasan arc, dan 2 giliran narasi bersih terakhir). AI **tidak memiliki akses langsung** menulis ke SQLite, membaca berkas sistem, atau mengakses kunci API.
- **Provider / Retention:** Default 100% lokal via Ollama atau LM Studio (0 transmisi data keluar perangkat). Mode opsional BYOM gratis (Groq, Gemini AI Studio, OpenRouter, NVIDIA NIM, Cloudflare, Mistral) menampilkan lencana privasi eksplisit; penyedia seperti tier gratis Gemini dan Mistral menyatakan konten dapat digunakan untuk pelatihan model sehingga UI melarang pengguna memasukkan data pribadi nyata pada mode tersebut.
- **Output Contract:** Objek JSON datar tervalidasi Pydantic v2 (`TurnResponse`: `narrative`, `actor_deltas`, `relation_deltas`, `new_anchor`, `updated_arc_summary`, `suggested_choices`) tanpa `additionalProperties`, dengan *clamping* numerik di sisi Python.
- **Human Confirmation:** Persetujuan aktif modal T&C sebelum sesi pertama dimulai; konfirmasi eksplisit pengguna sebelum mengaktifkan pengiriman data ke penyedia BYOM *cloud* pihak ketiga; *human-in-the-loop* penuh untuk setiap interpretasi skenario kebijakan.
- **Evaluation:** Enam suite `pytest` deterministik (>= 34 uji) yang mencakup kasus langsung (JSON valid), tidak langsung (relasi asimetris & isolasi cabang), negatif (input/ID fiktif, halusinasi `actor_id`, nilai luar rentang), kegagalan (tag `<think>`, JSON rusak, *timeout* menuju *fallback*), kebocoran kredensial (kunci API 0 baris di DB), dan uji trajektori 100 giliran O(1).
- **Telemetry / Cost:** Log token per giliran disimpan lokal di SQLite (tanpa pernah mencatat `X-LLM-API-Key`); anggaran runtime Rp0 (lokal gratis + BYOM *free tier*); kegagalan API otomatis jatuh ke *Deterministic Safe Fallback*.

## Quality Standards

**What This App Will NOT Accept:**
- Teks placeholder ("Lorem ipsum", nama generik fiktif tak kontekstual, atau tombol mati yang tidak melakukan apa pun).
- Pola *AI slop* UI (gradien ungu/indigo, font Inter seragam, ikon emoji fungsional, kartu 3-kolom identik, atau ketiadaan `prefers-reduced-motion`).
- Kegagalan HTTP 500 tak tertangani saat model lokal mengeluarkan JSON rusak atau server LLM mati.
- Kebocoran API key, file `.env`, atau file `.db` mentah ke repositori GitHub publik.
- Kode yang dihasilkan AI namun tidak dipahami oleh anggota kelompok yang mempresentasikannya.

*These standards will be enforced by the AI coding assistant via `CLAUDE.md` / `AGENTS.md` and GitHub Actions CI.*

## Budget & Constraints

- **Product & Operating Budget:** Rp0 untuk seluruh tumpukan teknologi, basis data, pustaka, dan runtime LLM aplikasi (100% lokal gratis + opsi BYOM *free tier*).
- **Vibe-Coding Development Budget:** **$100 USD** kredit **Claude API (pay-as-you-go)** untuk 17 hari pengerjaan aktif (hard cap Console di $95 USD; soft cap ~$4-$5/hari; $20-$25 cadangan Fase 3-4), dibantu Gemini & LM Studio lokal untuk tugas konten/prose non-kritis.
- **Timeline:** 17 hari pengerjaan aktif (23 Nov - 9 Des 2026) + 1 hari penyangga darurat sebelum batas Kamis, 10 Desember 2026 pukul 23:59 WIB.
- **Team:** 3-4 mahasiswa DDP1 Fasilkom UI (jumlah pasti anggota dikonfirmasi pada *Open Questions*).
- **Hardware Constraint:** GPU 8GB VRAM untuk inferensi lokal + OBS Studio 1080p secara simultan (plafon aman VRAM model ~6,0-6,2 GB), serta kompatibilitas bagi laptop rekan tim dan Asdos tanpa GPU diskret lewat BYOM gratis dan `MockLLMAdapter`.

## Open Questions & Assumptions

- **Open Question 1 (TBD):** Apakah komposisi final tim berjumlah 3 mahasiswa atau 4 mahasiswa? (Memengaruhi pembagian modul Jalur 3 dan Jalur 4, tanpa mengubah fitur P0).
- **Open Question 2 (TBD):** Apakah seluruh rekan tim memiliki akun GitHub dan lebih nyaman memakai **GitHub Desktop** dibanding CLI Git untuk alur PR harian?
- **Assumption 1:** Estimasi penghematan token 91,1% pada 100 giliran berasal dari model simulasi parametrik berbahasa Indonesia (~1,35 token/kata) dan akan diverifikasi ulang menggunakan penghitung token aktual di `test_context_compiler_o1.py`.
- **Assumption 2:** Batas kuota dan kebijakan retensi penyedia BYOM gratis (Groq, Gemini, OpenRouter) mengacu pada status Oktober-November 2026 dan dapat berubah sewaktu-waktu oleh masing-masing penyedia.

## Launch Strategy (Brief)

- **Soft Launch:** Gladi resik internal tim dengan Wi-Fi dimatikan total pada Hari ke-13 (Sabtu, 5 Desember 2026) untuk memverifikasi mode offline penuh dan 100% kelulusan `pytest`.
- **Target Users:** Asisten Dosen pembimbing, Dosen kelas DDP1, dan rekan mahasiswa Fasilkom UI (5-10 penguji awal dari kelas).
- **Feedback Plan:** Uji coba silang antar-anggota di sistem operasi berbeda (Windows/macOS) pada Hari ke-14 (*Bug Bash*) dan konsultasi progres rutin bersama Asdos pembimbing.
- **Iteration Cycle:** Siklus harian berbasis *Feature Branch* + PR terukur hingga *Feature Freeze* keras pada Minggu, 6 Desember 2026; tanggal 7-9 Desember fokus pada dokumentasi, produksi video YouTube <= 15 menit, dan submisi dini.

## Definition of Done for MVP

The MVP is ready to launch when:
- [ ] Seluruh 4 kelompok fitur P0 berfungsi penuh secara *end-to-end* di `http://127.0.0.1:8000`.
- [ ] Pipa ketahanan JSON 4 lapis dan *Deterministic Safe Fallback* mencegah error HTTP 500 pada seluruh skenario kegagalan LLM.
- [ ] Seluruh 6 suite `pytest` (>= 34 uji, termasuk uji stres 100 giliran <= 2.200 token dan verifikasi nol kebocoran API key) lulus 100% di lokal maupun GitHub Actions CI.
- [ ] Aplikasi berjalan 100% offline dengan Wi-Fi mati menggunakan aset lokal `static/vendor/`, `app.css` terkompilasi, dan Ollama lokal (`qwen2.5:7b` / `qwen3:8b`).
- [ ] Audit Pre-Delivery Anti-AI-Slop & aksesibilitas WCAG AA + `prefers-reduced-motion` lulus tanpa pelanggaran P0/HIGH.
- [ ] Seluruh anggota kelompok telah berkontribusi aktif di riwayat commit GitHub publik dan siap menjelaskan modul masing-masing pada video demonstrasi YouTube <= 15 menit.
- [ ] Tautan repositori GitHub publik dan tautan video YouTube terverifikasi dapat dibuka melalui jendela *Incognito* sebelum 10 Desember 2026 pukul 23:59 WIB.

## Next Steps

1. Tinjau dan sahkan PRD ini bersama kelompok serta Asisten Dosen pembimbing.
2. Ikuti Dokumen Desain Teknis (`docs/TechDesign-Whenyhh-ai-MVP.md` - Part 3) dan aturan agen (`AGENTS.md`, `CLAUDE.md`, `agent_docs/claude_api_budget.md`).
3. Mulai Phase 1 (Hari 1-4) dengan fokus mengunci `app/schemas.py` pada Hari ke-2.

---
*Document created: 2026-11-23*
*Status: Approved Draft — Ready for Implementation*

---
## Handoff Context
<!-- Machine-readable summary for the next workflow step. Do not delete; the next prompt in the workflow reads this block. -->
- Stage: prd
- App name: Whenyhh.ai
- User level: A (A = vibe coder, B = developer, C = in-between)
- Target platform: Web lokal Single-Origin (127.0.0.1:8000) berbasis Python FastAPI + HTML/JS ringan
- Budget: Rp0 untuk runtime/stack produk + $100 USD Claude API (pay-as-you-go) untuk vibe-coding pengembangan (hard cap $95 USD)
- Timeline: 17 hari kerja aktif + 1 hari buffer (23 Nov - 10 Des 2026 pukul 23:59 WIB)
- AI in product scope: yes
- Research status: Completed (Deep Research report verified with parametric O(1) simulation, 8GB VRAM benchmarks, Indonesian legal/ethical guidelines, and free BYOM tier analysis)
- Constraints: Komponen utama wajib Python (aturan DDP1); VRAM GPU 8GB berbagi dengan OBS Studio 1080p (batas aman model ~6,0-6,2 GB); 100% offline-capable; zero-build frontend tanpa Node.js wajib; kepatuhan UU PDP No. 27/2022 & SE Menkominfo No. 9/2023; seluruh anggota wajib aktif commit GitHub dan paham isi kode; desain UI anti-AI-slop bergaya cockpit GitKraken; disiplin anggaran $100 USD Claude API
- Decisions: Externalized State Engine (SQLite WAL + STRICT + Recursive CTE); pemisahan Core vs State; graf relasi berarah asimetris; Dynamic Context Compiler plafon O(1) <= 2.200 token; Ollama lokal default + LM Studio + BYOM cloud gratis (kunci ephemeral sessionStorage) + MockLLMAdapter; 4-layer JSON resilience pipeline; 3 seed scenarios (Mahasiswa/Anti-Scam, Kebijakan Kampus, Kreator); halaman FAQ & modal T&C persetujuan aktif; tanpa auth/payments/merge kompleks di MVP
- Open questions: Jumlah pasti anggota kelompok (3 atau 4 orang); preferensi alat Git harian anggota (GitHub Desktop vs CLI)
- Source files: research-Whenyhh-ai.md -> docs/PRD-Whenyhh-ai-MVP.md
---

```json
{
  "schemaVersion": 1,
  "documentType": "prd",
  "appName": "Whenyhh.ai",
  "oneLiner": "Aplikasi web lokal visualisasi skenario bercabang, simulasi keputusan what-if, dan roleplay interaktif berbasis Externalized State Engine O(1) bebas amnesia konteks.",
  "targetUsers": "Mahasiswa dan masyarakat umum, pemangku kebijakan/peneliti (simulasi eksploratif non-preskriptif), serta novelis dan kreator digital.",
  "phase": "Foundation",
  "mustHave": [
    "Externalized State Engine (Core vs State, Relasi Asimetris, Jangkar Kausal) dan Git-DAG Imutabel dengan click-to-checkout/fork",
    "Dynamic Context Compiler berplafon O(1) <= 2.200 token ramah KV prefix cache dan Panel Telemetri Token Plotly",
    "Gerbang LLM Lokal 8GB VRAM (Ollama default, LM Studio opsional), BYOM Cloud Gratis (kunci ephemeral), Mock Mode, dan Pipa Ketahanan JSON 4 Lapis",
    "Antarmuka Cockpit 3-Pane Anti-AI-Slop bergaya GitKraken, 3 Skenario Bawaan, Halaman FAQ, Modal Persetujuan Aktif T&C Indonesia, dan Ekspor Lokal JSON/Markdown"
  ],
  "niceToHave": [
    "Modal komparasi Side-by-Side (/diff) antara dua cabang",
    "Formulir pembuat skenario kustom sederhana di UI",
    "Impor kembali berkas ekspor JSON ke sesi baru"
  ],
  "notInMvp": [
    "Login, akun multi-user, dan cloud hosting",
    "Merge dua cabang kompleks beserta resolusi konflik otomatis",
    "Audio/TTS, Speech-to-Text, dan generator gambar karakter",
    "Perintah Git lanjutan (rebase, bisect, cherry-pick, stash)",
    "Sistem pembayaran dan langganan"
  ],
  "successMetrics": [
    "100% lulus >= 34 uji otomatis pytest (termasuk uji stres 100 giliran <= 2.200 token input)",
    "0 crash (0 HTTP 500) selama demo lokal offline OBS 1080p berdurasi 13-14 menit",
    "100% anggota tim memiliki riwayat commit aktif dan PR ter-merge di repositori GitHub publik",
    "Total biaya Claude API vibe-coding tetap <= $95 USD dari anggaran $100 USD",
    "Memenuhi seluruh 6 kriteria rubrik DDP1 Fasilkom UI untuk menembus rekomendasi Asdos ke final 9 kelas"
  ]
}
```
