# Dokumen Persyaratan Produk (PRD) — No-Code Dashboard Builder & Visual Web Designer

**Nama Fitur:** Afivision Dashboard Builder & Standalone Web Export  
**Target Proyek:** `D:\[01] PROJECT\REA\webapp`  
**Tanggal:** 24 Oktober 2026  
**Status:** Disetujui (Approved) & Dalam Tahap Eksekusi  

---

## 1. Ringkasan Eksekutif & Latar Belakang

Afivision Builder telah memiliki editor alur kerja (*workflow studio*) berbasis node bergaya n8n/Node-RED yang andal untuk merancang pipa komputasi visi (*Computer Vision pipeline*), seperti deteksi objek YOLO, pelacakan Multi-Zone, pengenal plat nomor (LPR), estimasi pose tubuh manusia, hingga filter logika tingkat lanjut.

Akan tetapi, pengguna akhir di lapangan—mulai dari operator pos keamanan, supervisor pabrik, hingga manajer operasional—tidak membutuhkan diagram kabel node. Mereka membutuhkan antarmuka pemantauan terpadu yang menampilkan monitor CCTV, kartu indikator angka (scorecard), grafik tren fluktuasi, tabel kejadian terkini, dan tombol unduh laporan harian.

Fitur **Dashboard Builder** hadir sebagai solusi penjembatan: sebuah perancang web visual nirkode (*No-Code Web Builder*) bergaya gabungan **Elementor / Canva** (kebebasan tata letak seret-dan-lepas) dan **Google Looker / Grafana** (interaksi analitik metrik dan filter silang). Lebih dari itu, pengguna dapat mengekspor hasil rancangan dashboard beserta pipa AI-nya menjadi paket **Docker Compose mandiri** yang dapat dijalankan di server mana pun tanpa ketergantungan pada studio Afivision.

---

## 2. Arsitektur Inti & Keputusan Desain

Berdasarkan kesepakatan teknis, arsitektur sistem dibangun di atas empat pilar utama:

### 2.1 Tata Letak Bebas Seret & Lepas (Free Drag & Drop Canvas)
* Kanvas desain menggunakan sistem koordinat absolut `(x, y, w, h, z-index)` dengan panduan garis bantu sejajar (*smart snapping guidelines*).
* Setiap widget dapat digeser secara leluasa ke posisi mana pun di atas kanvas dan ditarik sudutnya (*resize handles*) untuk mengubah dimensi kartu.
* Kanvas mendukung sistem dwi-tema: **Dark Mode (Command Center)** sebagai standar bawaan dengan kontras warna tajam, serta **Light Mode** untuk presentasi manajemen.

### 2.2 Arsitektur Multi-Workflow Terpadu (Federated Multi-Process)
* Satu kanvas dashboard dapat menghubungkan banyak file alur kerja sekaligus.
* Setiap alur kerja atau sumber kamera dijalankan pada proses latar belakang mandiri (*Multi-Process Isolation*) agar komputasi berat pada satu kamera tidak menghambat kelancaran kamera lainnya (*non-blocking*).

### 2.3 Standar Bus Data Universal (`Afivision Universal Data Bus`)
* Untuk menjamin semua variasi node yang ada (YOLO, LPR, Pose, OCR, Zone Occupancy, Anomaly) dapat menyalurkan data ke widget mana pun, sistem menerapkan kontrak data terpadu melalui WebSocket dan memori lokal:
  ```json
  {
    "workflow_id": "wf_gate_in",
    "node_id": "lpr_camera_01",
    "timestamp": 1729792000.12,
    "metrics": {
      "count": 12,
      "text": "B 1945 ZZZ",
      "status": "APPROVED",
      "speed": 18.5
    },
    "alert": {
      "level": "normal",
      "message": "Kendaraan logistik terverifikasi"
    },
    "stream_id": "cam_gate_in"
  }
  ```
* Node baru bernama **`dashboard_sink`** disediakan di studio alur kerja untuk menetapkan variabel keluaran utama, label deskripsi, serta batas ambang peringatan (*threshold*).

### 2.4 Penyimpanan Historis Otomatis (SQLite Time-Series)
* Engine secara berkala merekam ringkasan angka metrik dan log kejadian deteksi ke dalam berkas basis data SQLite lokal (`data/dashboard_history.db`).
* Data historis ini menjadi sumber bahan bakar bagi widget grafik tren dan fungsi penarikan laporan lembar sebar (*spreadsheet*).

---

## 3. Spesifikasi 5 Widget Inti (MVP)

### 3.1 Widget CCTV Player (Pemutar Video Kamera Pintar)
* **Tampilan:** Mengalirkan video dari node input kamera atau node pemrosesan visual melalui rute `/api/preview/{node_id}`.
* **Bilah Kontrol Kartu:**
  1. *Tombol Layar Penuh (Fullscreen):* Memperbesar tampilan video ke jendela modal terfokus tanpa mengganggu komposisi kanvas.
  2. *Sakelar Mode Aliran (Stream Toggle):* Mengalihkan seketika antara aliran video asli (*Raw Video*) dan video beranotasi kotak AI (*Annotated Stream*).
  3. *Tombol Tangkapan Layar (Snapshot):* Mengunduh frame detik tersebut dalam format `.PNG` resolusi penuh.
  4. *Lencana Status Jaringan:* Menampilkan status koneksi kamera (Aktif, Menghubungkan Ulang, atau Terputus) beserta taksiran laju frame (FPS).

### 3.2 Widget Scorecard KPI (Kartu Metrik Beradaptasi)
* **Tampilan:** Menampilkan nilai metrik numerik berukuran besar, label penjelas, dan ikon penanda.
* **Perilaku Ambang Batas Tiga Tingkat (Adaptive Thresholds):**
  - 🟢 **Normal (Hijau):** Nilai berada pada rentang aman.
  - 🟡 **Waspada (Kuning):** Nilai mendekati batas toleransi operasional.
  - 🔴 **Bahaya (Merah Berkedip):** Nilai melampaui batas toleransi kritis, memicu animasi denyut visual (*pulse*) untuk memperingatkan operator.
* **Pengaturan Sumber:** Pemilihan nama variabel metrik langsung melalui menu tarik-turun (*dropdown*) yang membaca daftar variabel dari node `dashboard_sink`.

### 3.3 Widget Grafik Analitik (Trend Chart)
* **Tampilan:** Grafik garis (*line chart*) atau diagram batang (*bar chart*) yang mencerminkan pola kenaikan atau penurunan angka deteksi.
* **Sumber Data:** Menarik rekaman historis dari SQLite lokal dengan pilihan rentang waktu fleksibel (1 Jam Terakhir, Hari Ini, 7 Hari Terakhir).

### 3.4 Widget Tabel Log Kejadian (Live Event Table)
* **Tampilan:** Tabel tabular yang memuat catatan kronologis kejadian deteksi secara langsung (*real-time*).
* **Kolom Informasi:** Cap Waktu (*Timestamp*), Nama Kamera / Lokasi, Objek Terdeteksi, Keterangan Teks, dan Status Validasi.
* **Kemampuan:** Dilengkapi penyaring rentang tanggal/jam dan fitur gulir otomatis saat ada data baru yang masuk.

### 3.5 Widget Tombol Ekspor Excel (.XLSX)
* **Tampilan:** Tombol aksi profesional dengan ikon lembar kerja.
* **Mekanisme Kerja:** Saat ditekan, sistem mengeksekusi panggilan ke endpoint `/api/dashboard/export-excel`, menyusun berkas Excel terformat rapi sesuai filter aktif, dan mengunduh berkas `.XLSX` langsung ke komputer pengguna.

---

## 4. Elemen Dekoratif & Kustomisasi Kanvas (Gaya Elementor)

Agar tampilan dashboard dapat disesuaikan dengan identitas operasional institusi atau perusahaan, kanvas dilengkapi perkakas tata letak:
1. **Komponen Teks Kustom:** Judul utama (H1–H3), teks keterangan, dan label penanda dengan kontrol perataan, warna teks, dan ukuran huruf.
2. **Komponen Logo & Citra:** Pengunggah berkas gambar untuk menyematkan logo korporat atau denah lokasi.
3. **Wadah Pengelompokan (Container Box):** Kartu pembungkus dengan pilihan warna latar semi-transparan dan garis tepi (*border*) untuk mengelompokkan kamera dan metrik satu zona.
4. **Lencana Status Global:** Indikator operasional ringkas seperti penanda shift kerja aktif atau status kesiapan sistem.

---

## 5. Interaksi Silang Antar-Widget (Gaya Looker / Cross-Filtering)

Dashboard bukan sekadar pajangan pasif, melainkan alat investigasi aktif:
* Mengklik salah satu kartu pemutar CCTV akan memicu penyaringan terfokus pada widget lain:
  - Kartu CCTV terpilih mendapat garis tepi sorotan (*highlight*).
  - Tabel log kejadian seketika hanya menampilkan baris yang bersumber dari kamera tersebut.
  - Kartu metrik menyesuaikan kalkulasi hanya untuk parameter kamera terpilih.
* Mengklik tombol pelepas filter (*Reset Filter*) mengembalikan tampilan ke ringkasan agregat seluruh area.

---

## 6. Format Paket Ekspor Mandiri (Docker Compose)

Ketika pengguna menekan tombol **"Export Web Dashboard"**, sistem menghasilkan sebuah berkas arsip berformat ZIP (`afivision-dashboard-standalone.zip`) dengan isi:

```text
afivision-dashboard-standalone/
├── docker-compose.yml           # Orkestrator Docker multi-layanan
├── Dockerfile                   # Definisi lingkungan runtime Python dan OpenCV
├── run.bat                      # Peluncur cepat untuk Windows
├── run.sh                       # Peluncur cepat untuk Linux / macOS
├── server.py                    # Server backend FastAPI dalam mode mandiri
├── engine/                      # Modul pemrosesan Computer Vision & AI runner
├── data/
│   ├── dashboard.json           # Tata letak kanvas dan binding data
│   ├── workflows/               # File alur kerja aktif yang dipasangi kamera
│   └── models/                  # Bobot model YOLO / model terdaftar (.pt, .onnx)
└── static/                      # Berkas antarmuka web dashboard terkompilasi
    ├── index.html               # Halaman mandiri tanpa editor studio
    ├── app.js                   # Mesin penampil widget dan koneksi WebSocket
    └── style.css                # Gaya visual dan tema dashboard
```

Pengguna penerima paket hanya perlu menjalankan:
```bash
docker compose up -d
```
atau pada komputer Windows biasa tanpa Docker:
```cmd
run.bat
```
Aplikasi dashboard langsung aktif pada peramban web di alamat `http://localhost:8765` tanpa perlu memasang aplikasi studio Afivision.

---

## 7. Metrik Keberhasilan & Pengujian

1. **Integritas Tata Letak:** Kartu dapat digeser dan diubah ukurannya dengan responsif tanpa lonjakan posisi tak terduga (*layout shifting*).
2. **Kinerja Aliran Multi-Kamera:** Mampu menampilkan minimal 4 aliran video 720p/480p sekaligus dengan latensi di bawah 250 ms pada jaringan lokal.
3. **Keandalan Ekspor Excel:** Penarikan berkas `.XLSX` untuk 10.000 baris rekaman terselesaikan dalam waktu kurang dari 3 detik.
4. **Kemandirian Paket Ekspor:** Paket Docker Compose hasil unduhan teruji lolos bangun (*build pass*) dan berhasil menyajikan antarmuka pemantauan secara mandiri.
