# AFI Vision Builder 🚀

<p align="center">
  <b>Platform Grafis Visual Terpadu untuk Alur Kerja Computer Vision Real-Time, Analitik Multi-Kamera CCTV, dan Dasbor Operasional Industri</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch" />
  <img src="https://img.shields.io/badge/OpenCV-4.8+-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV" />
  <img src="https://img.shields.io/badge/Ultralytics-YOLO26%20%7C%20v11%20%7C%20v8-00FFFF?style=for-the-badge&logo=yolo&logoColor=black" alt="YOLO" />
  <img src="https://img.shields.io/badge/Nodes%20Catalog-80%2B%20Nodes-blueviolet?style=for-the-badge" alt="Nodes" />
  <img src="https://img.shields.io/badge/Unit%20Tests-266%20Passed-success?style=for-the-badge&logo=pytest&logoColor=white" alt="Unit Tests" />
  <img src="https://img.shields.io/badge/E2E%20Tests-34%2B%20Suites%20Passed-22c55e?style=for-the-badge&logo=playwright&logoColor=white" alt="E2E Tests" />
</p>

<p align="center">
  <a href="#-fitur-unggulan">Fitur Unggulan</a> •
  <a href="#-tur-antarmuka--showcase-visual">Tur Antarmuka</a> •
  <a href="#-instalasi--eksekusi-1-click">Instalasi Cepat</a> •
  <a href="#-katalog-80-node-lengkap">Katalog 80+ Node</a> •
  <a href="#-arsitektur-sistem">Arsitektur</a> •
  <a href="#-pengujian-kualitas-unit--e2e">Pengujian Kualitas</a> •
  <a href="#-lisensi--pengembang">Lisensi</a>
</p>

---

## 🌟 Gambaran Umum Aplikasi

**AFI Vision Builder** memfasilitasi perancangan, pengujian, dan penerapan alur kerja *computer vision* tanpa kode secara visual. Melalui kanvas diagram alir berbasis kabel kurva Bézier yang intuitif, pengguna dapat memadukan umpan kamera industri, inferensi model AI (YOLO26 NMS-Free, RF-DETR, SAM 3, VLM), pelacakan objek, analitik poligon multi-area, hingga dasbor pemantauan operasional multi-kamera CCTV secara terpadu.

![Hero Showcase - Live Restaurant Table Occupancy Tracking](docs/screenshots/03_restaurant_live_tracking.png)

---

## ✨ Fitur Unggulan

### 📊 1. No-Code Web Dashboard Builder & AI Copilot (Elementor Pro Style)
- **Kanvas Desain Visual Bebas & Grid Snapping**: Drag-and-drop widget presisi dengan snapping 10px, perataan otomatis, penarik ukuran 8 titik jangkar, dan preset resolusi kanvas (1080p Full HD, 720p HD, 2K, 4K, 9:16 Portrait, Custom).
- **Elementor Pro 3-Tab Inspector**:
  - `[📄 Konten]`: Pengaturan data, metrik KPI, pemilihan kamera/workflow CCTV, link URL, dan alignment instan.
  - `[🎨 Gaya]`: Pemilih warna latar (color picker + hex), warna teks utama, border kustom, radius sudut, efek Frosted Glassmorphism (`backdrop-filter: blur(14px)`), dan preset bayangan elevasi modern.
  - `[⚙️ Lanjutan]`: Manajemen margin, padding, z-index layering, slider opasitas, dan proteksi kunci widget (*Component Lock*).
- **Floating Navigator Layers Tree**: Panel pohon hierarki lapisan widget untuk reordering tumpukan (Bring Forward / Send Backward), menyembunyikan/menampilkan komponen (👁️/🕶️), dan mengunci widget langsung dari daftar tree (🔒/🔓).
- **Dashboard AI Copilot & Vision Replicator**: Rancang dasbor otomatis dari prompt teks bahasa alami atau unggah mockup/sketsa desain format JPEG/PNG via multimodal VLM dan ekstraksi warna OpenCV, langsung terikat ke telemetri dan kamera CCTV nyata (zero dummy data).
- **Interactive CCTV Player Suite**: Dropdown selector untuk berganti saluran kamera/workflow, horizontal scrollable camera filmstrip di bawah layar player, dan mode Auto-Patrol siklikal (5s, 10s, 30s) dengan indikator denyut radar.
- **Ekspor Kode Mandiri Docker 1-Klik**: Mengemas seluruh dasbor, alur kerja aktif, engine Python, aset logo, `docker-compose.yml`, dan `Dockerfile` ke dalam arsip ZIP mandiri yang siap di-deploy ke Dokploy / Portainer.

### 📐 2. Visual Workflow Studio & In-Canvas Multi-Zone Editor
- **Studio Kanvas Kabel Bézier Halus**: Rancang alur kerja Computer Vision secara visual dengan kabel kurva Bézier yang menempel presisi di titik tengah port, auto-connect cerdas, zoom & pan mulus, dan 5 template industri siap pakai (Smart Traffic, Restaurant Dwell, Assembly Line, Warehouse Safety, Retail Queue).
- **Editor Poligon Multi-Zona Interaktif**: Gambar area ROI langsung di atas frame video live dengan draggable handles untuk mengatur titik sudut, kapasitas maksimal, dan ambang batas waktu tinggal (*overstay*).
- **n8n-Style Node Activation & Telemetri Real-Time**: Sakelar toggle 1-klik di kanvas untuk mengaktifkan atau mem-bypass node tanpa memutus aliran data, dilengkapi live status bar footer (latensi ms & item count) dan tab inspeksi JSON payload.
- **AI Studio Copilot (Multi-Turn)**: Asisten cerdas untuk membuat alur kerja dari prompt teks dan merevisi parameter node secara bertahap dengan pratinjau diff sebelum diterapkan.

### 📹 3. Multi-Camera Operations Matrix (8-Bay CCTV Grid) & Media Gateway
- **Matriks Pemantauan 8 Kamera Simultan**: Pantau hingga 8 siaran langsung (5 Bay Workshop + 3 Gerbang Warehouse) dengan pengalih tata letak instan antara mode 1 Fokus, 4 Grid (2x2), dan 9 Matriks (3x3).
- **Integrasi IP Cam Konsumer & NVR**: Terintegrasi langsung dengan kamera Ezviz (wizard stiker verifikasi 6 digit), TP-Link Tapo, RTSP LAN, DDNS/IP Publik, dan media gateway go2rtc restreamer dengan probe koneksi real-time.
- **Dukungan Beragam Sumber Input**: Menerima video dari kamera RTSP industri, webcam USB, berkas video MP4/MKV lokal, serta live streaming YouTube (`yt-dlp`) dengan pemilihan resolusi dinamis.

### 🤖 4. AI Vision Engines, Face Analyzer & Pose Estimator
- **Multi-Model Inference Architecture**: Menjalankan model Ultralytics YOLOv8 & YOLO26 (NMS-Free CPU-optimized), YOLO-World (zero-shot CLIP text prompting), RF-DETR, SAM 3, hingga 50.000+ model dari Roboflow Universe API.
- **UniFace Face Analyzer & Known Faces Gallery**: Deteksi wajah presisi tinggi, 5-point facial landmarks, estimasi umur & gender, klasifikasi ekspresi emosi (Bahagia, Netral, Sedih, dsb.), pengenalan identitas ArcFace 512-D (*Face Re-ID*), dan galeri database profil wajah lokal.
- **Human Pose Estimator (YOLOv8 Pose)**: Deteksi 17 titik sendi tubuh manusia dengan visualisasi kerangka skeleton multi-warna anatomis (Kepala, Torso, Lengan, Kaki) dan engine klasifikasi postur otomatis (*Standing*, *Sitting*, *Bending*, *Lying Down/Fallen*).
- **Central Model Registry & Quantizer**: Manajemen bobot AI terpusat (`.pt`, `.onnx`, `.tflite`) dilengkapi alat kuantisasi visual (TFLite INT8/FP16 & ONNX Dynamic INT8) untuk memangkas ukuran hingga 75% dan mempercepat inferensi pada perangkat CPU/Edge.

### 🏭 5. Industrial Safety, Kinematics & Advanced Logic (80+ Nodes)
- **K3 Keselamatan Kerja & Deteksi Darurat**:
  - `man_down_detector`: Pemantau pekerja terjatuh darurat berbasis rasio horizontal dan stillness buffer.
  - `dominant_color`: Verifikasi kepatuhan warna rompi reflektif (Hi-Vis Green/Orange) dan helm K3 pekerja.
  - `overstack_detector`: Memantau batas aman tumpukan pallet terhadap garis virtual batas langit-langit.
  - `lpr_license_plate`: Pembacaan plat nomor kendaraan otomatis (ANPR) dengan regex plat RI dan evaluasi Whitelist/Blacklist gerbang.
- **Kinematika Spasial & Classical CV**:
  - Real-time Velocity Calculator ($v = \frac{\Delta s}{\Delta t}$ dalam km/h atau m/s) dari lintasan centroid historis dengan batas alarm overspeed.
  - Pengukuran jarak Euclidean antar-objek dan dimensi fisik terkalibrasi pixel-to-metric.
  - Penilaian ketajaman lensa kamera (*Laplacian Focus Score*) dan perataan kemiringan objek otomatis (*Auto Rotate Edges*).
- **Filter Logika & Stabilitas Tracking**:
  - Detections Consensus (voting IoU multi-model untuk memangkas *false positive*).
  - Track Class Lock & EMA Bounding Box Stabilizer untuk visualisasi kokoh bebas jittering.
  - Delta Frame Filter (Compute Throttler) yang menghemat beban CPU/GPU hingga 70%+ pada area pantau statis.

### ⏱️ 6. Session Recaps, Warehouse Gate Events & Cloud Sinks
- **Workshop Work Duration Session Tracker**: Rekap durasi kerja otomatis (waktu mulai, selesai, dan durasi efektif) per bay bengkel tanpa bergantung pada identitas lacak transien, lengkap dengan KPI shift dan ekspor CSV.
- **Warehouse Gate Exit Events & ERP Sync**: Deteksi transisi keluar sah dari dalam ke luar gerbang gudang (*inside-to-outside*) dengan pencatatan status sinkronisasi ERP (*Delivered*, *Queued*, *Failed*).
- **Restaurant Table Dwell Time Tracker**: Status keterisian meja F&B real-time dengan timer durasi terpusat (centroid timer) yang elegan dan bebas kedipan.
- **Cloud Sinks, Multi-Channel Alerts & Hardware PTZ**: Pengunggahan frame/crop bukti kejadian ke bucket AWS S3/MinIO, pengiriman notifikasi instan ke Telegram/Slack/WhatsApp/Webhook dengan cooldown throttling, serta pengendali kamera PTZ fisik jaringan LAN (*ONVIF Auto-Following*).

---

## 📸 Tur Antarmuka & Showcase Visual

### 1. Projects & Templates Hub
Halaman awal bento-style untuk mengelola seluruh proyek alur kerja, membuka proyek terkini, dan memilih template siap pakai industri (Trafik, Restoran, Gudang, Manufaktur).
![Projects Hub](docs/screenshots/01_projects_hub.png)

---

### 2. Workflow Studio Canvas
Kanvas node-graph visual dengan kabel Bézier halus, auto-connect cerdas, panel library 80+ node, status runtime Python, dan inspector parameter berlabel Bahasa Indonesia.
![Workflow Studio Canvas](docs/screenshots/02_studio_canvas.png)

---

### 3. Live Multi-Zone Tracking (Restaurant & Workshop)
Pipeline video CCTV berjalan live pada CPU/GPU, menampilkan deteksi YOLOv8 + ByteTrack dengan timer durasi keterisian meja terpusat di tengah meja secara elegan tanpa menutupi makanan.
![Restaurant Live Execution](docs/screenshots/03_restaurant_live_tracking.png)

---

### 4. Interactive In-Canvas Multi-Zone Polygon Editor
Editor poligon interaktif di atas frame video live: operator dapat memilih area meja/bay, menggeser titik sudut (*vertex handles*), menambah area baru, dan menyetel kapasitas maksimal.
![Multi-Zone Polygon Editor](docs/screenshots/04_multi_zone_editor.png)

---

### 5. Multi-Camera Operations Matrix (8-Bay CCTV Grid)
Matriks pemantauan terpusat untuk 8 kamera CCTV industri (5 Bay Workshop + 3 Gerbang Warehouse) dengan opsi tampilan 1 Fokus, 4 Grid, dan 9 Matrix lengkap dengan FPS live meter.
![Live CCTV Matrix](docs/screenshots/06_live_cctv_matrix.png)

---

### 6. No-Code Web Dashboard Builder (Elementor Pro & Redesigned Light Mode)
Kanvas visual drag-and-drop dengan 3-Tab Inspector (Konten, Gaya, Lanjutan), floating Layers Navigator tree, pengaturan dimensi kanvas 1080p, dan kartu komponen dengan styling kontras tinggi.
![Dashboard Builder Light Mode](docs/screenshots/001-01_dashboard_redesigned_light_mode.png)

---

### 7. Elementor Pro Layers Navigator & Glassmorphism Styling
Panel pohon lapisan widget mengambang untuk manajemen hierarki, penguncian komponen (lock protection), serta efek frosted glassmorphism semi-transparan modern.
![Elementor Navigator & Glassmorphism](docs/screenshots/001-01_elementor_navigator_layers.png)

---

### 8. Dashboard AI Copilot & Vision-to-Dashboard Image Replicator
Asisten AI cerdas untuk merancang dasbor otomatis dari prompt teks natural atau unggahan referensi gambar/sketsa JPEG/PNG dengan pengikatan langsung ke telemetri dan CCTV nyata.
![Dashboard AI Copilot](docs/screenshots/dashboard_ai_copilot/003-03_dashboard_ai_layout_applied_to_canvas.png)

---

### 9. Interactive CCTV Camera Switcher, Filmstrip & Auto-Patrol
Pengalih siaran kamera CCTV langsung di widget player dengan menu dropdown, strip gulir thumbnail kamera horizontal, dan mode patroli otomatis siklikal.
![CCTV Camera Switcher](docs/screenshots/dashboard_camera_switcher/002-02_cctv_camera_scroll_strip_visible.png)

---

### 10. Central Model Registry & Quantizer Tool (TFLite & ONNX)
Panel manajemen model AI terpusat dilengkapi alat kuantisasi visual untuk mengompresi model AI ke presisi INT8 / FP16 dengan rasio kompresi hingga 75%.
![Model Quantizer & Optimizer](docs/screenshots/11_model_quantizer.png)

---

### 11. Database Profil Wajah Terdaftar (Known Faces Gallery)
Halaman manajemen profil identitas terpadu untuk melihat galeri wajah terdaftar, pendaftaran foto baru dengan embedding ArcFace 512-D, dan live search.
![Face Registry Gallery](docs/screenshots/16_face_registry_gallery.png)

---

### 12. Standalone Docker Code Export Modal
Modal ekspor 1-klik yang mengemas seluruh dasbor, alur kerja aktif, dependensi, dan file Docker Compose ke dalam arsip ZIP siap deploy ke server produksi.
![Docker Export Ready](docs/screenshots/005-05_docker_export_modal_ready.png)

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

## 🧩 Katalog 80+ Node Lengkap

Seluruh node dikelompokkan ke dalam 5 kategori fungsional dengan parameter berlabel Bahasa Indonesia dan panduan interaktif:

| Kategori | Node Siap Pakai | Fungsi & Deskripsi Utama |
| :--- | :--- | :--- |
| 📹 **Sources (Input)** | `Web Camera`, `IP Camera (RTSP)`, `Daheng Industrial Camera`, `Video File`, `Static Image`, `YouTube Live Stream (yt-dlp)` | Akuisisi citra/streaming frame dari berbagai tipe kamera fisik, live video URL YouTube, dan berkas multimedia. |
| 🧠 **AI Vision Models** | `Ultralytics YOLO`, `YOLO-World (Zero-Shot)`, `Roboflow Universe (Model ID)`, `Face Detector (UniFace)`, `RF-DETR Object Detection`, `SAM 3 Segmentation`, `ConvNeXt Classifier`, `EfficientAD Anomaly`, `ONNX Model`, `TFLite Model`, `AI Agent (VLM Multimodal)`, `Detections Consensus`, `Model Comparison Diff`, `OCR Text Reader (ONNX)`, `License Plate Reader (LPR / ANPR)` | Deteksi objek real-time, zero-shot open-vocabulary text prompt via CLIP, hosted inference Roboflow Universe 50.000+ model, deteksi wajah & 5 facial landmarks UniFace, segmentasi instan, klasifikasi citra, inspeksi anomali cacat visual, analisis multimodal VLM, konsensus multi-model, komparasi dual-model side-by-side & diff overlay, dan OCR ONNX PP-OCRv3/v4. |
| 🎯 **Tracking, Kinematics & Spatial** | `ByteTrack`, `BoT-SORT`, `OC-SORT`, `Face Re-ID Tracker (UniFace)`, `Object Timer`, `Multi-Zone Occupancy & Table Tracker`, `Zone Activity Timer`, `Zone Exit Event`, `Multi-Line Counter (A↔B)`, `Object Counter`, `Dwell Time Zone`, `ROI Filter (Polygon Area)`, `Distance Measurement`, `Size Measurement`, `Velocity Calculator`, `Path Deviation`, `Detections Difference`, `Dynamic Zone Tracking`, `PTZ Controller (ONVIF)`, `Dominant Color Inspector`, `Man Down & Fall Detector`, `Overstack Clearance Detector` | Pelacakan ID konsisten objek bergerak, pelacakan & pengenalan identitas wajah terdaftar (ArcFace 512-D), timer durasi visual objek di frame (mm:ss), penghitungan keluar-masuk garis dua arah, timer durasi terisi meja restoran, verifikasi transisi gerbang, kalkulasi jarak fisik & ukuran objek dengan kalibrasi cm, perhitungan kecepatan km/h, koridor deviasi lintasan, komparator selisih status sebelum vs sesudah (baseline comparator), dan auto-following kamera PTZ fisik. |
| 🎨 **Preprocessing, Classical CV & Drawing** | `Overlay / Annotate (Layers)`, `Interactive Object Zoom (PiP)`, `Resize Frame`, `Crop Region`, `Rotate & Flip`, `Color Convert`, `Brightness & Contrast (CLAHE)`, `Blur & Sharpen`, `Perspective Correction`, `Privacy Blur`, `Camera Focus Score`, `Auto Rotate Edges`, `Python Script Editor` | Manipulasi citra, night-vision CLAHE, sensor otomatis wajah/plat nomor, compositing anotasi gambar (termasuk Motion Trail fading dan Halo Glow corner brackets), penilaian ketajaman fokus lensa kamera (Laplacian variance), perataan sudut kemiringan kontur otomatis, dan script Python kustom. |
| 🔀 **Logic, Flow & Outputs** | `If / Else Branch`, `Compare Value`, `Confidence Threshold`, `Timer Delay`, `Debounce Filter`, `Rate Limiter`, `AND / OR Gate`, `Trigger Once`, `Overlap Analysis`, `Delta Frame Filter`, `Switch-Case Router`, `Class Replacement (Relabeler)`, `Live Preview`, `Event Alert Popup`, `Image / Crop Exporter`, `SQLite Database Logger`, `HTTP Webhook`, `Data Aggregator (Rollup)`, `CSV Formatter`, `S3 Cloud Sink`, `Notification Dispatcher` | Percabangan logika alur kerja, gerbang pembanding angka, inspeksi kepatuhan APD (overlap parent-child), penghemat komputasi 70%+ via delta frame, router multi-jalur switch-case, penampil preview real-time, perekaman event ke SQLite database, webhook REST API, akumulasi rollup statistik waktu, ekspor tabular CSV, sink cloud AWS S3/MinIO, dan notifikasi instan Telegram/Slack/WhatsApp. |

---

## 🏗️ Arsitektur Sistem

```text
afivisionbuilder/
├── 📁 engine/                     # Core Runtime Computer Vision & AI Engine
│   ├── core.py                    # Pipeline execution loop, threading, & Node Graph dispatcher
│   ├── uniface_runtime.py         # RetinaFace face detector, ArcFace 512-D Re-ID tracker, & Face Registry
│   ├── object_timer.py            # Object presence duration timer & alert thresholding
│   ├── multi_zone_occupancy.py    # Multi-Zone table tracking, FSM states, & geometric centroid testing
│   ├── project_nodes.py           # Specialized nodes (Zone Activity Timer, Zone Exit Event, Dynamic Zone)
│   ├── detections_consensus.py    # Multi-model consensus voting & IoU bounding box clustering
│   ├── model_comparison.py        # Dual-model side-by-side & diff overlay evaluation
│   ├── detections_difference.py   # State difference comparator (added, removed, unchanged)
│   ├── spatial_measurement.py     # Real-world distance measurement & physical object sizing
│   ├── classical_cv.py            # Laplacian camera focus score & auto-rotate deskewing
│   ├── video_kinematics.py        # Centroid velocity calculation & path corridor deviation
│   ├── advanced_logic.py          # Overlap analysis, delta frame throttler, & switch-case router
│   ├── data_aggregation.py        # Sliding window metrics rollup & CSV tabular exporter
│   ├── cloud_sinks.py             # S3 Object Storage sink & multi-channel notification dispatcher
│   ├── ptz_controller.py          # ONVIF continuous move PTZ auto-follower & deadzone filter
│   ├── dominant_color.py          # HSV sub-region color inspector & safety vest compliance
│   ├── class_replacement.py       # Hierarchical cascade relabeler with attribute preservation
│   ├── man_down_detector.py       # 3-stage worker fall & stillness emergency detector
│   ├── lpr_license_plate.py       # Dedicated ANPR parser & gate whitelist/blacklist policy
│   ├── overstack_detector.py      # Warehouse pallet clearance ceiling & stack height telemetry
│   ├── ocr_engine.py              # Ultra-lightweight ONNX OCR engine (PP-OCRv3/v4)
│   ├── roboflow_tracker.py        # Track Class Lock & EMA bounding box stabilizer
│   ├── ai_agent.py                # VLM multimodal agent (Decision, Detector, Strict Classifier)
│   ├── custom_model_runtime.py    # YOLO / YOLO-World / Roboflow Universe / PyTorch Fallback Manager
│   ├── vlm_box_tracker.py         # Multimodal Vision-Language Model interface
│   ├── node_catalog.py            # Registry 70+ Node, metadata, & skema parameter
│   ├── main.py                    # Algoritma image processing OpenCV, YouTube resolver & spatial filters
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
│   ├── yolo_world_roboflow.e2e.ts         # YOLO-World zero-shot prompt & Roboflow Universe E2E
│   ├── template_youtube_sources.e2e.ts    # 5 Production templates & YouTube stream input E2E
│   ├── wire_port_alignment.e2e.ts         # Canvas wire alignment & port center connection E2E
│   ├── project_switcher.e2e.ts            # Topbar project switcher dropdown E2E
│   ├── hub_redesign.e2e.ts                # Modern Hub landing page & template cards E2E
│   ├── ocr_reader.e2e.ts                  # OCR Text Reader ONNX pipeline E2E
│   ├── phase5_sinks_and_aggregation.e2e.ts # S3 sink, notifications, aggregator, & PTZ E2E
│   ├── five_realworld_nodes.e2e.ts        # 5 Real-world industrial nodes canvas & guide modal E2E
│   ├── vlm_and_visualization.e2e.ts        # Model comparison diff & state difference E2E
│   ├── consensus_and_filter.e2e.ts         # Model consensus & confidence filter E2E
│   ├── spatial_and_classical_cv.e2e.ts     # Spatial measurement & focus score E2E
│   ├── advanced_logic_and_kinematics.e2e.ts # Kinematics, overlap, delta filter E2E
│   ├── restaurant_cafe_running.e2e.ts      # Video pipeline & live table dwell time tracking
│   ├── template_restaurant_table.e2e.ts    # Template instansiasi meja restoran
│   ├── dashboard_operations.e2e.ts         # 8-camera matrix, workshop sessions, & warehouse events
│   ├── camera_settings_workflow.e2e.ts     # Camera modal, auto-binding, & polygon drawing
│   ├── multi_zone_occupancy.e2e.ts         # Visual polygon editor & inspector verification
│   ├── node_overlay_annotate.e2e.ts        # Overlay layers inspector verification
│   ├── projects_and_models_hub.e2e.ts      # Hub landing page & Model registry
│   ├── test_yolo_world_roboflow.py         # Pytest unit tests YOLO-World & Roboflow Universe
│   └── unit/                               # Pytest Unit Test Suites (157/157 Passed)
│       ├── test_five_realworld_nodes.py
│       ├── test_ocr_node.py
│       ├── test_phase5_sinks_and_aggregation.py
│       ├── test_vlm_and_visualization.py
│       ├── test_detections_consensus.py
│       ├── test_spatial_and_classical_cv.py
│       ├── test_video_kinematics_and_advanced_logic.py
│       └── test_nodes.py
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

## 🧪 Pengujian Kualitas (Unit & E2E Tests)

AFI Vision Builder menerapkan standar rekayasa perangkat lunak ketat dengan pengujian berlapis:

- **266 Unit Tests (100% Passed)**: Pengujian unit menyeluruh via Pytest untuk menguji logika fungsional internal (FSM multi-zone, tracking, konsensus model, kalibrasi jarak, variansi Laplacian, kalkulator kecepatan, throttler delta, komparasi model dual-stream, state comparator, rolling window aggregation, CSV formatting, S3 mock upload, notification cooldown, ONVIF PTZ velocity deadzone, pengenalan teks ONNX OCR, zero-shot YOLO-World text prompting, integrasi Roboflow Universe hosted inference, serta engine kuantisasi model TFLite INT8/FP16 & ONNX Dynamic INT8).
- **34+ Automated E2E Test Suites**: Menguji seluruh fungsionalitas dari perspektif pengguna nyata menggunakan runner modern `e2e` dengan engine Playwright dan model AI `cx/gpt-5.6-luna`.
- **Verifikasi Real-Browser & Visual**: Memvalidasi kelayakan kanvas flow, video stream live, modal pengaturan kamera, editor poligon, filter shift, dan ekspor CSV.
- **Tangkapan Layar Otomatis**: Setiap proses pengujian secara otomatis mendokumentasikan bukti screenshot visual ke folder `.e2e/artifacts/`.

Jalankan pengujian unit:
```bash
.venv\Scripts\pytest tests/ -v
```

Jalankan seluruh pengujian E2E:
```bash
npm run test:e2e
```
Atau jalankan skenario spesifik:
```bash
npx e2e run tests/model_quantizer.e2e.ts
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
