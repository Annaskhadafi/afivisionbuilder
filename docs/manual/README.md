# BUKU PANDUAN RESMI OPERASIONAL DAN PENGEMBANGAN SISTEM
# AFI VISION BUILDER & INTEGRATED OPEN-NVR PLATFORM
## *The Comprehensive Enterprise Computer Vision & Video Management System Manual*

---

**Edisi:** Enterprise Production Edition (V3.8 / Re-ID Fleet)  
**Dokumen Klasifikasi:** Operational, Architectural & Integration Manual  
**Total Lingkup Materi:** 150 Halaman Setara Cetak Standar (*Comprehensive 11-Volume Master Guidebook*)  
**Tanggal Rilis:** November 2026  
**Target Pembaca:** Vision AI Engineer, CCTV Network Administrator, Automation / K3 Supervisor, Solution Architect, Software Developer, System Integrator.

---

## 📖 PENGANTAR DAN STRUKTUR BUKU PANDUAN

Buku panduan ini merupakan dokumentasi teknis dan operasional terlengkap untuk sistem **Afi Vision Builder** dan sub-sistem **Integrated Open-NVR**. Sistem ini dirancang untuk menjembatani kebutuhan implementasi *Computer Vision* industri tingkat lanjut—mulai dari workshop manufaktur, pergudangan (*warehouse*), inspeksi jalan, pemantauan K3 (*Occupational Health & Safety*), hingga integrasi NVR (*Network Video Recorder*) cerdas berskala perusahaan.

Buku panduan ini disusun dalam **11 Bagian Utama (Chapters)** yang dapat dibaca secara mandiri per bab maupun secara komprehensif dalam satu kesatuan dokumen master.

```
📁 docs/manual/
├── 📄 README.md                                          <-- Anda berada di sini (Peta Manual & Daftar Isi)
├── 📄 BAB_01_PENGENALAN_DAN_ARSITEKTUR.md                <-- Fondasi Arsitektur, Engine Pipeline, Dataflow Graph
├── 📄 BAB_02_PANDUAN_INSTALASI_DAN_DEPLOYMENT.md         <-- Baremetal, Docker, CUDA/OpenVINO, Environment & Service
├── 📄 BAB_03_WORKSPACE_STUDIO_DAN_NAVIGASI_UI.md         <-- Projects Hub, Visual Studio, Canvas, CAD Annotation Studio
├── 📄 BAB_04_ENSIKLOPEDIA_NODE_PART1_SOURCES_PREPROCESSING.md <-- Sources (3) & Image Preprocessing (16 Nodes)
├── 📄 BAB_04_ENSIKLOPEDIA_NODE_PART2_AI_MODELS.md        <-- 15 AI Vision Models (YOLO, Pose, SAM, UniFace, LPR, LLM)
├── 📄 BAB_04_ENSIKLOPEDIA_NODE_PART3_TRACKING_ANALYSIS.md <-- 25 Tracking & Kinematic Analysis Nodes
├── 📄 BAB_04_ENSIKLOPEDIA_NODE_PART4_LOGIC_FLOW_CONTROL.md <-- 15 Logic, Filter & Flow Control Nodes
├── 📄 BAB_04_ENSIKLOPEDIA_NODE_PART5_ANNOTATIONS_DRAWING.md <-- 7 Annotations, Overlay & Visualization Nodes
├── 📄 BAB_04_ENSIKLOPEDIA_NODE_PART6_OUTPUTS_EXPORT.md   <-- 16 Outputs, Cloud Sinks, Event Recorders & Code Export
├── 📄 BAB_05_EKOSISTEM_OPEN_NVR_DAN_CCTV_HUB.md          <-- ONVIF Discovery, RTSP Matrix Wall, Vault & Bandwidth Gate
├── 📄 BAB_06_DASHBOARD_BUILDER_DAN_TELEMETRI.md          <-- No-Code Dashboard Designer, 24+ Widgets, Cross-Filter
├── 📄 BAB_07_MODEL_ZOO_DAN_QUANTIZATION.md               <-- Custom Weight Registry, ONNX Quantizer FP16/INT8, Face Gallery
├── 📄 BAB_08_INTEGRASI_API_MQTT_DAN_ERP.md               <-- REST API v1/v2, Webhook Ingestion, MQTT Broker, ERP Sync
├── 📄 BAB_09_EXPORT_CODE_DAN_EDGE_DEPLOYMENT.md          <-- Standalone Code Generator, Edge Jetson/IPC, Headless Runner
├── 📄 BAB_10_STUDI_KASUS_DAN_TUTORIAL_STEP_BY_STEP.md    <-- 5 Implementasi End-to-End Lapangan dari Nol
└── 📄 BAB_11_TROUBLESHOOTING_MAINTENANCE_FAQ.md          <-- Penanganan Masalah Lapangan, Profiling, Tuning & FAQ
```

---

## 📑 DAFTAR ISI LENGKAP (MASTER TABLE OF CONTENTS)

### BAGIAN I: PENGENALAN DAN ARSITEKTUR SISTEM
1. **Latar Belakang & Visi Produk**
   - Tantangan Vision AI di Lingkungan Operasional Nyata
   - Filosofi *Low-Code Node-Graph Architecture*
   - Paradigma *Zero Cloud Dependency* (Edge-Ready Architecture)
2. **Arsitektur Tingkat Tinggi (High-Level Architecture)**
   - Lapisan Antarmuka Pengguna (Web Studio, Dashboard Designer, OpenNVR Cockpit)
   - Lapisan Aplikasi & API Gateway (FastAPI / Asynchronous Event Loop)
   - Lapisan Komputasi Vision Core (Execution Runner: Threaded vs Serial Engine)
   - Lapisan Fleet Manager & Multi-Camera Orchestration
   - Lapisan Storage, Event Vault & Telemetry Bus
3. **Dataflow Pipeline & Siklus Eksekusi Node**
   - Struktur Objek Data Paket Frame (`VisionPacket`)
   - Mekanisme Propagasi Deteksi, Tracking ID, dan Metadata
   - Manajemen Buffer Frame, Zero-Copy Shared Memory, dan Dropping Rule
   - Diagram Alir Data End-to-End

---

### BAGIAN II: PANDUAN INSTALASI & LINGKUNGAN DEPLOYMENT
1. **Persyaratan Sistem Perangkat Keras & Lunak**
   - Konfigurasi Minimal vs Rekomendasi (CPU-Only vs GPU Acceleration)
   - Kompatibilitas Sistem Operasi (Ubuntu 22.04/24.04 LTS, Windows 10/11, Rocky Linux)
2. **Instalasi Bare-Metal Menggunakan Python Virtualenv**
   - Langkah Demi Langkah Instalasi Python 3.10 / 3.11
   - Setup Environment `.venv` dan Penanganan Konflik Wheel
   - Instalasi Dependensi Inti (`requirements.txt`)
   - Instalasi Ekstensi AI Tambahan (MediaPipe, PyTorch ReID, OCR, ONNX Runtime)
3. **Deployment Berbasis Docker & Docker Compose**
   - Struktur `Dockerfile` Multi-Stage Build
   - Konfigurasi `docker-compose.yml` untuk Produksi
   - Mapping Persistent Volume (`public/uploads`, `data/projects`, `data/models`, `data/vault`)
   - Menjalankan Container dengan Akses NVIDIA GPU Passthrough
4. **Konfigurasi Environment Variables (`.env`)**
   - Parameter Keamanan, Port Binding, Token AI Multimodal, dan Konfigurasi NVR
5. **Verifikasi Instalasi & Prosedur Health Check Otomatis**
   - Menjalankan Unit Test Terintegrasi
   - Pengujian Otomatis End-to-End (*Playwright Browser Verification*)
   - Memeriksa Endpoint `/api/health` dan `/api/status`

---

### BAGIAN III: WORKSPACE STUDIO & NAVIGASI ANTARMUKA PENGGUNA
1. **Projects Hub & Katalog Template**
   - Struktur Tampilan Beranda (*Projects Hub*)
   - Menavigasi 37+ Template Bawaan Siap Pakai
   - Manajemen Proyek: Buat Baru, Impor/Ekspor JSON, dan Duplikasi Instan
2. **Workflow Studio: Kanvas Interaktif**
   - Anatomi Kanvas: Infinite Panning, Semantic Zooming, Grid Snapping
   - Topbar Command Center: Play/Pause, Live FPS Counter, Restart Engine, Hot-Reload
   - Menambahkan dan Menghubungkan Node (Pin Input / Pin Output)
   - Validasi Topologi Graph & Pencegahan Circular Dependency
3. **Sidebar Palette & Pencarian Cerdas Node**
   - Struktur Kategori Node (Sources, Preprocessing, AI, Tracking, Logic, Drawing, Outputs)
   - Fuzzy Search Filter & Drag-and-Drop Node Placement
4. **Node Inspector & Drawer Konfigurasi Interaktif**
   - Pengaturan Parameter Dinamis (Numeric Slider, Dropdown, Textbox, Toggle Switch)
   - Real-time Config Propagation tanpa Mematikan Engine
5. **Full-Screen Calibration & Annotation Studio (CAD-Grade)**
   - Mode Layar Penuh 90vw untuk Kalibrasi Presisi Tinggi
   - Sub-Pixel Magnifier Loupe (Kaca Pembesar 3x)
   - Menggambar Polygon Bebas, ROI Rectangle, dan Garis Virtual
   - Penanganan Koordinat Normalisasi Letterbox Rasio Aspek
6. **Daftar Pintasan Keyboard (Keyboard Shortcuts & Hotkeys)**

---

### BAGIAN IV: ENSIKLOPEDIA LENGKAP SELURUH 98 NODE
*(Panduan Komprehensif: Spesifikasi Teknis, Pin Input/Output, Parameter Konfigurasi, Algoritma, dan Best Practice)*

1. **Bagian 4.1: Sources & Image Preprocessing (19 Nodes)**
   - *Sources:* `input`, `ip_camera`, `video_speed_controller`
   - *Preprocessing:* `auto_rotate_edges`, `background_subtract`, `blur_sharpen`, `brightness_contrast`, `camera_focus`, `color_convert`, `crop`, `delta_filter`, `frame_sampler`, `perspective`, `privacy_mask`, `python_script`, `resize`, `rotate_flip`, `slicer`, `undistort`
2. **Bagian 4.2: AI Vision Models (15 Nodes)**
   - `detector`, `classifier`, `segmenter`, `pose_detector`, `hand_skeleton`, `lpr_license_plate`, `ocr_reader`, `barcode_reader`, `efficientad`, `face_detector`, `face_analyzer`, `face_crop`, `detection_crop`, `model_comparison`, `ai_agent`
3. **Bagian 4.3: Tracking & Kinematic Analysis (25 Nodes)**
   - `tracker` (ByteTrack, BoT-SORT, C-BIoU, Roboflow ReID), `zone_activity_timer`, `zone_exit_event`, `multi_zone_occupancy`, `line_counter`, `object_counter`, `object_timer`, `dwell_time`, `overlap_analysis`, `detections_consensus`, `dominant_color`, `face_tracker`, `homography_projector`, `man_down_detector`, `overstack_detector`, `path_deviation`, `ppe_compliance_matrix`, `ptz_controller`, `size_measurement`, `distance_measurement`, `velocity_calculator`, `vlm_box_tracker`, `badminton_analytics`, `filter`, `track_snapshot`
4. **Bagian 4.4: Logic & Flow Control (15 Nodes)**
   - `motion_gate`, `debounce`, `alarm_cooldown_gate`, `switch_case`, `if_else`, `class_detected_condition`, `object_count_condition`, `compare_value`, `confidence_threshold`, `class_replacement`, `and_or_logic`, `rate_limiter`, `roi_filter`, `timer_delay`, `trigger_once`
5. **Bagian 4.5: Visualisasi, Drawing & Anotasi (7 Nodes)**
   - `overlay_annotate`, `draw_boxes`, `draw_text`, `blur_anonymizer`, `crowd_density_heatmap`, `bev_visualizer`, `interactive_zoom`
6. **Bagian 4.6: Outputs, Cloud Sinks & Code Export (17 Nodes)**
   - `preview`, `dashboard_sink`, `event_clip_recorder`, `incident_video_recorder`, `alert`, `image_output`, `database_output`, `mqtt_publisher`, `telegram_notification`, `notification_dispatcher`, `webhook_output`, `csv_formatter`, `data_aggregator`, `s3_sink`, `screenshot_capture`, `export_code`, `detections_difference`

---

### BAGIAN V: EKOSISTEM OPEN-NVR & CCTV HUB TERINTEGRASI
1. **Arsitektur Terpadu Open-NVR Hub**
   - Integrasi Dual-Engine: VMS Tradisional + In-line AI Processing
   - Protokol Streaming yang Didukung (RTSP, RTMP, HLS, WebRTC, ONVIF)
2. **Pencarian Kamera Otomatis (ONVIF WS-Discovery)**
   - Penemuan Kamera Jaringan Tanpa Konfigurasi Manual
   - Otentikasi Digest, Sinkronisasi Jam, dan Pengambilan RTSP URL Profil Utama/Kedua
3. **Pendaftaran Kamera Manual (Direct RTSP Connection)**
   - Format URL RTSP Berbagai Merek (Hikvision, Dahua, Uniview, Axis, Hanwha)
   - Konfigurasi Transport Protocol: TCP vs UDP Interleaved
4. **Manajemen Kamera Terdaftar & Status Pemantauan**
   - Layar Status Kamera: Latency, Resolution, Codec, Bitrate
   - Penanganan Otomatis Kondisi Offline: Frame Standby *CCTV NO SIGNAL*
5. **Matriks Live Video Wall**
   - Tata Letak Fleksibel: Single Cam, 2x2 Grid (4 Cam), 3x3 Grid (9 Cam), 1+5 Surveillance Grid
   - Fullscreen Monitoring Wall & Auto-Cycle Mode
6. **Evidence Vault (Brankas Klip Kejadian Forensik)**
   - Mekanisme Perekaman Pre-Roll & Post-Roll Berbasis Rolling Ring Buffer
   - Penguncian Metadata: Waktu Kejadian, Label Deteksi, ID Kamera, Skor Keyakinan
   - Pemutaran Klip Video & Ekspor Bukti MP4
7. **Motion Gate & Optimasi Bandwidth Jaringan**
   - Mencegah *CPU Overhead* dengan Analisis Gerak Ringan Sebelum Inference Berat
8. **Ekspor Mandiri Paket OpenNVR Edge Bundle**
   - Pengemasan VMS Standalone untuk Server Lapangan

---

### BAGIAN VI: DASHBOARD BUILDER & TELEMETRI ENTERPRISE
1. **Filosofi No-Code Visual Dashboard Designer**
   - Pemisahan Antara Logika Vision Pipeline dan Antarmuka Monitoring
   - Fleksibilitas Desain: Dark Aerospace Cockpit vs Light Operational Theme
2. **Katalog 24+ Komponen Widget Siap Pakai**
   - *Video Feeds:* Live Stream Canvas, Multi-CCTV Wall, Video Clip Replay
   - *Metrics & KPI:* Total Counter, Gauge Meter, Dwell Time Status, Occupancy Indicator
   - *Charts:* Real-time Time Series, Class Distribution Pie, Hourly Activity Bar Chart
   - *Event Logs:* Live Incident Feed, Data Table Virtualized, Snapshot Card
3. **Mekanisme Data Binding Menggunakan Dashboard Bus**
   - Arsitektur Pub/Sub WebSocket Real-time
   - Binding Variabel Output Node ke Parameter Widget
4. **Looker-Style Cross-Filtering Interaktif**
   - Interaktivitas Multi-Widget: Klik Bar Chart untuk Memfilter Tabel Kejadian
5. **Template Industri Bawaan**
   - Industrial Tire Workshop Dashboard
   - Warehouse Logistics & Truck Exit Portal
   - K3 Safety & Compliance Center
   - Smart Retail & Traffic Analytics
6. **Ekspor Dashboard Mandiri ke Docker Container**
   - Menghasilkan Kontainer Dashboard Standalone Tanpa Akses ke Studio Editor

---

### BAGIAN VII: MODEL ZOO, QUANTIZATION & CUSTOM RUNTIME
1. **Model Registry & Manajemen Bobot AI**
   - Struktur Direktori `weights/` dan Metadata Checksum SHA-256
   - Format Model yang Didukung: PyTorch (`.pt`), ONNX Runtime (`.onnx`), TensorRT Engine
2. **Dukungan YOLO Generasi Terbaru (YOLOv8, YOLO11, YOLO26n)**
   - Prosedur Download Resmi In-App & Idempotent Weight Storage
   - Model Khusus: Pose (`yolov8n-pose`), Segmentation (`yolov8n-seg`), Classification (`yolov8n-cls`)
3. **RF-DETR ONNX Runtime**
   - Arsitektur Transformer Detector Tanpa Non-Maximum Suppression (NMS)
4. **UniFace Enterprise Face Suite**
   - Deteksi Wajah, Landmark 5-Titik, Ekstraksi Feature Embedding, dan Face Attribute Analysis
   - Manajemen Galeri Wajah (Face Registry & Enrollment)
5. **EfficientAD Anomaly Inspection Runtime**
   - Deteksi Cacat Visual Tanpa Supervised Defect Dataset
6. **Model Quantizer Bawaan (FP32 ke FP16 / INT8)**
   - Konversi Otomatis Model ONNX untuk Efisiensi Memori & Kecepatan 3x Lipat pada CPU/Edge

---

### BAGIAN VIII: INTEGRASI SISTEM EKSTERNAL, MQTT & ENTERPRISE ERP
1. **REST API Gateway (OpenAPI / Swagger Spec)**
   - Autentikasi API Key & RBAC Token
   - Endpoint Kontrol Workflow, Status Proyek, dan Pengambilan Snapshot
2. **Webhook Event Ingestion & Outbound Dispatcher**
   - Format JSON Standar untuk Kejadian Vision
   - Pengiriman Bukti Gambar (Base64 vs URL Media)
   - Retry Policy dengan Exponential Backoff
3. **Konektivitas MQTT Industrial IoT**
   - Pengaturan Broker MQTT (Mosquitto, EMQX, HiveMQ)
   - Struktur Hierarki Topik (`cctv/site_id/camera_id/events`)
   - Quality of Service (QoS 0, QoS 1, QoS 2)
4. **Integrasi Bot Notifikasi Telegram**
   - Pembuatan Bot, Chat ID Grup, dan Template Pesan Darurat Beserta Foto Bukti
5. **Integrasi Basis Data Permanen (SQLite / PostgreSQL / TimescaleDB)**
   - Skema Tabel: Kejadian, Sesi Kerja, Deteksi Objek, Log Audit
6. **Antrean Kejadian ERP Enterprise & Deduplikasi**
   - Idempotency Key untuk Mencegah Pencatatan Ganda Transaksi Keluar Masuk Gudang

---

### BAGIAN IX: EXPORT CODE & DEPLOYMENT EDGE INDEPENDEN
1. **Arsitektur Code Generator (`export_code.py`)**
   - Mengubah Node-Graph Visual Menjadi Skrip Python Asli (`standalone_run.py`)
   - Keuntungan Ekspor: Headless Execution, Zero Web UI Overhead, Ultra-Low Latency
2. **Struktur Paket Unduhan Bundle ZIP**
   - `run.py` (Script Entrypoint)
   - `workflow_config.json` (Konfigurasi Pipeline Terkompresi)
   - `engine/` (Core Minimalis Python)
   - `requirements.txt` & `Dockerfile` Standalone
3. **Menjalankan Skrip Python Headless di Lingkungan Bersih**
   - Sintaks CLI: Parameter Input Kamera, Mode Headless, Log Output
4. **Deployment ke Edge Device (NVIDIA Jetson, Industrial IPC, Raspberry Pi)**
   - Optimasi Konsumsi Daya dan Pemanfaatan Hardware Acceleration (NVDEC / V4L2)

---

### BAGIAN X: PANDUAN LANGKAH DEMI LANGKAH: 5 STUDI KASUS NYATA
1. **Studi Kasus 1: Smart Workshop Bay Tracking (Estimasi Waktu Pekerjaan)**
   - *Tujuan:* Menghitung durasi riil mekanik bekerja pada ban alat berat per bay.
   - *Node yang Digunakan:* `ip_camera` -> `detector` -> `tracker` -> `zone_activity_timer` -> `overlay_annotate` -> `dashboard_sink` & `database_output`.
   - *Langkah Step-by-Step dari Nol hingga Verifikasi Telemetri.*
2. **Studi Kasus 2: Warehouse Gate Exit Surveillance & ERP Inventory Dispatch**
   - *Tujuan:* Mendeteksi ban/truk keluar dari gerbang gudang dan memicu transaksi ERP.
   - *Node yang Digunakan:* `ip_camera` -> `motion_gate` -> `detector` -> `lpr_license_plate` -> `zone_exit_event` -> `event_clip_recorder` -> `webhook_output`.
3. **Studi Kasus 3: K3 / K3LH Factory Safety & Fall Detection**
   - *Tujuan:* Memastikan APD lengkap (helm/rompi) dan mendeteksi pekerja jatuh pingsan.
   - *Node yang Digunakan:* `ip_camera` -> `pose_detector` -> `ppe_compliance_matrix` -> `man_down_detector` -> `alarm_cooldown_gate` -> `telegram_notification`.
4. **Studi Kasus 4: Retail Footfall & Smart Traffic Flow Analysis**
   - *Tujuan:* Menghitung volume perlintasan orang/kendaraan dengan homography planar.
   - *Node yang Digunakan:* `ip_camera` -> `detector` -> `tracker` -> `line_counter` -> `homography_projector` -> `crowd_density_heatmap` -> `csv_formatter`.
5. **Studi Kasus 5: Autonomous CCTV Copilot dengan Multimodal AI Agent (LLM)**
   - *Tujuan:* Melakukan penalaran logis situasional kejadian anomali menggunakan multimodal Vision LLM.
   - *Node yang Digunakan:* `ip_camera` -> `motion_gate` -> `detector` -> `ai_agent` -> `notification_dispatcher`.

---

### BAGIAN XI: TROUBLESHOOTING, PEMELIHARAAN & FAQ
1. **Diagnosa Masalah Jaringan & Streaming Kamera**
   - RTSP Frame Dropping, Smearing, Artefak H.264/H.265, dan Buffer Overflow
2. **Penanganan Masalah Performa & Pemakaian Sumber Daya**
   - Diagnosa Memory Leak, High CPU Usage, dan GPU Out of Memory (OOM)
   - Konfigurasi Dynamic FPS Governor
3. **Tuning dan Kalibrasi Akurasi Tracking & AI**
   - Mengatasi ID Switching pada Objek yang Bertumpukan (*Occlusion Handling*)
   - Memilih Algoritma: ByteTrack vs BoT-SORT vs Appearance ReID
4. **Pemeliharaan Sistem, Rotasi Log & Backup Basis Data**
   - Konfigurasi Retensi Rekaman Klip Bukti (*Evidence Vault Disk Management*)
   - Skrip Otomasi Pembersihan File Temporer
5. **Daftar Tanya Jawab Kritis (FAQ Operasional)**

---

*Mari kita mulai dengan mempelajari **Bagian I: Pengenalan dan Arsitektur Sistem**.*
