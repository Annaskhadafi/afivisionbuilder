# AFI Vision Builder 🚀

<p align="center">
  <b>Enterprise Visual Node-Graph Platform for Real-Time AI Computer Vision Pipelines, Multi-Camera CCTV Analytics & Operational Dashboards</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch" />
  <img src="https://img.shields.io/badge/OpenCV-4.8+-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV" />
  <img src="https://img.shields.io/badge/Ultralytics-YOLOv8%20%2F%20v11-00FFFF?style=for-the-badge&logo=yolo&logoColor=black" alt="YOLO" />
  <img src="https://img.shields.io/badge/ByteTrack-Supervision%20v0.30-38B2AC?style=for-the-badge" alt="Tracking" />
  <img src="https://img.shields.io/badge/E2E%20Tests-14%20Suites%20Passed-22c55e?style=for-the-badge&logo=playwright&logoColor=white" alt="E2E Tests" />
</p>

<p align="center">
  <a href="#-fitur-unggulan-terbaru">Fitur Unggulan</a> •
  <a href="#-tur-antarmuka--showcase-visual">Tur Antarmuka</a> •
  <a href="#-instalasi--eksekusi-1-click">Instalasi Cepat</a> •
  <a href="#-katalog-50-node-lengkap">Katalog 50 Node</a> •
  <a href="#-arsitektur-sistem">Arsitektur</a> •
  <a href="#-pengujian-otomatis-e2e">Pengujian E2E</a> •
  <a href="#-lisensi--kontributor">Lisensi</a>
</p>

---

## 🌟 Overview Aplikasi

**AFI Vision Builder** adalah platform visual tanpa coding (*low-code / zero-code*) untuk merancang, menguji, dan mendeploy pipeline Computer Vision & AI secara real-time. Dengan antarmuka node-graph berbasis kabel kurva Bézier yang intuitif, Anda dapat menyambungkan input video/kamera industri, inferensi model AI (YOLO, RF-DETR, SAM 3, VLM), pelacakan objek, analitik poligon multi-zona, hingga dashboard operasional multi-kamera CCTV secara terpadu.

![Hero Showcase - Live Restaurant Table Occupancy Tracking](docs/screenshots/03_restaurant_live_tracking.png)

---

## ✨ Fitur Unggulan Terbaru

### 🍽️ 1. Restaurant Table Occupancy & Dining Dwell Time Tracker
- **Pemantauan Meja Restoran/Kafe Real-Time**: Deteksi otomatis status keterisian meja (`VACANT` ➔ `CONFIRMING` ➔ `OCCUPIED` ➔ `PENDING_VACANT`).
- **Compact Centroid Timer Overlay**: Indikator durasi duduk tamu (`1s`, `4m 12s`) diletakkan tepat di titik tengah meja dengan kartu glassmorphism semi-transparan, tidak menghalangi tampilan makanan/tamu.
- **Tahan Terhadap Flicker & Video Loop**: State Machine tangguh dengan toleransi *grace period* saat tamu bergerak atau terhalang sejenak.
- **Template Siap Pakai**: Tersedia template alur kerja 4 meja restoran (VIP, 4-seat, 2-seat) di Projects Hub.

### 📐 2. Interactive In-Canvas Multi-Zone & Polygon Editor
- **Gambar Poligon Area Langsung di Atas Video**: Buat area ROI (*Region of Interest*) langsung dari frame live preview atau grid kalibrasi.
- **Draggable Vertex Handles**: Geser titik sudut, tambah titik baru di garis tepi, atau hapus titik sudut poligon dengan interaksi klik visual.
- **Multi-Area Management**: Kelola banyak area sekaligus (misal: Meja 1-4, Bay Workshop 1-5, Pintu Gerbang) lengkap dengan kapasitas maksimum dan batas waktu overstay.

### 📹 3. Multi-Camera Operations Matrix (8-Stream CCTV Grid)
- **Monitoring Simultan 8 Kamera RTSP**: Menampilkan streaming langsung 5 Workshop Bays (`WS-01` s/d `WS-05`) dan 3 Warehouse Gates (`WH-01` s/d `WH-03`).
- **Grid Layout Switcher**: Ganti tampilan dalam 1 klik antara mode **1 Fokus**, **4 Grid (2x2)**, atau **9 Matrix (3x3)**.
- **Filter Kategori Kamera**: Filter cepat tampilan berdasarkan area (*All*, *Workshop Bays*, *Warehouse Gates*).
- **Direct Workflow Binding**: Setiap kartu kamera dilengkapi status koneksi workflow dan tombol cepat untuk membuka alur kerja terkait di Studio.

### ⏱️ 4. Workshop Work Duration Sessions Dashboard
- **Rekap Durasi Kerja Otomatis**: Menghitung waktu mulai, waktu selesai, dan durasi efektif kerja di setiap bay workshop tanpa bergantung pada tracking ID transien.
- **KPI Metrics Card**: Ringkasan Total Sesi, Total Jam Kerja, Rata-rata Durasi/Sesi, dan Jumlah Ban/Objek terproses.
- **Filter Shift Kerja**: Filter data berdasarkan Shift Pagi, Shift Siang, Shift Malam, atau seluruh shift dengan pencarian live bay.
- **Ekspor CSV 1-Klik**: Unduh seluruh riwayat sesi kerja ke format spreadsheet CSV.

### 🚪 5. Warehouse Gate Exit Events & ERP Sync Logs
- **Deteksi Transisi Keluar Sah (Inside-to-Outside)**: Memverifikasi pergerakan fisik objek dari dalam gudang melintasi gerbang ke luar, mencegah *false alarm* akibat objek yang sekadar hilang dari pandangan kamera.
- **Status Integrasi ERP**: Pelacakan status sinkronisasi kejadian (*Delivered*, *Queued*, *Failed*) dengan nomor referensi DO/SJ.
- **Filter Gerbang & Status**: Filter log berdasarkan gerbang spesifik (`WH-01`, `WH-02`, `WH-03`) dan ekspor rekaman kejadian ke CSV.

### 🎨 6. Roboflow-Style Overlay / Annotate Inspector
- **Manajemen Layer Anotasi Terpadu**: Kendalikan seluruh tampilan visual di satu node inspector modern.
- **Pilihan Layer Lengkap**: Bounding box (warna & ketebalan kustom), Label dinamis (`{class} {confidence}`), Confidence score, Status badge, Custom text, Heatmap, dan Panah arah gerak (*Direction Arrow*).
- **Layer Reorder & Toggle**: Urutkan tumpukan layer ke atas/bawah, sembunyikan/tampilkan per layer, serta hapus layer dengan cepat.

### 🧠 7. Central Model Registry & Hub
- **Repositori Model Terpusat**: Manajemen seluruh bobot model AI yang terpasang di sistem (`.pt`, `.onnx`, `.engine`, `.tflite`).
- **Tabel Metadata Lengkap**: Menampilkan informasi Engine inferensi, Format, Task, Versi, Ukuran file, dan Status ketersediaan.
- **Upload Modal Drag-and-Drop**: Unggah custom model buatan sendiri langsung dari peramban web.

### 🤖 8. AI Agent & Vision-Language Model (VLM)
- **Penalaran Multimodal Tingkat Lanjut**: Kirim frame tangkapan kamera ke model VLM (OpenAI GPT-4o/5, 9router, atau OpenRouter) untuk analisis visual mendalam, deteksi cacat kompleks, dan inspeksi SOP industri.
- **Keamanan Kredensial**: API Key disanitasi secara otomatis dan dapat dimuat aman dari environment server (`.env`).

---

## 📸 Tur Antarmuka & Showcase Visual

### 1. Projects & Templates Hub
Halaman awal untuk mengelola seluruh proyek alur kerja, membuka proyek terkini, mengimpor alur kerja JSON, dan memilih template siap pakai industri (Restaurant Dwell Tracker, Bottle Inspection, dll).
![Projects Hub](docs/screenshots/01_projects_hub.png)

---

### 2. Workflow Studio Canvas
Kanvas node-graph interaktif dengan kabel Bézier halus, auto-connect cerdas, zoom & pan mulus, panel library 50+ node, status runtime Python, dan inspector parameter berlabel Bahasa Indonesia.
![Workflow Studio Canvas](docs/screenshots/02_studio_canvas.png)

---

### 3. Live Execution: Restaurant Table Occupancy & Dining Dwell Tracker
Pipeline video CCTV Kafe berjalan secara live pada CPU/GPU, menampilkan deteksi YOLOv8 + ByteTrack dengan timer durasi duduk tamu (`1s`, `4m 12s`) di tengah meja secara elegan tanpa menutupi makanan.
![Restaurant Live Execution](docs/screenshots/03_restaurant_live_tracking.png)

---

### 4. Interactive Multi-Zone Polygon Editor
Editor poligon interaktif di atas frame video live: operator dapat memilih area meja/bay, menggeser titik sudut (*vertex handles*), menambah area baru, dan menyetel kapasitas maksimal.
![Multi-Zone Polygon Editor](docs/screenshots/04_multi_zone_editor.png)

---

### 5. Roboflow-Style Overlay / Annotate Inspector
Panel inspector modern bergaya Roboflow untuk menambahkan layer anotasi (kotak pembatas, label kelas, heatmap, skor akurasi) dengan pengaturan warna, posisi, dan ketebalan interaktif.
![Overlay Annotate Inspector](docs/screenshots/05_overlay_annotate_inspector.png)

---

### 6. Multi-Camera Operations Matrix (8-Bay CCTV Grid)
Matriks pemantauan terpusat untuk 8 kamera CCTV industri (5 Bay Workshop + 3 Gerbang Warehouse) dengan opsi tampilan 1 Fokus, 4 Grid, dan 9 Matrix lengkap dengan FPS live meter.
![Live CCTV Matrix](docs/screenshots/06_live_cctv_matrix.png)

---

### 7. Modern Camera Settings & Workflow Auto-Binding
Dialog konfigurasi kamera CCTV kontras tinggi dengan fitur *Auto-generate Workflow* dari template industri dan tombol shortcut langsung `[📐 Gambar Poligon Area]`.
![Camera Settings Modal](docs/screenshots/07_camera_settings_modal.png)

---

### 8. Workshop Work Duration Sessions Dashboard
Dashboard analitik sesi kerja bengkel/workshop: kartu ringkasan KPI, filter shift (Pagi, Siang, Malam), pencarian live bay, dan tombol ekspor CSV untuk integrasi laporan.
![Workshop Sessions Dashboard](docs/screenshots/08_workshop_sessions.png)

---

### 9. Warehouse Gate Exit Events & ERP Logs
Log kejadian keluar gerbang gudang dengan verifikasi transisi fisik dari dalam ke luar gerbang, status pengiriman ERP (*Delivered* / *Queued*), filter pintu gerbang, dan ekspor CSV.
![Warehouse Events Log](docs/screenshots/09_warehouse_events.png)

---

### 10. Central Model Registry Manager
Panel manajemen model AI terpusat dengan tabel metadata terstruktur (YOLOv8, YOLOv11, ONNX, TensorRT, RF-DETR), status aktif, serta modal upload model baru.
![Models Registry Manager](docs/screenshots/10_models_registry.png)

---

## ⚡ Instalasi & Eksekusi (1-Click)

### 🪟 Pengguna Windows (Disarankan)

AFI Vision Builder dirancang portabel dengan skrip launcher otomatis:

1. **Persyaratan**: Pastikan **Python 3.10, 3.11, atau 3.12** terpasang *(Centang "Add Python to PATH" saat instalasi)*.
2. **Instalasi Dependensi (Cukup 1x di awal)**:
   Klik dua kali berkas:
   ```cmd
   install.bat
   ```
   > Skrip ini otomatis membuat virtual environment (`.venv`), memasang PyTorch, Ultralytics, Supervision, OpenCV, FastAPI, dan seluruh modul pendukung.
3. **Menjalankan Aplikasi**:
   Klik dua kali berkas:
   ```cmd
   run.bat
   ```
   > Server lokal akan langsung aktif dan otomatis membuka peramban web ke:  
   > 👉 **http://127.0.0.1:8765**

---

### 🐧 Pengguna Linux & macOS

1. Berikan izin eksekusi pada berkas skrip:
   ```bash
   chmod +x install.sh run.sh
   ```
2. Jalankan instalasi:
   ```bash
   ./install.sh
   ```
3. Jalankan aplikasi:
   ```bash
   ./run.sh
   ```

---

## 🧩 Katalog 50 Node Lengkap

Seluruh node dikelompokkan ke dalam 5 kategori fungsional dengan parameter berlabel Bahasa Indonesia dan panduan interaktif:

| Kategori | Node Siap Pakai | Fungsi & Deskripsi Utama |
| :--- | :--- | :--- |
| 📹 **Sources (Input)** | `Web Camera`, `IP Camera (RTSP)`, `Daheng Industrial Camera`, `Video File`, `Static Image` | Akuisisi citra/streaming frame dari berbagai tipe kamera dan berkas multimedia. |
| 🧠 **AI Vision Models** | `Ultralytics YOLO`, `RF-DETR Object Detection`, `SAM 3 Segmentation`, `ConvNeXt Classifier`, `EfficientAD Anomaly`, `ONNX Model`, `TFLite Model`, `AI Agent (VLM Multimodal)` | Deteksi objek real-time, segmentasi instan, klasifikasi citra, inspeksi anomali cacat visual, dan analisis multimodal VLM. |
| 🎯 **Tracking & Spatial** | `ByteTrack`, `BoT-SORT`, `OC-SORT`, `Multi-Zone Occupancy & Table Tracker`, `Zone Activity Timer`, `Zone Exit Event`, `Multi-Line Counter (A↔B)`, `Object Counter`, `Dwell Time Zone`, `ROI Filter (Polygon Area)` | Pelacakan ID konsisten objek bergerak, penghitungan keluar-masuk garis dua arah, timer durasi terisi meja restoran, dan verifikasi transisi gerbang keluar. |
| 🎨 **Preprocessing & Drawing** | `Overlay / Annotate (Layers)`, `Resize Frame`, `Crop Region`, `Rotate & Flip`, `Color Convert`, `Brightness & Contrast (CLAHE)`, `Blur & Sharpen`, `Perspective Correction`, `Privacy Blur`, `Python Script Editor` | Manipulasi citra, night-vision CLAHE, sensor otomatis wajah/plat nomor, compositing anotasi gambar, dan script eksekusi Python kustom. |
| 🔀 **Logic, Flow & Outputs** | `If / Else Branch`, `Compare Value`, `Confidence Threshold`, `Timer Delay`, `Debounce Filter`, `Rate Limiter`, `AND / OR Gate`, `Trigger Once`, `Live Preview`, `Event Alert Popup`, `Image / Crop Exporter`, `SQLite Database Logger`, `HTTP Webhook` | Percabangan logika alur kerja, gerbang pembanding angka, penampil preview real-time, perekaman event ke SQLite database, dan webhook REST API ke sistem ERP eksternal. |

---

## 🏗️ Arsitektur Sistem

```text
afivisionbuilder/
├── 📁 engine/                     # Core Runtime Computer Vision & AI Engine
│   ├── core.py                    # Pipeline execution loop, threading, & Node Graph dispatcher
│   ├── multi_zone_occupancy.py    # Multi-Zone table tracking, FSM states, & geometric centroid testing
│   ├── project_nodes.py           # Specialized nodes (Zone Activity Timer, Zone Exit Event)
│   ├── custom_model_runtime.py    # YOLO / PyTorch / CUDA Fallback Manager
│   ├── vlm_box_tracker.py         # Multimodal Vision-Language Model interface
│   ├── node_catalog.py            # Registry 50 Node, metadata, & skema parameter
│   ├── main.py                    # Algoritma image processing OpenCV & spatial filters
│   └── camera_daheng.py           # Driver SDK kamera industri Daheng
├── 📁 static/                     # Frontend Single Page Application (SPA)
│   ├── index.html                 # Struktur markup Studio, Dashboard, & Hub
│   ├── app.js                     # State management, Bézier canvas routing, & UI interactions
│   ├── style.css                  # Desain visual modern, tema dark, & glassmorphism
│   └── logo.png                   # Brand identitas AFI Vision Builder
├── 📁 docs/                       # Dokumentasi Teknis & Showcase Media
│   ├── PRD.md                     # Product Requirements Document
│   ├── TASK_LIST.md               # Riwayat pengerjaan, handoff log, & roadmap
│   └── screenshots/               # Koleksi 10 tangkapan layar antarmuka resolusi tinggi
├── 📁 tests/                      # Automated E2E Test Suites (@e2e-dev/web & Playwright)
│   ├── example.e2e.ts             # Workspace loading & brand verification
│   ├── restaurant_cafe_running.e2e.ts  # Video pipeline & live table dwell time tracking
│   ├── template_restaurant_table.e2e.ts# Template instansiasi meja restoran
│   ├── dashboard_operations.e2e.ts# 8-camera matrix, workshop sessions, & warehouse events
│   ├── camera_settings_workflow.e2e.ts # Camera modal, auto-binding, & polygon drawing
│   ├── multi_zone_occupancy.e2e.ts# Visual polygon editor & inspector verification
│   ├── node_overlay_annotate.e2e.ts # Overlay layers inspector verification
│   └── projects_and_models_hub.e2e.ts # Hub landing page & Model registry
├── 📁 data/                       # Penyimpanan Lokal Terisolasi
│   ├── models/                    # Bobot model AI lokal (.pt, .onnx)
│   ├── projects/                  # File alur kerja JSON proyek
│   ├── cameras.json               # Konfigurasi 8 kamera CCTV industri
│   ├── outputs/                   # Folder hasil ekspor frame & crop event
│   └── visonode.db                # SQLite database log sesi & event
├── 📄 server.py                   # REST API & WebSocket Streaming Server (FastAPI / Starlette)
├── 📄 e2e.config.ts               # Konfigurasi pengujian otomatis E2E
├── 📄 requirements.txt            # Daftar pustaka Python terverifikasi
├── ⚙️ install.bat / run.bat       # Skrip instalasi & launcher otomatis Windows
└── ⚙️ install.sh / run.sh         # Skrip instalasi & launcher Linux/macOS
```

---

## 🧪 Pengujian Otomatis E2E (Quality Assurance)

AFI Vision Builder dilengkapi standar pengujian otomatis **End-to-End (E2E)** berbasis *real-browser* menggunakan runner modern `e2e`:

- **14 Suite Pengujian E2E**: Menguji seluruh fungsionalitas dari perspektif pengguna nyata (kanvas flow, video stream live, modal pengaturan kamera, editor poligon, filter shift, dan ekspor CSV).
- **Verifikasi AI Agent**: Memanfaatkan agen visual untuk memvalidasi kelayakan antarmuka di setiap langkah pengujian.
- **Tangkapan Layar Otomatis**: Setiap proses pengujian secara otomatis mendokumentasikan bukti screenshot visual ke folder `.e2e/artifacts/`.

Jalankan seluruh pengujian dengan satu perintah:
```bash
npm run test:e2e
```
Atau jalankan skenario spesifik:
```bash
npx e2e run tests/restaurant_cafe_running.e2e.ts
```

---

## 🛠️ Persyaratan Sistem

- **Sistem Operasi**: Windows 10/11 (64-bit), Ubuntu 20.04/22.04 LTS, atau macOS.
- **Prosesor**: Minimal Intel Core i5 / AMD Ryzen 5 (disarankan 6 core ke atas).
- **RAM**: Minimal 8 GB (disarankan 16 GB untuk multi-camera matrix).
- **GPU (Opsional)**: NVIDIA GeForce GTX 1060 ke atas dengan CUDA 11.8 / 12.x untuk inferensi real-time maksimal. *Jika tidak ada GPU, aplikasi otomatis menggunakan akselerasi CPU dengan mulus.*

---

## 📄 Lisensi & Pengembang

Dikembangkan dengan dedikasi tinggi oleh **Anas Khadafi** ([@Annaskhadafi](https://github.com/Annaskhadafi)) dan tim untuk kebutuhan inspeksi visual industri, analitik CCTV cerdas, dan automasi Computer Vision modern.

Hak Cipta © 2026 **AFI Vision Builder**. Seluruh hak cipta dilindungi undang-undang.
