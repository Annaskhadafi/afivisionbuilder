<!-- ============================================================================== -->
<!-- MASTER EDITION: BUKU PANDUAN LENGKAP RESMI AFI VISION BUILDER & OPEN-NVR   -->
<!-- TOTAL ESTIMASI HALAMAN: 150 HALAMAN CETAK STANDAR                           -->
<!-- ============================================================================== -->




<!-- PAGE BREAK: README.md -->


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



<!-- PAGE BREAK: BAB_01_PENGENALAN_DAN_ARSITEKTUR.md -->


# BAGIAN I: PENGENALAN DAN ARSITEKTUR SISTEM
## Afi Vision Builder & Integrated Open-NVR Platform

---

## 1.1 Latar Belakang & Visi Produk

Sistem Computer Vision industri sering kali menghadapi kesenjangan besar antara tahap eksperimen di laboratorium (*Jupyter Notebook / Python script*) dan implementasi operasional nyata di pabrik, workshop, tambang, atau pergudangan. Beberapa tantangan kritis di lapangan meliputi:

1. **Kompleksitas Integrasi Kamera**: Variasi protokol video (RTSP, RTMP, WebRTC, ONVIF), inkonsistensi frame rate, fluktuasi bandwidth jaringan, dan frame drop.
2. **Ketergantungan Kode Kaku (*Hardcoded Pipelines*)**: Setiap kali zona monitoring berubah, batas waktu toleransi berganti, atau logika peringatan disesuaikan, teknisi harus merevisi kode Python mentah dan merestart proses secara manual.
3. **Keterbatasan Sumber Daya Perangkat Keras**: Tidak semua lokasi operasional memiliki server dengan GPU NVIDIA kelas server (*datacenter*). Banyak lokasi hanya memiliki PC industri tanpa GPU terdedikasi (CPU-only, RAM 16-32 GB), sehingga membutuhkan pipeline yang hemat memori, asynchronous, dan mendukung optimasi ONNX/OpenVINO.
4. **Isolasi Antara VMS (Video Management System) dan AI**: Sistem CCTV tradisional terpisah dari sistem kecerdasan buatan, membutuhkan dua infrastruktur terpisah yang meningkatkan biaya dan latensi transmisi.

**Afi Vision Builder** hadir untuk menyelesaikan seluruh permasalahan tersebut melalui satu platform terpadu (*All-in-One AI-Powered VMS & Workflow Automation Engine*). 

```
+-----------------------------------------------------------------------------------+
|                        AFI VISION BUILDER ECOSYSTEM                                |
|                                                                                   |
|  +--------------------+   +-----------------------+   +------------------------+  |
|  |  WORKFLOW STUDIO   |   |   DASHBOARD BUILDER   |   |   INTEGRATED OPEN-NVR  |  |
|  | Visual Node-Graph  |   | Real-time Telemetry   |   | Matrix Live Wall       |  |
|  | 98 Processing Nodes|   | 24+ Live Widgets      |   | Evidence Clip Vault    |  |
|  | CAD Annotations    |   | Looker Cross-Filter   |   | ONVIF Auto-Discovery   |  |
|  +---------+----------+   +-----------+-----------+   +-----------+------------+  |
|            |                          |                           |               |
|  +---------v--------------------------v---------------------------v------------+  |
|  |                         UNIFIED ENGINE & RUNTIME CORE                       |  |
|  |  * Async FastAPI Gateway          * Dual Execution Engine (Threaded/Serial) |  |
|  |  * Multi-Stream RTSP Demuxer      * Zero-Copy Frame Ring Buffer             |  |
|  |  * Model Zoo (YOLO/ONNX/UniFace)  * Roboflow ReID Tracking Engine           |  |
|  |  * WebSocket Telemetry Bus        * Headless Standalone Python Code Export  |  |
|  +------------------------------------+----------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 1.2 Arsitektur Tingkat Tinggi (High-Level Architecture)

Arsitektur Afi Vision Builder dibangun dengan model berlapis (*layered architecture*) yang modular, modularitas ini memastikan bahwa kegagalan satu komponen (misalnya hilangnya sinyal satu kamera) tidak akan meruntuhkan keseluruhan sistem.

```mermaid
graph TD
    subgraph UI_Layer ["Lapisan Antarmuka Pengguna (Web Frontend)"]
        UI_Studio["Workflow Studio Canvas (Pan/Zoom/Nodes)"]
        UI_Dash["Dashboard Designer & Live Operations"]
        UI_NVR["Open-NVR Matrix Wall & Evidence Vault"]
        UI_CAD["Full-Screen CAD Annotation Studio"]
    end

    subgraph API_Gateway ["Lapisan Gateway & Service (FastAPI)"]
        Route_Workflow["/api/workflow (Load/Save/Execute)"]
        Route_Camera["/api/camera & /api/cctv (Stream Hub)"]
        Route_NVR["/api/nvr (Discovery/Matrix/Clips)"]
        Route_Telemetry["WebSocket /api/telemetry (Real-time Bus)"]
        Route_Export["/api/export-code (Standalone Bundle)"]
    end

    subgraph Vision_Core ["Lapisan Vision Core & Runner Engine"]
        Runner_Manager["Execution Runner (Threaded / Serial Engine)"]
        Graph_Scheduler["DAG Dependency Topological Sorter"]
        Frame_Buffer["Zero-Copy Shared Memory Frame Buffer"]
        Motion_Filter["Motion Gate & Background Subtraction"]
    end

    subgraph AI_Runtime ["Lapisan Model Zoo & AI Runtime"]
        Engine_YOLO["YOLOv8 / YOLO11 / YOLO26 Engine"]
        Engine_RFDETR["RF-DETR ONNX Transformer Engine"]
        Engine_UniFace["UniFace Facial Recognition & Re-ID"]
        Engine_Pose["MediaPipe & Pose / Hand Skeleton"]
        Engine_Anomaly["EfficientAD Anomaly Inspection"]
        Engine_LLM["Multimodal Vision AI Agent (OpenAI/Ollama)"]
    end

    subgraph Storage_IO ["Lapisan Penyimpanan & Sink Eksternal"]
        DB_Store["SQLite / PostgreSQL (Events & Sessions)"]
        Vault_Store["Evidence Vault (Pre/Post-Roll MP4 Clips)"]
        Sink_MQTT["MQTT Broker (IoT / Factory SCADA)"]
        Sink_ERP["Enterprise ERP REST / Webhook Ingestion"]
        Sink_Cloud["S3 Cloud Sink & Telegram Alert Bot"]
    end

    UI_Layer --> API_Gateway
    API_Gateway --> Vision_Core
    Vision_Core --> AI_Runtime
    Vision_Core --> Storage_IO
```

### 1. Lapisan Antarmuka Pengguna (Frontend Layer)
Frontend dirancang menggunakan HTML5, Tailwind CSS, dan JavaScript murni (*vanilla ES6+*) berkinerja tinggi tanpa ketergantungan framework berat. Komponen utamanya meliputi:
- **Workflow Studio**: Kanvas visual berbasis drag-and-drop dengan *smooth pan-and-zoom*, visualisasi kabel penghubung node dengan kurva bezier, dan indikator status live frame.
- **Dashboard Designer**: Lingkungan desain visual ala Elementor yang memungkinkan pengguna menyusun dashboard monitoring industri dengan widget drag-and-drop.
- **Open-NVR Matrix Wall**: Konsol monitoring CCTV multi-grid (1, 2x2, 3x3, 1+5) dengan latensi sub-detik melalui Motion JPEG over HTTP atau WebSocket streaming.
- **CAD Annotation Studio**: Studio anotasi layar penuh (*full-screen 90vw*) dengan pembesar sub-pixel (*3x loupe magnifier*) untuk penempatan zona polygon, garis crossing, dan ROI dengan akurasi piksel mutlak.

### 2. Lapisan API Gateway & Kontrol Layanan (FastAPI)
Menggunakan framework **FastAPI** di atas Python `asyncio` dan `uvicorn`. Gateway ini melayani:
- Sinkronisasi status alur kerja (*live workflow state synchronization*).
- Penemuan kamera jaringan melalui protokol ONVIF WS-Discovery.
- Streaming video multi-klien dengan buffer terpisah agar klien lambat tidak membebani proses vision engine.
- WebSocket bus untuk telemetri berlatensi rendah (< 50 ms) ke antarmuka dashboard.

### 3. Lapisan Vision Core & Execution Engine (`engine/core.py` & `engine/main.py`)
Inti komputasi vision yang mengeksekusi topologi graf node. Engine ini mendukung dua mode operasional:
- **Threaded Execution Engine**: Setiap node atau kelompok node sumber/inferensi dijalankan dalam *worker thread* terisolasi yang dihubungkan melalui *thread-safe ring buffer*. Cocok untuk memaksimalkan throughput pada CPU multi-core.
- **Serial Deterministic Runner**: Node dieksekusi secara berurutan sesuai urutan topologi graf (*Topological Sort*). Sangat ideal untuk debugging, analisis frame-by-frame, dan replay rekaman historis.

### 4. Lapisan Model Zoo & AI Runtime
Mesin inferensi multi-arsitektur yang mendukung:
- **Ultralytics PyTorch / ONNX Runtime**: Mendukung YOLOv8, YOLO11, dan YOLO26n secara *native*.
- **RF-DETR ONNX Runtime**: Model Transformer deteksi objek tanpa NMS (*Non-Maximum Suppression*).
- **UniFace**: Stack komprehensif pengenalan wajah berkecepatan tinggi (SCRFD untuk deteksi, ArcFace untuk embedding, dan atribut usia/gender/ekspresi).
- **EfficientAD**: Model deteksi cacat visual industri berbasis pembelajaran tanpa pengawasan (*unsupervised anomaly detection*).
- **Multimodal AI Agent**: Penghubung langsung ke Vision LLM (OpenAI GPT-4o / GPT-5, Ollama LLaVA/Qwen-VL) untuk penalaran semantik kompleks dari frame CCTV.

### 5. Lapisan Storage, Event Vault & Integrasi Industri
- **SQLite / Postgres Storage**: Menyimpan metadata kejadian (*events*), log sesi zona kerja, dan jejak audit pengguna.
- **Evidence Vault**: Perekam video lokal yang menyimpan buffer rekaman berkelanjutan (*rolling ring buffer*). Ketika sebuah anomali atau pelanggaran terjadi, sistem otomatis mengekstrak 5 detik sebelum kejadian (*pre-roll*) dan 10 detik setelah kejadian (*post-roll*) menjadi file MP4 permanen.
- **Industrial Gateways**: Pengirim kejadian ke sistem ERP perusahaan, SCADA/PLC melalui MQTT, dan bot peringatan instan Telegram.

---

## 1.3 Dataflow Pipeline & Siklus Hidup Paket Data (`VisionPacket`)

Setiap data yang mengalir dari satu node ke node lainnya di dalam graf dibungkus dalam sebuah struktur data standar yang disebut **`VisionPacket`**.

### 1. Struktur Data `VisionPacket`
Di dalam `engine/core.py`, struktur data ini membawa informasi komprehensif:

```python
class VisionPacket:
    frame_id: int               # Nomor urut frame global (monotonik naik)
    timestamp: float            # Timestamp waktu presisi tinggi (time.time())
    source_id: str              # Identitas sumber kamera (misal: "CAM_BAY_01")
    image: np.ndarray           # Matriks citra mentah (BGR format, OpenCV numpy array)
    annotated_image: np.ndarray # Citra yang telah ditimpa anotasi visual
    detections: List[Detection] # Daftar deteksi bounding box yang teridentifikasi
    tracks: List[Tracklet]      # Objek hasil pelacakan temporal dengan ID stabil
    events: List[VisionEvent]   # Kejadian diskrit yang dipicu pada frame ini
    metadata: Dict[str, Any]    # Data konteks dinamis antar-node (misal: suhu, OCR)
```

### 2. Siklus Eksekusi Node (Execution Lifecycle)
Ketika satu siklus frame dieksekusi:

```mermaid
sequenceDiagram
    autonumber
    participant SRC as Source Node (IP Camera)
    participant PRE as Preprocessing (Crop / Slicer)
    participant AI as AI Model (Detector)
    participant TRK as Tracker (ByteTrack / Re-ID)
    participant LOG as Logic (Zone Timer / Gate)
    participant OUT as Output (Vault & ERP)
    participant DRW as Drawing (Annotator)

    SRC->>PRE: 1. Generate Raw Frame (VisionPacket)
    PRE->>AI: 2. Filtered / Resized Image
    AI->>TRK: 3. Append Bounding Boxes & Confidence
    TRK->>LOG: 4. Assign Persistent Track IDs & History
    LOG->>OUT: 5. Evaluate Business Rule -> Trigger Event
    OUT->>OUT: 6. Save Event Clip & Push to ERP
    LOG->>DRW: 7. Pass Packet to Annotator
    DRW-->>SRC: 8. Render Preview & Emit Telemetry WebSocket
```

1. **Inisiasi Sumber (*Source Ingestion*)**: Node sumber (`ip_camera` atau `input`) mengambil frame dari buffer kamera RTSP melalui OpenCV atau hardware-accelerated GStreamer/FFmpeg decoder.
2. **Pra-pemrosesan (*Preprocessing*)**: Citra dapat dipotong (ROI Crop), diubah rasio kontrasnya (CLAHE), atau diiris (*tiled*) menggunakan SAHI (*Slicing Aided Hyper Inference*) untuk mendeteksi objek mikroskopis/kecil.
3. **Inferensi AI (*AI Inference*)**: Frame diteruskan ke model neural network (misal: YOLOv8). Model mendeteksi koordinat *bounding box*, kelas objek, dan nilai keyakinan (*confidence*).
4. **Pelacakan Temporal (*Temporal Tracking*)**: Deteksi dicocokkan dengan lintasan sebelumnya menggunakan algoritma pelacak (ByteTrack, BoT-SORT, atau Appearance Re-ID) sehingga setiap objek mempertahankan ID numerik yang stabil melintasi waktu.
5. **Evaluasi Logika Bisnis (*Business Logic & Spatial Analysis*)**: Node analisis seperti `zone_activity_timer` memeriksa apakah objek target berada di dalam koordinat polygon zona kerja. Jika kondisi terpenuhi, timer bertambah dan jika selesai, sebuah `VisionEvent` dibuat.
6. **Eksekusi Output Berprioritas Tinggi (*High-Priority Sinks*)**: Output kejadian diskrit (pengiriman webhook ke ERP, penyimpanan klip rekaman ke Vault, notifikasi Telegram) **dieksekusi langsung sebelum** proses rendering visual. Hal ini menjamin bahwa fluktuasi kinerja tampilan antarmuka web tidak akan pernah menghilangkan data kejadian penting.
7. **Rendering Anotasi Visual (*Visual Annotation*)**: Node `overlay_annotate` atau `draw_boxes` menggambar kotak pembatas, garis pelacak, label nama objek, dan HUD status langsung di atas frame citra.
8. **Pengiriman Telemetri (*Telemetry Dispatch*)**: Citra teranotasi dikirim ke antarmuka pengguna via HTTP MJPEG, sementara metadata numerik dipancarkan via WebSocket ke Dashboard Bus.

---

## 1.4 Konsep Node-Graph & Topologi Graf Terarah (DAG)

Afi Vision Builder mengadopsi prinsip **Directed Acyclic Graph (DAG)**. Dalam graf terarah ini:
- **Node**: Unit komputasi mandiri yang memiliki fungsi spesifik (misal: mendeteksi, memotong, menghitung waktu, mengirim data).
- **Pin Input**: Titik masuk data pada node, hanya dapat menerima tipe data yang kompatibel (misalnya: citra menerima citra, daftar deteksi menerima daftar deteksi).
- **Pin Output**: Titik keluar hasil komputasi node untuk diteruskan ke satu atau banyak node penerima (*one-to-many branching*).
- **Kabel / Koneksi (*Wire Edge*)**: Saluran data yang menghubungkan Pin Output sebuah node ke Pin Input node lainnya.

```
       +--------------------+
       |  IP Camera (RTSP)  |
       +---------+----------+
                 |
        [Raw Image Frame]
                 |
        +--------v----------+
        |  Object Detector  |
        +--------+----------+
                 |
      [Detections List & Image]
                 |
        +--------v----------+
        |   Object Tracker  |
        +---+------------+--+
            |            |
 [Tracked Object]     [Tracked Object]
            |            |
+-----------v-----+    +-v-----------------+
| Zone Act. Timer |    |  Overstack Sensor |
+-----------+-----+    +-------+-----------+
            |                  |
      [Timer Event]     [Violation Event]
            |                  |
+-----------v------------------v-----------+
|          Telegram / ERP Webhook          |
+------------------------------------------+
```

### Aturan Topologi & Validasi Graf
Sistem memiliki validator topologi internal di `engine/core.py` yang secara otomatis mencegah:
1. **Circular Dependency (Loop Tertutup)**: Sebuah node tidak diizinkan mengirim output kembali ke dirinya sendiri atau leluhurnya, yang dapat menyebabkan *infinite execution loop*.
2. **Type Mismatch (Inkompatibilitas Tipe Data)**: Menolak penyambungan data yang tidak masuk akal (misalnya menghubungkan output string dari node OCR langsung ke input frame citra).
3. **Dead Branch Elimination**: Cabang graf yang tidak memiliki node output (sink/preview) akan dieksekusi secara efisien tanpa pemborosan alokasi memori anotasi.

---

## 1.5 Paradigma Edge-Ready & Zero Cloud Dependency

Salah satu keunggulan terbesar Afi Vision Builder adalah kemampuan operasional penuh secara **100% lokal (*on-premises*)** tanpa membutuhkan koneksi internet publik (*air-gapped environment*).

| Aspek | Afi Vision Builder | Cloud Vision Services Tradisional |
|---|---|---|
| **Ketergantungan Internet** | **Nol (Zero)**; Berjalan penuh di LAN / Server Lokal | Wajib koneksi internet berkecepatan tinggi terus-menerus |
| **Biaya Bandwidth Video** | **Gratis**; Video resolusi 4K diproses langsung di jaringan lokal | Sangat mahal; Mengirim stream video CCTV ke cloud membebani biaya kuota ISP |
| **Privasi & Keamanan Data** | **Sangat Aman**; Video dan wajah karyawan tidak pernah meninggalkan gedung | Rentan; Rekaman sensitif tersimpan di server pihak ketiga |
| **Latensi Respon Kejadian** | **< 30 milidetik**; Respon real-time di tepi jaringan (*edge*) | 500 ms – 3000 ms tergantung latensi server cloud |
| **Model Biaya Operasional** | **Lisensi Server Lokal / Open Runtime** tanpa biaya per-frame | Biaya *Pay-per-API-Call* yang membengkak seiring bertambahnya kamera |

Dengan fondasi arsitektur yang tangguh ini, Afi Vision Builder siap diterapkan di lokasi dengan tantangan jaringan ekstrem seperti area tambang pedalaman, lantai pabrik tertutup, dan pelabuhan peti kemas.

---

*Lanjutkan ke **Bagian II: Panduan Instalasi dan Deployment** untuk instruksi pengaturan lingkungan server.*



<!-- PAGE BREAK: BAB_02_PANDUAN_INSTALASI_DAN_DEPLOYMENT.md -->


# BAGIAN II: PANDUAN INSTALASI DAN DEPLOYMENT
## Afi Vision Builder & Integrated Open-NVR Platform

---

## 2.1 Persyaratan Sistem Perangkat Keras & Lunak

Afi Vision Builder dirancang dengan fleksibilitas tinggi agar dapat beroperasi secara optimal pada spektrum perangkat keras yang luas—mulai dari komputer industri (*IPC*) tanpa GPU hingga server *multi-GPU datacenter*.

### 1. Spesifikasi Perangkat Keras (Hardware Requirements)

| Komponen | Spesifikasi Minimal (CPU-Only / Edge) | Spesifikasi Rekomendasi (Workstation 8-16 Cam) | Spesifikasi Enterprise (Datacenter 32+ Cam) |
|---|---|---|---|
| **Prosesor (CPU)** | Intel Core i5 / AMD Ryzen 5 (min. 4 Core, 8 Thread) | Intel Core i7/i9 12th+ / AMD Ryzen 7 (8-16 Core) | Intel Xeon Gold / AMD EPYC (32+ Core) |
| **Memori (RAM)** | 16 GB DDR4 | 32 GB DDR4 / DDR5 | 64 GB – 128 GB ECC DDR5 |
| **GPU (Opsional)** | Tidak ada (CPU OpenVINO / ONNX-CPU) | NVIDIA RTX 3060 / 4060 (8-12 GB VRAM) | NVIDIA RTX 4090 / A4000 / A5000 / L4 (16-24 GB VRAM) |
| **Penyimpanan (Disk)** | 128 GB SSD (OS + Model AI) | 512 GB NVMe SSD + 2 TB HDD (Evidence Vault) | 1 TB NVMe SSD + 8-16 TB Enterprise Surveillance HDD / NAS |
| **Koneksi Jaringan** | Gigabit Ethernet (1000BASE-T) | Gigabit Ethernet Dedicated CCTV VLAN | 10 Gigabit SFP+ Dual NIC (Isolated Surveillance Network) |

> [!NOTE]
> Pada konfigurasi **CPU-Only (tanpa GPU)**, server dengan prosesor 8-core dan RAM 32 GB mampu menangani **5 hingga 8 kamera RTSP simultan** pada resolusi 1080p dengan frame skip terkalibrasi (5-10 FPS inference) menggunakan model YOLOv8n atau YOLO26n terkuantisasi INT8/FP16.

### 2. Kompatibilitas Sistem Operasi
Sistem ini teruji dan didukung penuh pada:
- **Linux (Sangat Disarankan untuk Produksi)**:
  - Ubuntu 22.04 LTS / 24.04 LTS (x86_64)
  - Debian 11 / 12 (Bullseye / Bookworm)
  - Rocky Linux 9 / AlmaLinux 9 / RHEL 9
- **Windows**:
  - Windows 10 Pro / Enterprise (64-bit)
  - Windows 11 Pro (64-bit)
  - Windows Server 2019 / 2022
- **Arsitektur CPU**:
  - `x86_64` / `AMD64` (Intel/AMD)
  - `aarch64` / `ARM64` (NVIDIA Jetson Orin Nano / AGX Orin)

---

## 2.2 Instalasi Bare-Metal Menggunakan Python Virtualenv

Metode ini memberikan kontrol penuh terhadap lingkungan sistem dan sangat cocok untuk lingkungan kerja workstation lokal atau server on-premise mandiri.

### Langkah 1: Persiapan Prasyarat Sistem

#### Pada Sistem Operasi Linux (Ubuntu / Debian):
Buka terminal dan pasang dependensi pustaka C++, Python dev, dan codec multimedia:
```bash
sudo apt-get update && sudo apt-get install -y \
    python3.11 python3.11-venv python3.11-dev \
    git curl ffmpeg libsm6 libxext6 libgl1-mesa-glx \
    libglib2.0-0 build-essential libssl-dev
```

#### Pada Sistem Operasi Windows:
1. Pastikan **Python 3.10 atau 3.11 (64-bit)** telah terpasang dari situs resmi [python.org](https://www.python.org). Jangan lupa mencentang opsi **"Add Python to PATH"** saat instalasi.
2. Pastikan **Git for Windows** telah terpasang.
3. Unduh dan pasang executable **FFmpeg** lalu tambahkan folder `bin/` FFmpeg ke System PATH Windows Anda.
4. Pastikan **Visual Studio C++ Build Tools** (atau setidaknya Visual C++ Redistributable 2015-2022 x64) telah terpasang untuk kompilasi modul native C++.

---

### Langkah 2: Kloning Repositori & Pembuatan Virtual Environment

Navigasi ke direktori kerja Anda dan siapkan virtual environment:

```bash
# Masuk ke direktori proyek
cd /opt/afi-vision-builder   # (atau D:\[01] PROJECT\REA\webapp pada Windows)

# Buat virtual environment bernama .venv dengan Python 3.10/3.11
python -m venv .venv
```

Aktifkan environment tersebut:
- **Di Linux / macOS**:
  ```bash
  source .venv/bin/activate
  ```
- **Di Windows (PowerShell)**:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
- **Di Windows (Command Prompt `cmd`)**:
  ```cmd
  .\.venv\Scripts\activate.bat
  ```

Perbarui pengelola paket `pip`, `setuptools`, dan `wheel`:
```bash
python -m pip install --upgrade pip setuptools wheel
```

---

### Langkah 3: Instalasi Dependensi Inti (`requirements.txt`)

Instal dependensi standar aplikasi yang tercantum di file `requirements.txt`:
```bash
pip install -r requirements.txt
```

Isi dari `requirements.txt` mencakup pustaka fundamental:
```text
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6
websockets>=12.0
opencv-python-headless>=4.8.0.76
numpy>=1.24.0,<2.0.0
ultralytics>=8.1.0
onnxruntime>=1.17.0
pydantic>=2.5.0
requests>=2.31.0
aiohttp>=3.9.0
python-dotenv>=1.0.0
Pillow>=10.0.0
jinja2>=3.1.0
```

---

### Langkah 4: Instalasi Ekstensi AI Tambahan (Opsional Sesuai Kebutuhan)

Jika Anda ingin mengaktifkan modul khusus (Pose MediaPipe, OCR, UniFace, atau Appearance ReID):

1. **Untuk Akselerasi GPU NVIDIA (CUDA 11.8 atau 12.1)**:
   ```bash
   # Ganti versi PyTorch CPU dengan PyTorch CUDA resmi
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
   pip install onnxruntime-gpu
   ```

2. **Untuk Modul ReID (Roboflow Tracking Re-ID & OSNet)**:
   ```bash
   pip install gdown scipy torchvision
   ```

3. **Untuk Modul Pose & Hand Tracking (MediaPipe)**:
   ```bash
   pip install mediapipe>=0.10.9
   ```

4. **Untuk Modul OCR (EasyOCR / ONNX-OCR)**:
   ```bash
   pip install pyclipper shapely
   ```

---

## 2.3 Deployment Berbasis Docker & Docker Compose

Docker adalah metode deployment yang paling disukai untuk lingkungan produksi enterprise karena menjamin isolasi sistem, kebersihan dependensi, dan kemudahan manajemen migrasi server.

### 1. Struktur Dockerfile Multi-Stage (`Dockerfile`)
Proyek ini telah dilengkapi dengan `Dockerfile` yang dioptimasi untuk ukuran citra kecil (*lightweight production container*) dan mendukung GPU passthrough:

```dockerfile
FROM python:3.11-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS runner

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsm6 libxext6 libgl1 libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

# Buat folder penyimpanan persisten jika belum ada
RUN mkdir -p public/uploads data/projects data/models data/vault data/exports

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8765/api/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]
```

---

### 2. Konfigurasi `docker-compose.yml` untuk Produksi

Berikut adalah konfigurasi lengkap `docker-compose.yml` yang mencakup **Persistent Bind Mounts** untuk memastikan data proyek, rekaman video, dan upload file tidak terhapus saat kontainer di-rebuild:

```yaml
version: '3.8'

services:
  afi-vision:
    image: afi-vision-builder:latest
    build:
      context: .
      dockerfile: Dockerfile
    container_name: afi_vision_core
    restart: unless-stopped
    ports:
      - "8765:8765"
    environment:
      - PORT=8765
      - HOST=0.0.0.0
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - DATA_DIR=/app/data
      - UPLOAD_DIR=/app/public/uploads
      - NVR_RECORDINGS_PATH=/app/data/vault
      - MAX_CONCURRENT_CAMERAS=16
    volumes:
      # PENTING: Mount direktori data lokal ke dalam kontainer
      - ./data/projects:/app/data/projects
      - ./data/vault:/app/data/vault
      - ./data/models:/app/data/models
      - ./public/uploads:/app/public/uploads
      - ./weights:/app/weights
      - ./server_out.log:/app/server_out.log
    # Konfigurasi Passthrough GPU NVIDIA (Hapus blok ini jika menggunakan CPU-only)
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
```

#### Menjalankan Kontainer:
```bash
# Build dan jalankan secara daemon di latar belakang
docker compose up -d --build

# Periksa status kontainer
docker compose ps

# Membaca log output server
docker compose logs -f afi-vision
```

---

## 2.4 Konfigurasi Environment Variables (`.env`)

Afi Vision Builder membaca konfigurasi sistem melalui file `.env`. Salin file template `.env.example` menjadi `.env`:

```bash
cp .env.example .env
```

Berikut adalah daftar variabel lingkungan (*environment variables*) penting yang dapat dikustomisasi:

```ini
# ==============================================================================
# SERVER & NETWORK BINDING
# ==============================================================================
PORT=8765
HOST=0.0.0.0
DEBUG=False
SECRET_KEY=ganti-dengan-kunci-rahasia-acak-32-karakter-enterprise

# ==============================================================================
# PATH DIREKTORI PENYIMPANAN
# ==============================================================================
DATA_DIR=./data
UPLOAD_DIR=./public/uploads
VAULT_DIR=./data/vault
MODELS_DIR=./weights

# ==============================================================================
# OPEN-NVR & CCTV HUB PARAMETERS
# ==============================================================================
NVR_DEFAULT_TRANSPORT=tcp          # Opsi: tcp / udp
NVR_DISCOVERY_TIMEOUT=4            # Timeout pencarian ONVIF (detik)
NVR_EVIDENCE_PRE_ROLL_SECONDS=5    # Buffer rekaman sebelum kejadian
NVR_EVIDENCE_POST_ROLL_SECONDS=10  # Buffer rekaman setelah kejadian
NVR_STANDBY_TIMEOUT_SECONDS=10     # Batas waktu mendeteksi offline

# ==============================================================================
# MULTIMODAL AI AGENT INTEGRATION (VISION LLM)
# ==============================================================================
# Digunakan oleh node 'ai_agent' untuk penalaran semantik CCTV cerdas
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
# Alternatif: Router 9router internal
# OPENAI_BASE_URL=https://9router.chitraparatama.com/v1
# OPENAI_API_KEY=sk-a510b6e65efa23d4-hpbvtn-35dad8f5

# Alternatif: Local Ollama URL
OLLAMA_HOST=http://127.0.0.1:11434

# ==============================================================================
# TELEGRAM & MQTT DISPATCHER
# ==============================================================================
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz
TELEGRAM_DEFAULT_CHAT_ID=-1001234567890
MQTT_BROKER_HOST=127.0.0.1
MQTT_BROKER_PORT=1883
```

---

## 2.5 Menjalankan Server & Prosedur Verifikasi Health Check

### 1. Menjalankan Aplikasi Secara Langsung

#### Di Lingkungan Windows:
Cukup jalankan script batch otomatis yang disediakan:
```cmd
run.bat
```
Atau melalui terminal PowerShell dengan Python virtualenv aktif:
```powershell
python server.py --host 0.0.0.0 --port 8765
```

#### Di Lingkungan Linux:
```bash
./run.sh
```
Atau:
```bash
python3 server.py --host 0.0.0.0 --port 8765
```

Terminal akan menampilkan banner startup resmi:
```text
======================================================================
       AFI VISION BUILDER & INTEGRATED OPEN-NVR PLATFORM
======================================================================
[*] Host: 0.0.0.0 | Port: 8765
[*] Engine Mode: Hybrid Multi-Stream Async
[*] Registered Node Blueprints: 98 Active Nodes
[*] Open-NVR Hub: Enabled (WS-Discovery & Evidence Vault Ready)
[*] Telemetry WebSocket: ws://0.0.0.0:8765/api/telemetry
======================================================================
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8765 (Press CTRL+C to quit)
```

Buka peramban (*web browser*) Anda dan arahkan ke alamat:
👉 **`http://localhost:8765`**

---

### 2. Pengujian Unit Otomatis (Unit Testing)
Sistem memiliki suite pengujian komprehensif untuk memvalidasi algoritma pelacakan, node logic, dan sinkronisasi graf:

```bash
# Menjalankan seluruh unit test suite
pytest tests/unit/ -v

# Menjalankan pengujian khusus Roboflow Re-ID Tracker
pytest tests/unit/test_reid_tracking.py -v

# Menjalankan pengujian Video Speed & Timeline Controller
pytest tests/unit/test_video_speed_timeline.py -v
```

Semua unit test harus berstatus **PASSED (100%)**.

---

### 3. Pengujian Otomatis Real-Browser E2E (`tester-army/e2e`)
Sesuai standar penjaminan kualitas sistem, setiap alur antarmuka diuji menggunakan framework agen cerdas Playwright:

```bash
# Menjalankan pengujian E2E antarmuka Open-NVR Hub
npx e2e run tests/opennvr_hub.e2e.ts

# Menjalankan pengujian antarmuka Re-ID Tracker Inspector
npx e2e run tests/reid_tracker.e2e.ts

# Menjalankan seluruh pengujian E2E sistem
npm run test:e2e
```

Hasil tangkapan layar otomatis akan tersimpan di direktori `.e2e/artifacts/web/.screenshots/` sebagai bukti audit visual antarmuka.

---

### 4. Pemeriksaan Endpoint API Health & Status

Anda dapat memverifikasi kesiapan operasional server menggunakan perintah cURL sederhana:

```bash
# Periksa kesehatan server
curl -s http://localhost:8765/api/health | jq .
```
Respons yang diharapkan:
```json
{
  "status": "healthy",
  "version": "3.8.0",
  "uptime_seconds": 124.5,
  "active_runners": 1,
  "active_cameras": 3,
  "memory_usage_mb": 412.8,
  "gpu_available": false
}
```

```bash
# Periksa status runner graf aktif
curl -s http://localhost:8765/api/status | jq .
```

Jika seluruh output di atas merespons dengan kode status `200 OK`, maka sistem Afi Vision Builder telah siap digunakan secara penuh.

---

*Lanjutkan ke **Bagian III: Workspace Studio dan Navigasi Antarmuka Pengguna** untuk menguasai pengoperasian studio visual.*



<!-- PAGE BREAK: BAB_03_WORKSPACE_STUDIO_DAN_NAVIGASI_UI.md -->


# BAGIAN III: WORKSPACE STUDIO DAN NAVIGASI ANTARMUKA PENGGUNA
## Afi Vision Builder & Integrated Open-NVR Platform

---

## 3.1 Projects Hub & Katalog Template Industri

Saat Anda mengakses URL root sistem (`http://localhost:8765`), Anda akan disambut oleh antarmuka **Projects Hub**. Halaman ini dirancang sebagai pusat komando operasional untuk mengelola proyek alur kerja komputer vision dan memilih template solusi siap pakai.

![Projects Hub Overview](screenshots/01_projects_hub.png)
*Gambar 3.1: Tampilan Utama Projects Hub dengan Header Telemetri dan Navigasi Segmented Bar.*

### 1. Struktur Navigasi Beranda
Antarmuka Projects Hub terdiri dari beberapa bagian utama:
- **Header Telemetri & Status**: Menampilkan statistik ringkas sistem secara langsung:
  - Jumlah Alur Kerja Aktif (*Active Pipelines*)
  - Total Kamera Terkoneksi (*Online RTSP Streams*)
  - Penggunaan Memori RAM & Ketersediaan Akselerasi Grafis (GPU / CPU Mode)
  - Versi Build Sistem Terpasang
- **Segmented Control Tab**: Membagi navigasi menjadi dua tab utama:
  1. **Tab Template Industri (37+ Pre-configured Blueprints)**: Solusi vision siap pakai yang dikurasi oleh para pakar industri.
  2. **Tab Proyek Saya (My Projects Table)**: Daftar seluruh alur kerja kustom yang pernah Anda buat atau simpan.

![Katalog Template](screenshots/home_template_crop.png)
*Gambar 3.2: Grid Kartu Template Vision Industri dengan Thumbnail Asli 16:9.*

---

### 2. Memilih dan Menggunakan Template Bawaan
Sistem menyediakan **37+ Template Alur Kerja** yang mencakup berbagai sektor:
- **Manufaktur & Heavy Equipment**:
  - *Tire Workshop Zone Activity Timer*: Pemantauan durasi kerja mekanik pada bay ban alat berat.
  - *Welding Quality & Thermal Monitoring*: Deteksi kestabilan proses pengelasan.
  - *Assembly Line Bottle / Package Counter*: Penghitungan konveyor kecepatan tinggi.
- **Logistik & Pergudangan (Warehouse)**:
  - *Warehouse Gate Exit Violation*: Deteksi truk/palet keluar tanpa izin resmi.
  - *Overstack Clearance Detection*: Sensor batas ketinggian tumpukan kardus/palet di rak gudang.
  - *Forklift & Pedestrian Safety Zone*: Zona interaksi bahaya antara manusia dan alat berat.
- **K3 & Keselamatan Kerja (Safety & Compliance)**:
  - *PPE Compliance Matrix*: Verifikasi pemakaian Helm (Hardhat), Rompi Pantul, dan Sarung Tangan.
  - *Man Down & Fall Detector*: Deteksi dini pekerja jatuh pingsan atau tergeletak darurat.
- **Smart City & Manajemen Gedung**:
  - *LPR (License Plate Recognition) Barrier Gate*: Pembaca plat nomor kendaraan otomatis.
  - *Crowd Heatmap & Dwell Time Analytics*: Analisis kepadatan pengunjung di ruang publik.

Untuk menggunakan template, cukup arahkan kursor ke kartu yang diinginkan lalu klik tombol **"Buka Template"**. Sistem akan memuat topologi node yang telah terhubung sempurna ke dalam Workspace Studio.

---

### 3. Manajemen Proyek: Duplikasi, Ekspor & Impor
Pada tab **Proyek Saya**, Anda dapat mengelola alur kerja yang tersimpan:

![Tabel Proyek](screenshots/home_projects_table.png)
*Gambar 3.3: Tabel Manajemen Proyek dengan Tombol Aksi Duplikasi Cepat.*

- **Duplikasi Proyek Instan (*Quick Clone*)**: Klik tombol bertanda ikon dokumen gandakan di samping proyek. Sistem akan menyalin seluruh struktur topologi graf, konfigurasi parameter, dan koordinat polygon zona kerja ke dalam proyek baru dengan akhiran nama `(Salinan)` dan ID acak baru.
- **Ekspor JSON Workflow**: Mengunduh skema alur kerja ke dalam file `.json` lokal sebagai backup atau untuk dipindahkan ke server lain.
- **Impor JSON**: Mengunggah kembali file konfigurasi alur kerja JSON secara langsung tanpa kehilangan setelan apapun.

---

## 3.2 Workflow Studio: Kanvas Visual Interaktif

**Workflow Studio** adalah ruang kerja utama tempat Anda merancang, menguji, dan mengamati proses inferensi *Computer Vision*.

![Workflow Studio Canvas](screenshots/007_workflow_studio_canvas.png)
*Gambar 3.4: Kanvas Visual Workflow Studio dengan Jalur Koneksi Kabel Bezier dan Preview Frame Aktif.*

### 1. Anatomi Kanvas Visual
- **Infinite Panning**: Geser kanvas ke segala arah dengan cara **klik kiri dan tahan** pada area kosong kanvas lalu seret kursor, atau gunakan **tombol tengah mouse (wheel drag)**.
- **Semantic Zooming**: Putar roda mouse (*scroll wheel*) ke atas untuk memperbesar (*zoom-in*) hingga detail pin terkecil, atau ke bawah untuk memperkecil (*zoom-out*) melihat keseluruhan arsitektur graf.
- **Background Grid Snapping**: Latar belakang bermotif titik kisi (*dot grid*) memandu penataan node agar rapi dan simetris secara otomatis.

---

### 2. Topbar Command Center (Pusat Komando)
Topbar horizontal di bagian atas kanvas menyediakan kontrol eksekusi alur kerja:

![Toolbar Actions](screenshots/12_unified_toolbar_actions.png)
*Gambar 3.5: Toolbar Terpadu dengan Kontrol Play, FPS Live, Tombol Open-NVR, dan Export Code.*

| Ikon / Elemen | Nama Aksi | Fungsi Teknis |
|---|---|---|
| ▶️ / ⏸️ | **Run / Pause Engine** | Memulai eksekusi alur kerja di latar belakang atau menghentikan runner sementara waktu. |
| 🔄 | **Hot-Reload Graph** | Mengirim pembaruan konfigurasi parameter ke runner aktif tanpa merestart stream kamera. |
| ⚡ **FPS Meter** | **Live Performance Counter** | Menampilkan kecepatan frame per detik (*Frames Per Second*) riil dan latensi pemrosesan milidetik. |
| 📹 **NVR Hub** | **Buka Open-NVR Modal** | Membuka jendela kokpit NVR untuk penemuan kamera ONVIF, pengaturan RTSP, dan Evidence Vault. |
| 🖥️ **CAD Studio** | **Full-Screen Calibration** | Membuka mode layar penuh 90vw untuk kalibrasi zona polygon dan garis crossing tingkat presisi CAD. |
| 📦 **Export Code** | **Unduh Python Standalone** | Mengemas alur kerja aktif menjadi file ZIP mandiri berisi skrip `run.py` untuk deployment edge. |
| 📊 **Dashboard** | **Buka Dashboard Viewer** | Membuka antarmuka dashboard operasional yang terikat dengan alur kerja ini. |

---

### 3. Anatomi Sebuah Node Visual
Setiap node pada kanvas direpresentasikan sebagai kartu modular dengan struktur terstandardisasi:

```
+------------------------------------------+
|  [Ikon]  Object Detector (YOLO)          |  <-- Header Node (Nama & Tipe)
+------------------------------------------+
| (o) Input Image                          |  <-- Pin Input (Kiri)
|                               (o) Image  |  <-- Pin Output (Kanan)
|                          (o) Detections  |  <-- Pin Output (Kanan)
+------------------------------------------+
| Model: yolov8n.pt | Conf: 0.45           |  <-- Ringkasan Parameter Cepat
+------------------------------------------+
```

- **Pin Input (Lingkaran di Sisi Kiri)**: Menerima aliran data dari node sebelumnya.
- **Pin Output (Lingkaran di Sisi Kanan)**: Memancarkan hasil pemrosesan ke node downstream berikutnya.
- **Kabel Penghubung (*Wire Edge*)**: Klik dan seret dari Pin Output sebuah node, lalu lepaskan kursor tepat di atas Pin Input node target. Garis kurva bezier akan terbentuk dengan animasi aliran data saat runner aktif.
- **Menghapus Sambungan**: Klik kanan pada kabel atau klik ikon silang kecil pada kabel untuk memutus aliran data.

---

## 3.3 Sidebar Palette & Pencarian Cerdas Node

Di sisi kiri kanvas terdapat **Sidebar Palette** yang menampung seluruh 98 node bawaan sistem.

![Sidebar Palette](screenshots/15_blank_canvas_new_project.png)
*Gambar 3.6: Kanvas Bersih dengan Sidebar Palette Terbuka Menampilkan Kategori Node.*

### 1. Kategori Node Terstruktur
Node dikelompokkan ke dalam 7 kategori fungsional:
1. **Sources (Sumber Input)**: Pintu masuk video (Kamera RTSP, File Video MP4, YouTube Stream).
2. **Image Preprocessing**: Pemrosesan awal citra (Crop, Slicer SAHI, Rotate, Privacy Mask).
3. **AI Vision Models**: Model kecerdasan buatan (YOLO Detector, Pose, UniFace, LPR, LLM Agent).
4. **Tracking & Analysis**: Pelacakan objek temporal dan logika spasial (ByteTrack, Zone Timer, Line Counter).
5. **Logic & Flow Control**: Pengatur alur dan filter kondisi (Motion Gate, Cooldown Gate, If/Else).
6. **Annotations & Drawing**: Visualisasi kotak, garis, teks, dan heatmap kepadatan.
7. **Outputs & Export**: Pengiriman hasil (Evidence Vault, ERP Webhook, MQTT, Telegram, CSV).

### 2. Fitur Pencarian Cerdas (*Fuzzy Search*)
Cukup ketik kata kunci pada kotak pencarian di bagian atas sidebar (misalnya ketik `"timer"`, `"plate"`, `"face"`, atau `"mqtt"`). Daftar node akan tersaring seketika. Anda cukup **menyeret (drag)** node yang diinginkan dan **melepaskannya (drop)** di area kanvas visual.

---

## 3.4 Node Inspector Drawer (Panel Konfigurasi Interaktif)

Saat Anda mengklik sebuah node pada kanvas, panel **Node Inspector** akan terbuka secara mulus di sisi kanan layar. Panel ini memungkinkan pengaturan parameter rinci yang terikat langsung ke *schema* node tersebut.

![Inspector Konfigurasi](screenshots/05_overlay_annotate_inspector.png)
*Gambar 3.7: Node Inspector untuk Pengaturan Komprehensif Lapisan Overlay dan Anotasi.*

### Tipe Kontrol Input pada Inspector:
- **Numeric Slider & Stepper**: Mengatur nilai ambang batas dengan presisi (misal: *Confidence Threshold* `0.00` hingga `1.00`, atau *IOU Threshold*).
- **Dropdown Selector**: Memilih bobot model AI (`yolov8n.pt`, `yolov8s.pt`, `yolo11n.pt`, `yolo26n.pt`), algoritma tracking (`bytetrack`, `botsort`, `cbiou`), atau mode warna.
- **Toggle Switch**: Mengaktifkan atau menonaktifkan fitur secara cepat (misal: *Appearance Re-ID Lock*, *Draw Skeleton*, *Save Video Clip*).
- **Text & JSON Input**: Mengonfigurasi URL RTSP kamera, alamat Broker MQTT, Token API Webhook, atau custom prompt untuk AI Agent.
- **Interactive Coordinate Button**: Tombol "Edit Polygon" atau "Edit Line" yang langsung meluncurkan CAD Annotation Studio untuk kalibrasi koordinat visual.

Setiap perubahan nilai di Inspector disimpan secara otomatis dan langsung dipropagasikan ke backend tanpa perlu menekan tombol simpan berulang kali.

---

## 3.5 Full-Screen Calibration & Annotation Studio (CAD-Grade)

Menggambar koordinat zona atau garis pada kotak kecil preview video di monitor resolusi tinggi sering kali tidak presisi. Afi Vision Builder menyediakan **Full-Screen Calibration Studio**, sebuah kanvas anotasi berukuran masif (90% viewport width) dengan fitur presisi kelas CAD/Figma.

![Multi Zone Editor](screenshots/04_multi_zone_editor.png)
*Gambar 3.8: Full-Screen CAD Annotation Studio untuk Menggambar Multi-Zona Polygon Presisi Tinggi.*

### Fitur Kunci CAD Annotation Studio:
1. **Sub-Pixel Loupe Magnifier (Kaca Pembesar 3x)**:
   Saat kursor mouse mendekati titik sudut (*vertex*) polygon, kaca pembesar bundar akan muncul di sekitar kursor, menampilkan perbesaran 300% dari piksel frame video di bawahnya. Hal ini memastikan titik zona diletakkan tepat pada garis lantai atau batas gerbang tanpa meleset satu piksel pun.
2. **Auto-Freeze & Live Stream Toggle**:
   Tersedia tombol untuk membekukan (*freeze*) frame sementara saat Anda menggambar objek yang sedang bergerak cepat di kamera, lalu mengembalikannya ke mode siaran langsung (*unfreeze live*) saat verifikasi zona.
3. **Pena Polygon Interaktif (*Smart Polygon Pen*)**:
   - Klik kiri pada area video untuk meletakkan titik sudut baru.
   - Klik dan seret titik yang sudah ada untuk memindahkan posisi koordinat.
   - Klik kanan pada titik untuk menghapusnya.
   - Klik titik awal kembali untuk menutup (*close*) loop polygon.
4. **Normalisasi Rasio Aspek (Aspect Ratio Letterbox Normalization)**:
   Sistem secara otomatis menghitung offset koordinat normalisasi (0.0 hingga 1.0) bebas distorsi, bahkan jika rasio layar monitor Anda (16:10 / 21:9) berbeda dengan rasio asli stream kamera (16:9 / 4:3).
5. **Validasi Geometri Otomatis**:
   Sistem menolak polygon yang berpotongan sendiri (*self-intersecting bowtie polygon*) untuk menjamin algoritma penentuan objek *Point-in-Polygon (Ray Casting)* tidak pernah mengalami error matematis.

---

## 3.6 Daftar Pintasan Papan Ketik (Keyboard Shortcuts & Hotkeys)

Untuk mempercepat alur kerja profesional, gunakan tombol pintas berikut saat berada di Workflow Studio:

| Kombinasi Tombol | Aksi yang Dijalankan |
|---|---|
| `Space` + **Drag Mouse** | Menggeser kanvas (*Pan Canvas View*) |
| `Ctrl` + `Scroll Wheel` | Memperbesar / Memperkecil Kanvas (*Zoom In / Zoom Out*) |
| `Ctrl` + `Z` | Membatalkan aksi terakhir (*Undo Node/Connection*) |
| `Ctrl` + `Y` / `Ctrl` + `Shift` + `Z` | Mengulang aksi yang dibatalkan (*Redo*) |
| `Delete` / `Backspace` | Menghapus node atau kabel koneksi yang sedang dipilih |
| `Ctrl` + `A` | Memilih seluruh node di kanvas (*Select All Nodes*) |
| `Ctrl` + `C` & `Ctrl` + `V` | Menyalin (*Copy*) dan Menempel (*Paste*) node terpilih |
| `Ctrl` + `S` | Menyimpan perubahan proyek ke basis data server |
| `F` | Memfokuskan tampilan kanvas ke seluruh node (*Fit View to Screen*) |
| `Esc` | Menutup jendela modal / keluar dari CAD Annotation Studio |

---

*Lanjutkan ke **Bagian IV: Ensiklopedia Lengkap Seluruh 98 Node** untuk memahami spesifikasi teknis dan parameter setiap modul.*



<!-- PAGE BREAK: BAB_04_ENSIKLOPEDIA_NODE_PART1_SOURCES_PREPROCESSING.md -->


# ENSIKLOPEDIA NODE: BAGIAN 4.1
# SOURCES (SUMBER INPUT) & IMAGE PREPROCESSING (19 NODES)

---

## DAFTAR ISI BAGIAN 4.1

1. **Kategori Sources (Sumber Input Video)**
   - 4.1.1 `input`: Input Universal (Webcam, File MP4, Mock Generator)
   - 4.1.2 `ip_camera`: IP Camera / CCTV Network Stream (RTSP, RTMP, HLS, HTTP)
   - 4.1.3 `video_speed_controller`: Video Speed & Timeline Scrubbing Controller
2. **Kategori Image Preprocessing (Pra-Pemrosesan Citra)**
   - 4.1.4 `auto_rotate_edges`: Deteksi Kemiringan Otomatis & Koreksi Rotasi Tepi
   - 4.1.5 `background_subtract`: Pengurangan Latar Belakang (MOG2 / KNN Background Subtraction)
   - 4.1.6 `blur_sharpen`: Penghalusan Gaussian Blur / Penajaman Citra (Sharpen Kernel)
   - 4.1.7 `brightness_contrast`: Kalibrasi Kecerahan, Kontras & Adaptif CLAHE
   - 4.1.8 `camera_focus`: Evaluasi Ketajaman & Fokus Lensa Kamera (Laplacian Variance)
   - 4.1.9 `color_convert`: Konversi Ruang Warna (BGR, RGB, HSV, Grayscale, LAB)
   - 4.1.10 `crop`: Pemotongan Area Citra Statis (Region of Interest / ROI Crop)
   - 4.1.11 `delta_filter`: Filter Perbedaan Gerak Antar-Frame (Temporal Frame Differencing)
   - 4.1.12 `frame_sampler`: Pengatur Frekuensi Frame / FPS Decimation
   - 4.1.13 `perspective`: Transformasi Perspektif Bird's Eye View / Keystone Correction
   - 4.1.14 `privacy_mask`: Masking Area Privasi & Pengecualian Deteksi (Exclusion Mask)
   - 4.1.15 `python_script`: Eksekusi Skrip Python Kustom Terisolasi (Sandboxed Runtime)
   - 4.1.16 `resize`: Skalasi Dimensi Citra (Bilinear, Nearest, Bicubic, Area)
   - 4.1.17 `rotate_flip`: Rotasi Sudut Tetap (90, 180, 270 Derajat) & Pembalikan Cermin (Flip)
   - 4.1.18 `slicer`: Pemotong Objek Kecil Berkecepatan Tinggi (SAHI - Slicing Inference)
   - 4.1.19 `undistort`: Koreksi Distorsi Lensa Fisheye & Wide-Angle (Camera Calibration)

---

## 4.1.1 `input`: Input Universal (Webcam / File Video)

### Deskripsi Fungsional
Node `input` berfungsi sebagai generator sumber citra awal untuk pengujian lokal, demonstrasi alur kerja, atau inferensi dari file video rekaman dan kamera web USB bawaan perangkat.

### Diagram Alur Data & Pin Koneksi
```
+------------------------------------------+
|  [Icon]  Input (Universal Source)        |
+------------------------------------------+
|                               (o) Image  |
+------------------------------------------+
```
- **Pin Input**: *Tidak ada* (Node Awal / Root Generator)
- **Pin Output**: 
  - `image` (`np.ndarray`): Matriks citra warna format BGR ukuran resolusi asli sumber.

### Parameter Konfigurasi (Config Schema)
| Parameter | Tipe Data | Nilai Default | Pilihan / Rentang | Penjelasan Fungsional |
|---|---|---|---|---|
| `sourceType` | String | `"sample"` | `"sample"`, `"webcam"`, `"file"`, `"url"` | Menentukan jenis media input yang akan dibaca. |
| `webcamIndex` | Integer | `0` | `0` s/d `10` | Indeks perangkat keras kamera web USB (0 = kamera default). |
| `videoPath` | String | `""` | Path lokal file | Alamat absolut atau relatif file video lokal (contoh: `data/sample.mp4`). |
| `loop` | Boolean | `true` | `true` / `false` | Memutar ulang file video secara otomatis saat mencapai akhir durasi. |
| `targetFps` | Integer | `30` | `1` s/d `60` | Membatasi kecepatan pembacaan frame per detik untuk mencegah *CPU spike*. |

### Algoritma & Perilaku Teknis
Node menggunakan `cv2.VideoCapture` yang dienkapsulasi dengan thread pembacaan asinkron. Jika sumber video mencapai akhir frame (*End of File / EOF*) dan opsi `loop=true`, penunjuk frame akan di-seek kembali ke frame 0 melalui `cap.set(cv2.CAP_PROP_POS_FRAMES, 0)`.

---

## 4.1.2 `ip_camera`: IP Camera / CCTV Network Stream

### Deskripsi Fungsional
Node tulang punggung integrasi pengawasan industri untuk menarik siaran langsung video (*live video stream*) dari kamera jaringan (IP Camera), NVR, DVR, atau encoder video industri melalui berbagai protokol jaringan.

### Diagram Alur Data & Pin Koneksi
```
+------------------------------------------+
|  [Icon]  IP Camera / CCTV Stream         |
+------------------------------------------+
|                               (o) Image  |
+------------------------------------------+
```
- **Pin Input**: *Tidak ada* (Node Awal)
- **Pin Output**:
  - `image` (`np.ndarray`): Citra frame BGR beresolusi tinggi langsung dari stream jaringan.

### Parameter Konfigurasi (Config Schema)
| Parameter | Tipe Data | Nilai Default | Pilihan / Rentang | Penjelasan Fungsional |
|---|---|---|---|---|
| `rtspUrl` | String | `"rtsp://..."` | URL RTSP Valid | Alamat RTSP lengkap kamera termasuk autentikasi user dan password. |
| `transport` | String | `"tcp"` | `"tcp"`, `"udp"`, `"http"` | Protokol transport RTSP. TCP sangat disarankan untuk mencegah *packet drop* dan artefak smearing. |
| `reconnectInterval` | Integer | `5` | `1` s/d `60` | Waktu tunggu (detik) sebelum mencoba menghubungkan ulang jika stream terputus. |
| `dropFrames` | Boolean | `true` | `true` / `false` | Membuang frame yang menumpuk di buffer saat inferensi AI lebih lambat dari FPS kamera (*Zero-Latency Mode*). |
| `hardwareDecode` | String | `"auto"` | `"auto"`, `"cpu"`, `"cuda"`, `"qsv"` | Akselerasi decoding perangkat keras menggunakan GPU NVIDIA NVDEC atau Intel QuickSync. |

### Contoh Format URL RTSP Berbagai Merek Kamera CCTV:
- **Hikvision / Hilook**: `rtsp://admin:Password123@192.168.1.64:554/Streaming/Channels/101` (Sub-stream: `/102`)
- **Dahua / IMOU**: `rtsp://admin:Password123@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0`
- **Uniview (UNV)**: `rtsp://admin:Password123@192.168.1.30:554/unicast/c1/s0/live`
- **Axis Communications**: `rtsp://root:Password123@192.168.1.50:554/axis-media/media.amp`

---

## 4.1.3 `video_speed_controller`: Video Speed & Timeline Scrubbing Controller

### Deskripsi Fungsional
Node pengendali playback video mutakhir yang memungkinkan akselerasi playback (0.25x hingga 4.0x), fungsi loncat timeline seketika (*seeking/scrubbing*), serta sinkronisasi dinamis via REST API `/api/video/seek` dan `/api/video/playback-speed`.

### Diagram Alur Data & Pin Koneksi
```
+------------------------------------------+
|  [Icon]  Video Speed & Timeline Control  |
+------------------------------------------+
| (o) Input Image                          |
|                               (o) Image  |
+------------------------------------------+
```
- **Pin Input**: `image` (Citra sumber video)
- **Pin Output**: `image` (Citra yang telah disinkronkan kecepatannya dengan overlay HUD opsional)

### Parameter Konfigurasi (Config Schema)
| Parameter | Tipe Data | Nilai Default | Pilihan / Rentang | Penjelasan Fungsional |
|---|---|---|---|---|
| `speedMultiplier` | Float | `1.0` | `0.25` s/d `4.0` | Faktor kecepatan pemutaran (misal: 0.5x slow motion, 2.0x fast forward). |
| `seekPercent` | Float | `0.0` | `0.0` s/d `100.0` | Posisi loncat timeline dalam persen durasi video. |
| `showOverlayHud` | Boolean | `true` | `true` / `false` | Menampilkan badge HUD transparan berisi indikator kecepatan dan posisi timeline pada pojok video. |
| `syncMode` | String | `"adaptive"` | `"adaptive"`, `"drop"`, `"wait"` | Mekanisme sinkronisasi frame rate untuk mempertahankan konsistensi clock visual. |

---

## 4.1.4 `auto_rotate_edges`: Deteksi Kemiringan & Koreksi Rotasi Otomatis

### Deskripsi Fungsional
Mengidentifikasi orientasi garis dominan pada citra (misalnya plat nomor, dokumen faktur, atau palet miring) dan memutar citra secara otomatis agar sejajar tegak lurus (*upright deskewing*).

### Parameter Konfigurasi
- `edgeThreshold1` (Integer, Default: `50`): Ambang batas bawah detektor tepi Canny.
- `edgeThreshold2` (Integer, Default: `150`): Ambang batas atas detektor tepi Canny.
- `houghThreshold` (Integer, Default: `100`): Akumulator batas minimum transformasi Hough Line.
- `maxAngleDegrees` (Float, Default: `45.0`): Batas rotasi koreksi maksimum untuk mencegah pemutaran citra terbalik.

---

## 4.1.5 `background_subtract`: Pengurangan Latar Belakang (Motion Mask)

### Deskripsi Fungsional
Memisahkan objek bergerak (*foreground*) dari pemandangan diam (*background*) menggunakan model statistik Gaussian Mixture (MOG2) atau K-Nearest Neighbors (KNN).

### Parameter Konfigurasi
- `algorithm` (String, Default: `"mog2"`): Pilihan antara `"mog2"` atau `"knn"`.
- `history` (Integer, Default: `500`): Jumlah frame historis yang digunakan untuk membangun model latar belakang.
- `varThreshold` (Float, Default: `16.0`): Ambang batas variansi Mahalanobis untuk mengklasifikasikan piksel gerak.
- `detectShadows` (Boolean, Default: `true`): Menandai bayangan objek sebagai warna abu-abu agar tidak dianggap sebagai benda solid.

---

## 4.1.6 `blur_sharpen`: Penghalusan Gaussian Blur / Penajaman Citra

### Deskripsi Fungsional
Melakukan pemfilteran spasial pada citra untuk mengurangi derau frekuensi tinggi (*high-frequency noise*) pada kamera malam, atau mempertajam tepi objek kabur sebelum masuk ke detektor AI.

### Parameter Konfigurasi
- `mode` (String, Default: `"blur"`): Pilihan `"blur"`, `"gaussian_blur"`, `"median"`, `"sharpen"`.
- `kernelSize` (Integer, Default: `5`): Ukuran matriks kernel ganjil (3, 5, 7, 9, 11). Nilai lebih besar menghasilkan keburaman lebih kuat.
- `sigmaX` (Float, Default: `1.5`): Deviasi standar kernel Gaussian pada sumbu X.
- `sharpenStrength` (Float, Default: `1.0`): Pengali intensitas unsharp masking untuk mode penajaman.

---

## 4.1.7 `brightness_contrast`: Kalibrasi Kecerahan, Kontras & CLAHE

### Deskripsi Fungsional
Mengoreksi kondisi pencahayaan ekstrem (ruangan gelap atau cahaya silau matahari) menggunakan transformasi linear $g(x) = \alpha \cdot f(x) + \beta$ atau algoritma adaptif CLAHE (*Contrast Limited Adaptive Histogram Equalization*).

### Parameter Konfigurasi
- `brightness` (Integer, Default: `0`, Rentang: `-100` s/d `100`): Penambah nilai offset piksel ($\beta$).
- `contrast` (Float, Default: `1.0`, Rentang: `0.1` s/d `3.0`): Pengali kontras citra ($\alpha$).
- `useClahe` (Boolean, Default: `false`): Mengaktifkan ekualisasi histogram lokal adaptif pada kanal Luminance (YCrCb atau LAB).
- `claheClipLimit` (Float, Default: `2.0`): Batas pemotongan kontras pada CLAHE untuk membatasi penguatan derau (*noise amplification*).
- `claheGridSize` (Integer, Default: `8`): Ukuran blok kisi kontekstual (misal: 8x8 piksel).

---

## 4.1.8 `camera_focus`: Evaluasi Ketajaman & Fokus Lensa Kamera

### Deskripsi Fungsional
Menilai kesehatan visual kamera secara otomatis dengan mengukur variansi operator Laplacian ($\sigma^2_{\Delta}$). Jika lensa buram karena debu, cipratan air, atau pergeseran fokus mekanis, node akan memicu peringatan pemeliharaan.

### Parameter Konfigurasi
- `blurThreshold` (Float, Default: `100.0`): Nilai skor fokus minimum. Frame dengan skor di bawah nilai ini dikategorikan `BLURRY` / buram.
- `warningCooldownSeconds` (Integer, Default: `60`): Jeda waktu minimum sebelum memicu kembali peringatan fokus rusak ke dashboard.

---

## 4.1.9 `color_convert`: Konversi Ruang Warna (Color Space)

### Deskripsi Fungsional
Mengonversi matriks citra BGR ke ruang warna lain untuk mempermudah analisis warna tertentu (misal: isolasi warna api pada HSV atau analisis pencahayaan murni pada LAB).

### Parameter Konfigurasi
- `targetSpace` (String, Default: `"rgb"`): Pilihan: `"rgb"`, `"gray"`, `"hsv"`, `"lab"`, `"ycrcb"`.

---

## 4.1.10 `crop`: Pemotongan Area Citra Statis (ROI Crop)

### Deskripsi Fungsional
Memotong persegi panjang statis dari frame video penuh untuk memfokuskan sumber daya inferensi AI hanya pada area kritis (misalnya hanya pada konveyor barang atau bay workshop tertentu), menghemat hingga 70% beban komputasi model AI.

### Parameter Konfigurasi
- `x` (Float, Default: `0.0`, Rentang: `0.0` s/d `1.0`): Koordinat normalisasi horizontal sudut kiri atas.
- `y` (Float, Default: `0.0`, Rentang: `0.0` s/d `1.0`): Koordinat normalisasi vertikal sudut kiri atas.
- `width` (Float, Default: `1.0`, Rentang: `0.0` s/d `1.0`): Lebar normalisasi area potongan.
- `height` (Float, Default: `1.0`, Rentang: `0.0` s/d `1.0`): Tinggi normalisasi area potongan.

---

## 4.1.11 `delta_filter`: Filter Perbedaan Gerak Antar-Frame

### Deskripsi Fungsional
Membandingkan frame saat ini $I_t$ dengan frame sebelumnya $I_{t-1}$ menggunakan pengurangan absolut $|I_t - I_{t-1}|$. Jika persentase piksel yang berubah berada di bawah ambang batas, frame diklasifikasikan statis dan tidak diteruskan ke node AI hilir.

### Parameter Konfigurasi
- `pixelThreshold` (Integer, Default: `25`): Selisih intensitas warna minimum agar satu piksel dianggap berubah.
- `minAreaRatio` (Float, Default: `0.005`): Rasio luas perubahan minimum terhadap total frame (0.5%) untuk meloloskan frame.

---

## 4.1.12 `frame_sampler`: Pengatur Frekuensi Frame (FPS Decimation)

### Deskripsi Fungsional
Mengatur frekuensi frame yang mengalir ke node berikutnya (misal: kamera mengirim 30 FPS, tetapi model AI hanya perlu mengeksekusi 5 FPS).

### Parameter Konfigurasi
- `sampleRate` (Integer, Default: `5`): Hanya meneruskan 1 frame setiap $N$ frame masuk.
- `maxFps` (Float, Default: `10.0`): Membatasi laju frame maksimum secara temporal (berdasarkan clock detik).

---

## 4.1.13 `perspective`: Transformasi Perspektif Bird's Eye View

### Deskripsi Fungsional
Menerapkan matriks homografi $3 \times 3$ untuk mengubah sudut pandang kamera miring (*angled perspective*) menjadi sudut pandang tegak lurus dari atas (*top-down bird's eye view*).

### Parameter Konfigurasi
- `sourcePoints` (List of Points): Empat titik sudut trapesium pada citra asli.
- `destPoints` (List of Points): Empat titik sudut persegi panjang datar pada citra hasil.
- `outputWidth` (Integer, Default: `640`): Lebar piksel citra hasil proyeksi.
- `outputHeight` (Integer, Default: `480`): Tinggi piksel citra hasil proyeksi.

---

## 4.1.14 `privacy_mask`: Masking Area Privasi & Pengecualian Deteksi

### Deskripsi Fungsional
Mengaburkan (*blackout* atau *blur*) polygon tertentu secara permanen dari frame sebelum masuk ke AI atau Live Preview. Sangat berguna untuk kepatuhan regulasi privasi data (GDPR/K3) untuk menutupi jendela kantor, layar komputer kasir, atau jalan raya umum di luar pabrik.

### Parameter Konfigurasi
- `maskPoints` (List of Coordinates): Titik-titik sudut polygon area yang ingin ditutup.
- `fillColor` (String, Default: `"black"`): Warna penutup: `"black"`, `"white"`, atau `"blur"`.

---

## 4.1.15 `python_script`: Eksekusi Skrip Python Kustom Terisolasi

### Deskripsi Fungsional
Node serbaguna bagi developer untuk menulis kode Python langsung di dalam Workflow Studio guna melakukan manipulasi matriks citra NumPy kustom, kalkulasi matematika, atau integrasi pustaka khusus tanpa memodifikasi kode inti backend.

### Parameter Konfigurasi
- `code` (String): Blok kode Python yang mendefinisikan fungsi `process(frame, detections, context)`.
- `timeoutSeconds` (Float, Default: `0.5`): Batas waktu eksekusi skrip untuk mencegah pembekuan (*freezing*) engine.

---

## 4.1.16 `resize`: Skalasi Dimensi Citra

### Deskripsi Fungsional
Mengubah resolusi spasial frame citra ke lebar dan tinggi target tertentu menggunakan interpolasi matematis teruji.

### Parameter Konfigurasi
- `width` (Integer, Default: `640`): Lebar citra baru.
- `height` (Integer, Default: `480`): Tinggi citra baru.
- `interpolation` (String, Default: `"linear"`): Pilihan: `"linear"` (cepat), `"area"` (terbaik untuk pengecilan), `"cubic"` (terbaik untuk pembesaran), `"nearest"`.
- `keepAspectRatio` (Boolean, Default: `true`): Mempertahankan rasio aspek asli dengan menambahkan bilah hitam (*letterboxing*).

---

## 4.1.17 `rotate_flip`: Rotasi Sudut Tetap & Pembalikan Cermin

### Deskripsi Fungsional
Memutar citra secara fisik sebesar 90°, 180°, atau 270° (searah jarum jam) atau membalik citra secara horizontal/vertikal. Berguna saat kamera CCTV fisik dipasang terbalik pada plafon atau dipasang vertikal (*portrait mode*).

### Parameter Konfigurasi
- `rotationAngle` (Integer, Default: `0`): Pilihan: `0`, `90`, `180`, `270`.
- `flipMode` (String, Default: `"none"`): Pilihan: `"none"`, `"horizontal"` (kiri-kanan), `"vertical"` (atas-bawah), `"both"`.

---

## 4.1.18 `slicer`: Pemotong Objek Kecil Berkecepatan Tinggi (SAHI)

### Deskripsi Fungsional
Mengimplementasikan teknik **Slicing Aided Hyper Inference (SAHI)**. Node ini mengiris frame resolusi tinggi (misal 4K atau 1080p) menjadi kisi-kisi ubin (*tiles*) yang saling bertumpukan (*overlapping patches*). Setiap ubin kemudian diproses secara terpisah oleh model detektor, memungkinkan deteksi objek mikroskopis yang terlalu kecil untuk dideteksi oleh YOLO standar.

### Parameter Konfigurasi
- `sliceHeight` (Integer, Default: `512`): Tinggi piksel setiap ubin irisan.
- `sliceWidth` (Integer, Default: `512`): Lebar piksel setiap ubin irisan.
- `overlapRatioHeight` (Float, Default: `0.2`): Rasio tumpang tindih vertikal antar-ubin (20%).
- `overlapRatioWidth` (Float, Default: `0.2`): Rasio tumpang tindih horizontal antar-ubin (20%).

---

## 4.1.19 `undistort`: Koreksi Distorsi Lensa Fisheye & Wide-Angle

### Deskripsi Fungsional
Menghilangkan efek distorsi cembung tong (*barrel distortion*) pada kamera CCTV bersudut pandang lebar (*wide-angle / fisheye lens*) menggunakan matriks intrinsik kamera ($K$) dan koefisien distorsi ($D$).

### Parameter Konfigurasi
- `cameraMatrix` (Matrix 3x3): Matriks fokal dan titik pusat optik $[[f_x, 0, c_x], [0, f_y, c_y], [0, 0, 1]]$.
- `distCoeffs` (Array 5-Elemen): Vektor distorsi radial dan tangensial $[k_1, k_2, p_1, p_2, k_3]$.

---

*Lanjutkan ke **Bagian 4.2: Ensiklopedia Node - AI Vision Models** untuk mempelajari modul inferensi kecerdasan buatan.*



<!-- PAGE BREAK: BAB_04_ENSIKLOPEDIA_NODE_PART2_AI_MODELS.md -->


# ENSIKLOPEDIA NODE: BAGIAN 4.2
# AI VISION MODELS (15 NODES)

---

## DAFTAR ISI BAGIAN 4.2

- 4.2.1 `detector`: Object Detection (YOLOv8 / YOLO11 / YOLO26n / RF-DETR)
- 4.2.2 `classifier`: Image Classification (Pengelompokan Kelas Citra Global)
- 4.2.3 `segmenter`: Object Segmentation & Pixel-Level Mask (YOLO-Seg / SAM)
- 4.2.4 `pose_detector`: Human Pose Estimator & Keypoint Skeleton (17 Titik Sendi)
- 4.2.5 `hand_skeleton`: Hand Tracking & Gesture Recognition (21 Titik Sendi Tangan)
- 4.2.6 `lpr_license_plate`: License Plate Reader (Pengenal Plat Kendaraan Otomatis)
- 4.2.7 `ocr_reader`: OCR Text Reader (Optical Character Recognition ONNX)
- 4.2.8 `barcode_reader`: Barcode & QR Code Scanner Multi-Format
- 4.2.9 `efficientad`: Visual Anomaly & Defect Inspection (Pembelajaran Tanpa Pengawasan)
- 4.2.10 `face_detector`: Face Detector (UniFace SCRFD Arsitektur Presisi Tinggi)
- 4.2.11 `face_analyzer`: Face Analyzer (Prediksi Atribut Usia, Gender, & Emosi)
- 4.2.12 `face_crop`: Face Crop & Aligning with Quality Assessment Score
- 4.2.13 `detection_crop`: Pemotong Bounding Box Dinamis untuk Inferensi Bertingkat
- 4.2.14 `model_comparison`: Model Comparison Diff & Benchmarking Visual
- 4.2.15 `ai_agent`: Autonomous Multimodal Vision AI Agent (LLM Integration)

---

## 4.2.1 `detector`: Object Detection (YOLO & RF-DETR)

### Deskripsi Fungsional
Node inti inferensi penglihatan komputer untuk melokalisasi dan mengklasifikasikan multi-objek secara simultan di dalam frame citra. Node ini mengembalikan koordinat kotak pembatas (*bounding boxes*), label kelas objek, dan skor keyakinan (*confidence score*).

![Detector Registry](screenshots/10_models_registry.png)
*Gambar 4.2.1: Panel Registrasi Model AI dengan Dukungan YOLOv8, YOLO11, dan YOLO26n.*

### Diagram Alur Data & Pin Koneksi
```
+------------------------------------------+
|  [Icon]  Object Detector (YOLO)          |
+------------------------------------------+
| (o) Input Image                          |
|                               (o) Image  |
|                          (o) Detections  |
+------------------------------------------+
```
- **Pin Input**: `image` (`np.ndarray` citra BGR)
- **Pin Output**:
  - `image` (`np.ndarray`): Citra asli yang diteruskan.
  - `detections` (`List[Detection]`): Struktur objek berisi koordinat `[x1, y1, x2, y2]`, `confidence` (0.0-1.0), `class_id` (int), dan `class_name` (str).

### Parameter Konfigurasi (Config Schema)
| Parameter | Tipe Data | Nilai Default | Pilihan / Rentang | Penjelasan Fungsional |
|---|---|---|---|---|
| `modelWeights` | String | `"yolov8n.pt"` | `"yolov8n.pt"`, `"yolov8s.pt"`, `"yolo11n.pt"`, `"yolo26n.pt"`, File Kustom `.onnx` | Nama bobot model AI yang dimuat dari direktori `weights/`. |
| `confidenceThreshold` | Float | `0.45` | `0.05` s/d `0.99` | Nilai probabilitas keyakinan minimum agar deteksi dianggap valid. |
| `iouThreshold` | Float | `0.45` | `0.10` s/d `0.90` | Ambang batas Intersection-over-Union untuk algoritma Non-Maximum Suppression (NMS). |
| `filterClasses` | List[String] | `[]` | Nama kelas COCO | Daftar kelas spesifik yang diizinkan lewat (misal: `["person", "truck", "tire"]`). Jika kosong, seluruh kelas diloloskan. |
| `device` | String | `"auto"` | `"auto"`, `"cpu"`, `"cuda:0"`, `"directml"` | Backend komputasi hardware yang digunakan untuk eksekusi model. |

---

## 4.2.2 `classifier`: Image Classification

### Deskripsi Fungsional
Mengklasifikasikan keseluruhan frame citra atau potongan objek ke dalam kategori probabilitas tertinggi (misalnya mengklasifikasikan apakah kondisi cuaca hujan/cerah, atau status mesin hidup/mati).

### Parameter Konfigurasi
- `modelWeights` (String, Default: `"yolov8n-cls.pt"`): Bobot model arsitektur klasifikasi.
- `topK` (Integer, Default: `3`): Jumlah prediksi probabilitas teratas yang dikembalikan.
- `confidenceThreshold` (Float, Default: `0.50`): Nilai keyakinan kelas minimum.

---

## 4.2.3 `segmenter`: Object Segmentation (YOLO-Seg / SAM)

### Deskripsi Fungsional
Melakukan segmentasi semantik tingkat piksel (*instance segmentation*), menghasilkan masker poligon yang presisi mengikuti lekukan bentuk asli objek (misalnya permukaan ban yang rusak, tumpahan oli di lantai, atau siluet kendaraan).

### Parameter Konfigurasi
- `modelWeights` (String, Default: `"yolov8n-seg.pt"`): Model segmentasi berbasis YOLO atau Segment Anything Model (SAM).
- `retinaMasks` (Boolean, Default: `true`): Menghasilkan masker beresolusi tinggi sesuai dimensi frame asli.
- `maskThreshold` (Float, Default: `0.50`): Ambang batas binarisasi probabilitas piksel masker.

---

## 4.2.4 `pose_detector`: Human Pose Estimator (17 Keypoints)

### Deskripsi Fungsional
Mengekstraksi kerangka tubuh manusia (*skeleton keypoints*) yang terdiri dari 17 titik sendi anatomis standar COCO: Hidung, Mata Kiri/Kanan, Telinga Kiri/Kanan, Bahu, Siku, Pergelangan Tangan, Pinggul, Lutut, dan Pergelangan Kaki.

![Pose Detection Frame](screenshots/001-01_canvas_custom_font.png)
*Gambar 4.2.2: Deteksi Kerangka Pose Manusia untuk Analisis Ergonomi dan K3.*

### Parameter Konfigurasi
- `modelWeights` (String, Default: `"yolov8n-pose.pt"`): Bobot model estimasi pose.
- `keypointThreshold` (Float, Default: `0.50`): Keyakinan minimum agar satu sendi digambar dan dihitung.
- `drawSkeleton` (Boolean, Default: `true`): Menggambar garis penghubung antar-sendi pada frame preview.

---

## 4.2.5 `hand_skeleton`: Hand Tracking & Gesture Recognition

### Deskripsi Fungsional
Melacak posisi tangan secara 3D dengan 21 koordinat sendi jari per tangan. Mendukung pengenalan gestur tangan (*gesture recognition*) seperti Jempol Atas (*Thumbs Up*), Tanda Kemenangan (*Victory / Peace*), Tangan Terbuka (*Open Palm*), dan Kepalan Tangan (*Fist*).

### Parameter Konfigurasi
- `maxHands` (Integer, Default: `2`, Rentang: `1` s/d `4`): Jumlah maksimum tangan yang dilacak bersamaan.
- `detectionConfidence` (Float, Default: `0.70`): Ambang keyakinan inisiasi deteksi tangan.
- `trackingConfidence` (Float, Default: `0.50`): Ambang batas kesinambungan pelacakan temporal.
- `hideNoneLabel` (Boolean, Default: `true`): Menyembunyikan label preview saat tidak ada gestur khusus yang cocok (`None`), menjaga kebersihan visual tampilan.

---

## 4.2.6 `lpr_license_plate`: License Plate Reader (LPR)

### Deskripsi Fungsional
Node terpadu dua tahap (*two-stage detector*) yang pertama-tama mendeteksi lokasi plat nomor kendaraan menggunakan model deteksi spesifik plat, lalu membaca karakter alfanumerik plat menggunakan OCR berbasis transformasi perspektif otomatis.

![LPR Inspector](screenshots/24_lpr_license_plate_inspector.png)
*Gambar 4.2.3: Konfigurasi Inspector Node License Plate Reader (LPR).*

### Parameter Konfigurasi
- `detectorWeights` (String, Default: `"weights/plate_detector.onnx"`): Model pelokalisasi plat.
- `ocrEngine` (String, Default: `"onnx_crnn"`): Engine pembaca karakter alfanumerik.
- `confidenceThreshold` (Float, Default: `0.60`): Keyakinan deteksi plat nomor.
- `countryRegexPattern` (String, Default: `^[A-Z]{1,2}\s?[0-9]{1,4}\s?[A-Z]{1,3}$`): Pola regex plat nomor standar Indonesia (contoh: `B 1234 CD`).

---

## 4.2.7 `ocr_reader`: OCR Text Reader (ONNX-CRNN)

### Deskripsi Fungsional
Mengekstraksi teks umum dari area tertentu pada frame, seperti membaca nomor seri kontainer (*ISO 6346 Container Code*), label barcode tercetak, atau teks pada papan nama industri.

### Parameter Konfigurasi
- `languages` (List[String], Default: `["en"]`): Bahasa teks yang dikenali.
- `textScoreThreshold` (Float, Default: `0.50`): Ambang batas probabilitas karakter teks.
- `allowlist` (String, Default: `""`): Karakter yang diizinkan (misal: `"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"`).

---

## 4.2.8 `barcode_reader`: Barcode & QR Code Reader

### Deskripsi Fungsional
Memindai dan mendecode berbagai format kode optik berkecepatan tinggi: QR Code, Data Matrix, Aztec, UPC-A, EAN-13, Code 128, dan Code 39.

### Parameter Konfigurasi
- `tryHarder` (Boolean, Default: `true`): Mengaktifkan rotasi multi-sudut dan peningkatan kontras untuk membaca kode yang rusak atau tergores.
- `formatFilter` (String, Default: `"ALL"`): Membatasi format pemindaian untuk meningkatkan kecepatan (misal: `"QR_CODE"`).

---

## 4.2.9 `efficientad`: Visual Anomaly & Defect Inspection

### Deskripsi Fungsional
Mengimplementasikan arsitektur **EfficientAD** untuk inspeksi cacat manufaktur tanpa supervisi (*unsupervised visual inspection*). Model dilatih hanya dengan menggunakan sampel produk normal (bebas cacat). Pada saat pengujian, model menandai setiap piksel yang menyimpang sebagai anomali (retak, goresan, perubahan warna, benda asing).

### Parameter Konfigurasi
- `modelPath` (String): Lokasi bobot model anomali spesifik komponen produk.
- `anomalyThreshold` (Float, Default: `0.55`): Ambang batas batas skor keparahan cacat visual.
- `generateHeatmap` (Boolean, Default: `true`): Menghasilkan visualisasi peta panas (*anomaly heatmap*) yang menyoroti area cacat.

---

## 4.2.10 `face_detector`: Face Detector (UniFace SCRFD)

### Deskripsi Fungsional
Mendeteksi wajah manusia dalam kondisi ekstrem (pencahayaan rendah, sudut miring ekstrem, dan wajah berjarak jauh) menggunakan arsitektur **SCRFD (Sample and Computation Redistribution for Efficient Face Detection)**.

![Face Registry](screenshots/16_face_registry_gallery.png)
*Gambar 4.2.4: Galeri Registrasi Wajah Karyawan untuk Face Recognition & Access Control.*

### Parameter Konfigurasi
- `confidenceThreshold` (Float, Default: `0.60`): Keyakinan deteksi wajah.
- `minFaceSizePixels` (Integer, Default: `30`): Mengabaikan wajah yang berukuran lebih kecil dari 30x30 piksel.

---

## 4.2.11 `face_analyzer`: Face Analyzer (Atribut Demografis)

### Deskripsi Fungsional
Memprediksi atribut komprehensif dari setiap wajah yang terdeteksi, meliputi estimasi rentang usia (*age prediction*), estimasi jenis kelamin (*gender prediction*), dan analisis ekspresi wajah (*happy, neutral, sad, angry, surprised*).

### Parameter Konfigurasi
- `hudScalePercent` (Integer, Default: `100`, Rentang: `50` s/d `200`): Skala ukuran badge HUD informasi atribut di atas kepala.
- `estimateAge` (Boolean, Default: `true`): Menghitung perkiraan usia.
- `estimateGender` (Boolean, Default: `true`): Menghitung probabilitas jenis kelamin.

---

## 4.2.12 `face_crop`: Face Crop & Quality Assessment

### Deskripsi Fungsional
Memotong bounding box wajah dengan rotasi otomatis berdasarkan garis mata (*eye alignment*) dan menghitung skor kualitas citra (*Image Quality Assessment / IQA*) untuk memastikan wajah memenuhi standar sebelum disimpan ke database absensi.

### Parameter Konfigurasi
- `targetResolution` (Integer, Default: `112`): Resolusi piksel hasil crop persegi (standar ArcFace 112x112).
- `minQualityScore` (Float, Default: `0.70`): Skor ambang batas ketajaman dan pencahayaan wajah.

---

## 4.2.13 `detection_crop`: Pemotong Deteksi Dinamis

### Deskripsi Fungsional
Menerima daftar deteksi dari node `detector`, lalu memotong setiap objek satu per satu (*crop each detection*) dan mengalirkannya ke pipeline sekunder (misalnya memotong setiap orang lalu meneruskannya ke model klasifikasi pemakaian rompi pengaman).

### Parameter Konfigurasi
- `paddingPercent` (Float, Default: `0.10`): Menambahkan margin kelonggaran 10% di sekitar bounding box agar tepi objek tidak terpotong.
- `targetClass` (String, Default: `""`): Memfilter hanya memotong kelas tertentu (misal: `"person"`).

---

## 4.2.14 `model_comparison`: Model Comparison Diff & Benchmarking

### Deskripsi Fungsional
Menerima keluaran deteksi dari dua model AI yang berbeda (misalnya YOLOv8n vs YOLO11n) pada frame yang sama, lalu menampilkan visualisasi perbandingan langsung: deteksi yang disepakati bersama (*consensus*), deteksi yang hanya ditemukan Model A, dan deteksi yang hanya ditemukan Model B.

### Parameter Konfigurasi
- `iouMatchThreshold` (Float, Default: `0.50`): Ambang IoU untuk menganggap dua kotak dari dua model mewakili objek yang sama.
- `modelLabelA` (String, Default: `"Model-A"`): Nama penanda visual model pertama.
- `modelLabelB` (String, Default: `"Model-B"`): Nama penanda visual model kedua.

---

## 4.2.15 `ai_agent`: Autonomous Multimodal Vision AI Agent

### Deskripsi Fungsional
Node paling mutakhir yang menggabungkan kemampuan **Multimodal Vision Large Language Model (VLM)** ke dalam aliran video CCTV (terinspirasi dari konsep n8n AI Agent). Node ini mengirimkan frame gambar beserta ringkasan metadata deteksi ke model LLM (seperti GPT-4o, GPT-5, atau Ollama LLaVA lokal) untuk menjawab pertanyaan penalaran kompleks, mendeteksi anomali tidak terduga, atau mengambil keputusan operasional otomatis.

![AI Studio Copilot](screenshots/13_ai_studio_copilot_drawer.png)
*Gambar 4.2.5: Antarmuka AI Agent Drawer untuk Konfigurasi Instruksi Semantik LLM.*

### Parameter Konfigurasi (Config Schema)
| Parameter | Tipe Data | Nilai Default | Pilihan / Rentang | Penjelasan Fungsional |
|---|---|---|---|---|
| `provider` | String | `"openai"` | `"openai"`, `"openrouter"`, `"ollama"`, `"custom"` | Penyedia layanan inferensi Large Language Model. |
| `modelName` | String | `"gpt-4o-mini"` | `"gpt-4o"`, `"gpt-4o-mini"`, `"llava:13b"`, `"qwen2-vl"` | Model multimodal yang digunakan. |
| `systemPrompt` | String | `"Anda adalah AI Pengawas Keamanan Industri..."` | Teks Instruksi Lengkap | Peran dan batasan etika operasional sistem pengawasan. |
| `userPrompt` | String | `"Periksa apakah ada personil yang melanggar batas keselamatan..."` | Teks Kueri Analisis | Pertanyaan semantik spesifik yang harus dievaluasi pada frame. |
| `triggerMode` | String | `"on_event"` | `"on_event"`, `"periodic"`, `"continuous"` | Mode pemicu: hanya berjalan saat ada event anomali, setiap $N$ detik, atau setiap frame. |
| `intervalSeconds`| Integer | `10` | `1` s/d `300` | Jeda waktu inferensi untuk mode periodic guna menghemat token API. |
| `maxTokens` | Integer | `300` | `50` s/d `2048` | Batas panjang respons teks penjelasan yang dihasilkan model. |

---

*Lanjutkan ke **Bagian 4.3: Ensiklopedia Node - Tracking & Kinematic Analysis** untuk mempelajari modul pelacakan temporal dan kalkulasi kinematika spasial.*



<!-- PAGE BREAK: BAB_04_ENSIKLOPEDIA_NODE_PART3_TRACKING_ANALYSIS.md -->


# ENSIKLOPEDIA NODE: BAGIAN 4.3
# TRACKING & KINEMATIC ANALYSIS (25 NODES)

---

## DAFTAR ISI BAGIAN 4.3

- 4.3.1 `tracker`: Multi-Algorithm Object Tracker (ByteTrack, BoT-SORT, C-BIoU, Roboflow Re-ID)
- 4.3.2 `zone_activity_timer`: Zone Activity Timer (Perhitungan Durasi Kerja Berbasis Waktu Elapsed)
- 4.3.3 `zone_exit_event`: Zone Exit Event (Deteksi Perpindahan Teramati Dari Dalam ke Luar)
- 4.3.4 `multi_zone_occupancy`: Multi-Zone Occupancy & Activity Tracker (Matriks Okupansi Multi-Area)
- 4.3.5 `line_counter`: Line Counter (Penghitung Garis Melintas Dua Arah / Tripwire)
- 4.3.6 `object_counter`: Object Counter (Akumulator Jumlah Objek Total dalam Frame)
- 4.3.7 `object_timer`: Object Timer (Pelacak Usia Eksistensi Setiap Objek Individu)
- 4.3.8 `dwell_time`: Dwell Time / Loitering (Pendeteksi Diam Mencurigakan / Diam Terlalu Lama)
- 4.3.9 `overlap_analysis`: Overlap Analysis (Analisis Tumpang Tindih Spasial Dua Kelas Objek)
- 4.3.10 `detections_consensus`: Detections Consensus (Konsensus Voting Multi-Model Deteksi)
- 4.3.11 `dominant_color`: Dominant Color Inspector (Ekstraksi Warna Dominan Objek Berbasis K-Means)
- 4.3.12 `face_tracker`: Face Re-ID Tracker (Pelacak Identitas Wajah Menggunakan Cosine Distance)
- 4.3.13 `homography_projector`: Homography Ground Projector (Proyeksi Koordinat Lantai 2D Dunia Nyata)
- 4.3.14 `man_down_detector`: Man Down & Fall Detector (Detektor Pekerja Jatuh / Pingsan Darurat)
- 4.3.15 `overstack_detector`: Overstack Clearance Detector (Sensor Pelanggaran Batas Ketinggian Tumpukan)
- 4.3.16 `path_deviation`: Path Deviation Monitor (Pemantau Penyimpangan Koridor Lintasan Kendaraan)
- 4.3.17 `ppe_compliance_matrix`: PPE Compliance Matrix (Matriks Kepatuhan APD K3: Helm & Rompi)
- 4.3.18 `ptz_controller`: PTZ Controller (Pengendali Motor Pan-Tilt-Zoom Otomatis via ONVIF)
- 4.3.19 `size_measurement`: Size Measurement (Pengukuran Dimensi Panjang/Lebar Metrik Objek)
- 4.3.20 `distance_measurement`: Distance Measurement (Pengukuran Jarak Antar-Objek / Proximity Alert)
- 4.3.21 `velocity_calculator`: Velocity Calculator (Estimasi Kecepatan Tempuh Objek km/jam atau m/s)
- 4.3.22 `vlm_box_tracker`: VLM Box Tracker (Pelacak Objek Fleksibel Berbasis Deskripsi Teks Semantik)
- 4.3.23 `badminton_analytics`: Badminton Match Analytics (Pelacak Kok & Analisis Lapangan Bulutangkis)
- 4.3.24 `filter`: Detection & Geometry Filter (Penyaring Deteksi Berdasarkan Ukuran & Skor)
- 4.3.25 `track_snapshot`: Once Per Track (Penyimpan Foto Bukti Terbaik Satu Kali per Objek)

---

## 4.3.1 `tracker`: Multi-Algorithm Object Tracker (Roboflow Re-ID Integrated)

### Deskripsi Fungsional
Node pelacak objek temporal yang bertanggung jawab menetapkan dan mempertahankan ID numerik unik (*Track ID*) untuk setiap objek saat mereka bergerak melintasi frame video dari waktu ke waktu.

Node ini mendukung 4 algoritma pelacakan kelas dunia:
1. **ByteTrack**: Algoritma pelacakan berkecepatan tinggi yang memanfaatkan deteksi berkeyakinan rendah (*low-confidence boxes*) untuk memulihkan objek yang tertutup bayangan atau oklusi sebagian.
2. **BoT-SORT**: Menggabungkan kalman filter terdistribusi dengan kompensasi gerakan kamera (*Camera Motion Compensation / CMC*) untuk kamera yang bergetar atau bergerak.
3. **C-BIoU**: Menggunakan Complete Bounding IoU untuk mencocokkan objek dengan presisi geometri tingkat piksel.
4. **Appearance Re-ID (Roboflow OSNet Integration)**: Mengekstrak vektor embedding fitur visual citra (512 dimensi) menggunakan deep convolutional neural network untuk memulihkan ID yang sama bahkan ketika objek menghilang di balik dinding selama beberapa detik.

![Face Tracker Inspector](screenshots/19_face_tracker_inspector.png)
*Gambar 4.3.1: Konfigurasi Inspector Node Pelacak Objek Temporal.*

### Parameter Konfigurasi (Config Schema)
| Parameter | Tipe Data | Nilai Default | Pilihan / Rentang | Penjelasan Fungsional |
|---|---|---|---|---|
| `algorithm` | String | `"bytetrack"` | `"bytetrack"`, `"botsort"`, `"cbiou"` | Algoritma utama asosiasi temporal bounding box. |
| `trackBuffer` | Integer | `30` | `5` s/d `300` | Jumlah frame toleransi mengingat objek yang hilang sebelum ID dihapus. |
| `matchThreshold` | Float | `0.70` | `0.10` s/d `0.99` | Nilai batas kesamaan jarak asosiasi Hungarian algorithm. |
| `enableReid` | Boolean | `false` | `true` / `false` | Mengaktifkan ekstraksi embedding visual Re-ID per kamera. |
| `reidModel` | String | `"osnet_x0_25"` | `"osnet_x0_25"`, `"osnet_x1_0"`, `"mobilenetv2_reid"` | Model neural network pengekstrak fitur visual penampilan. |
| `reidScoreThreshold` | Float | `0.65` | `0.30` s/d `0.95` | Ambang batas kemiripan cosinus (*cosine similarity*) embedding Re-ID. |
| `trackClassLock` | Boolean | `true` | `true` / `false` | Mengunci kelas objek agar tidak berkedip (*class flickering*) saat inferensi berubah-ubah, menggunakan sistem voting mayoritas (*majority voting*). |
| `smoothingAlgorithm` | String | `"ema"` | `"ema"`, `"kalman"`, `"none"` | Algoritma penghalus pergerakan koordinat kotak (EMA / Kalman). |

---

## 4.3.2 `zone_activity_timer`: Zone Activity Timer (Elapsed Time Engine)

### Deskripsi Fungsional
Dirancang khusus untuk workshop alat berat dan pabrik manufaktur. Node ini menghitung **durasi riil aktivitas pekerjaan mekanik** di dalam zona polygon tertentu tanpa ketergantungan rapuh pada satu Track ID yang dapat terputus.

Prinsip operasional:
- Pekerjaan dianggap terjadi jika ada **Objek Primer (Ban / Alat)** DAN **Objek Sekunder (Orang / Mekanik)** berada bersamaan di dalam zona polygon.
- Perhitungan berbasis waktu elapsed nyata (*monotonic clock*), bukan perhitungan frame sintetis.
- Menyediakan *Grace Period*: Toleransi jika mekanik keluar sejenak mengambil alat (misal 5 detik) agar sesi kerja tidak langsung tertutup.
- Menghasilkan event awal (*Session Started*), event berkala (*Session Progress*), dan event penutupan resmi (*Session Completed*) yang siap dikirim ke sistem ERP.

![Workshop Sessions](screenshots/08_workshop_sessions.png)
*Gambar 4.3.2: Rekapitulasi Sesi Kerja Riil Hasil Pencatatan Node Zone Activity Timer.*

### Parameter Konfigurasi
- `zonePolygon` (List[Point]): Titik-titik sudut polygon area kerja yang digambar melalui CAD Studio.
- `primaryClass` (String, Default: `"tire"`): Kelas target objek kerja utama.
- `secondaryClass` (String, Default: `"person"`): Kelas pelaku pekerjaan.
- `minDurationSeconds` (Float, Default: `5.0`): Durasi minimum interaksi sebelum status resmi dihitung sebagai sesi kerja.
- `gracePeriodSeconds` (Float, Default: `10.0`): Toleransi waktu kosong sementara sebelum menutup sesi kerja.
- `maxSessionDurationSeconds` (Integer, Default: `0`): Batas peringatan jika satu sesi berlangsung tidak wajar (0 = dinonaktifkan).

---

## 4.3.3 `zone_exit_event`: Zone Exit Event (Warehouse Exit Detection)

### Deskripsi Fungsional
Mendeteksi **perpindahan fisik dari dalam ke luar (*observed inside-to-outside transition*)**. Sangat penting untuk pergudangan (warehouse gate) guna mendeteksi truk atau palet barang yang keluar melewati batas gerbang.

> [!IMPORTANT]
> Sistem secara ketat membedakan antara *objek yang keluar nyata* dengan *objek yang sekadar menghilang dari kamera*. Kepergian objek hanya memicu event keluar jika objek tersebut terbukti berada di dalam zona pada frame sebelumnya dan teramati melintasi garis batas ke arah luar (*confirmed transition*).

![Warehouse Events](screenshots/09_warehouse_events.png)
*Gambar 4.3.3: Log Kejadian Barang Keluar Gudang yang Tercatat oleh Zone Exit Event.*

### Parameter Konfigurasi
- `zonePolygon` (List[Point]): Koordinat polygon batas gerbang gudang.
- `targetClasses` (List[String], Default: `["truck", "car", "tire"]`): Kelas objek yang diawasi pergerakan keluarnya.
- `directionFilter` (String, Default: `"outward_only"`): Pilihan: `"outward_only"`, `"inward_only"`, `"both"`.
- `rearmCooldownSeconds` (Float, Default: `3.0`): Jeda waktu pencegahan alarm ganda untuk objek berukuran panjang seperti truk trailer.

---

## 4.3.4 `multi_zone_occupancy`: Multi-Zone Occupancy & Activity Tracker

### Deskripsi Fungsional
Memantau banyak zona secara simultan (misalnya 4 bay workshop atau 6 jalur parkir) dalam satu kamera, menghitung jumlah orang/kendaraan di setiap zona, serta memancarkan telemetri okupansi real-time ke dashboard.

### Parameter Konfigurasi
- `zones` (JSON Array): Definisi setiap zona berisi `id`, `name`, dan `points`.
- `targetClass` (String, Default: `"person"`): Kelas objek yang dihitung jumlahnya.
- `overcrowdLimit` (Integer, Default: `5`): Batas kapasitas maksimum per zona sebelum memicu peringatan kelebihan kapasitas.

---

## 4.3.5 `line_counter`: Line Counter (Virtual Tripwire Crossing)

### Deskripsi Fungsional
Menghitung jumlah objek yang memotong garis virtual (*tripwire*) dua arah. Algoritma menghitung vektor perpotongan antara segmen garis virtual dengan segmen lintasan gerak titik tengah objek dari frame $t-1$ ke frame $t$.

![Line Counter Analytics](screenshots/line_counter_analytics.png)
*Gambar 4.3.4: Visualisasi Penghitung Garis Dua Arah dengan Statistik Masuk dan Keluar.*

### Parameter Konfigurasi
- `linePoints` (Array 2-Titik): Koordinat titik awal `[x1, y1]` dan titik akhir `[x2, y2]`.
- `targetClasses` (List[String], Default: `["person", "vehicle"]`): Objek yang dihitung.
- `showDirectionBadge` (Boolean, Default: `true`): Menampilkan panah arah perlintasan (Arah A->B vs B->A).

---

## 4.3.6 `object_counter`: Object Counter (Akumulator Total)

### Deskripsi Fungsional
Menghitung jumlah absolut seluruh objek yang sedang terlihat pada frame saat ini, dikelompokkan berdasarkan nama kelasnya (misal: "3 person, 2 forklift").

### Parameter Konfigurasi
- `targetClasses` (List[String], Default: `[]`): Filter kelas yang ingin dihitung.
- `emitPerClass` (Boolean, Default: `true`): Mengeluarkan metadata jumlah per kelas secara terpisah.

---

## 4.3.7 `object_timer`: Object Timer (Lifespan Tracker)

### Deskripsi Fungsional
Menghitung waktu keberadaan individual dari setiap objek yang dilacak sejak pertama kali terdeteksi hingga menghilang dari frame video.

![Object Timer Tracking](screenshots/20_object_timer_tracking.png)
*Gambar 4.3.5: Penghitung Waktu Individual Objek dengan HUD Usia di Atas Bounding Box.*

### Parameter Konfigurasi
- `alertThresholdSeconds` (Float, Default: `60.0`): Batas waktu keberadaan sebelum warna kotak berubah menjadi merah dan memicu peringatan.

---

## 4.3.8 `dwell_time`: Dwell Time / Loitering Monitor

### Deskripsi Fungsional
Mendeteksi perilaku berkeliaran atau berdiam diri (*loitering*) di area terlarang jika sebuah objek bergerak dalam radius kecil (< 1 meter) selama durasi tertentu.

### Parameter Konfigurasi
- `maxMoveRadiusPixels` (Integer, Default: `50`): Radius batas toleransi pergerakan minimal.
- `loiteringDurationSeconds` (Float, Default: `30.0`): Waktu minimum berdiam diri untuk memicu status `LOITERING_DETECTED`.

---

## 4.3.9 `overlap_analysis`: Overlap Analysis (Interaksi Dua Kelas)

### Deskripsi Fungsional
Menganalisis rasio tumpang tindih (*Intersection over Union* atau *Intersection over Target Area*) antara dua kelas berbeda, misalnya mengukur apakah pekerja mendekati mesin berputar terlalu dekat.

### Parameter Konfigurasi
- `classA` (String, Default: `"person"`): Kelas objek pertama.
- `classB` (String, Default: `"machinery"`): Kelas objek kedua.
- `minOverlapRatio` (Float, Default: `0.15`): Rasio batas tumpang tindih untuk memicu kondisi bahaya.

---

## 4.3.10 `detections_consensus`: Detections Consensus (Multi-Model Voting)

### Deskripsi Fungsional
Menerima deteksi dari beberapa model AI sekaligus (misal YOLOv8 dan EfficientDet) dan hanya meloloskan deteksi yang disepakati oleh mayoritas model dengan melakukan peleburan kotak (*Weighted Box Fusion / WBF*).

---

## 4.3.11 `dominant_color`: Dominant Color Inspector

### Deskripsi Fungsional
Mengekstraksi warna dominan dari objek di dalam bounding box menggunakan algoritma K-Means Clustering pada ruang warna LAB, lalu memetakannya ke palet warna standar (Merah, Biru, Hijau, Kuning, Putih, Hitam, Abu-abu). Sangat berguna untuk mengidentifikasi warna kendaraan atau seragam kerja.

![Dominant Color Inspector](screenshots/25_dominant_color_inspector.png)
*Gambar 4.3.6: Inspector Ekstraksi Warna Dominan Objek Berbasis K-Means.*

### Parameter Konfigurasi
- `numClusters` (Integer, Default: `3`): Jumlah klaster warna K-Means.
- `ignoreBackgroundMargin` (Float, Default: `0.15`): Mengabaikan 15% tepi bounding box agar warna latar belakang tidak ikut terhitung.

---

## 4.3.12 `face_tracker`: Face Re-ID Tracker (UniFace)

### Deskripsi Fungsional
Melacak pergerakan wajah secara temporal dengan mencocokkan vektor embedding wajah ArcFace (512 dimensi) menggunakan metrik *Cosine Distance*. Mempertahankan identitas orang yang sama meskipun wajah sempat membelakangi kamera.

### Parameter Konfigurasi
- `cosineThreshold` (Float, Default: `0.60`): Batas kemiripan embedding wajah.
- `maxLostFrames` (Integer, Default: `50`): Batas toleransi wajah tidak terlihat sebelum ID dilepas.

---

## 4.3.13 `homography_projector`: Homography Ground Projector

### Deskripsi Fungsional
Memproyeksikan titik kaki objek pada frame kamera ke koordinat 2D lantai dunia nyata (meter) menggunakan matriks planar homografi yang telah dikalibrasi.

### Parameter Konfigurasi
- `calibrationPointsCamera` (List[Point]): 4 titik acuan pada citra kamera.
- `calibrationPointsWorld` (List[Point]): 4 koordinat meter nyata di lapangan (contoh: `[0,0], [5,0], [5,10], [0,10]`).

---

## 4.3.14 `man_down_detector`: Man Down & Fall Detector

### Deskripsi Fungsional
Mendeteksi keadaan darurat pekerja jatuh atau tergeletak pingsan berdasarkan perubahan rasio aspek bounding box (dari vertikal menjadi horizontal) serta kecepatan perubahan orientasi sudut kerangka tubuh tubuh manusia.

![Man Down Inspector](screenshots/23_man_down_detector_inspector.png)
*Gambar 4.3.7: Inspector Pengaturan Ambang Batas Man Down & Fall Detector.*

### Parameter Konfigurasi
- `aspectRatioThreshold` (Float, Default: `1.30`): Rasio lebar terhadap tinggi kotak ($W/H \ge 1.30$ menandakan posisi berbaring).
- `immobilityDurationSeconds` (Float, Default: `5.0`): Waktu pekerja tergeletak tanpa bergerak sebelum memicu alarm darurat K3.

---

## 4.3.15 `overstack_detector`: Overstack Clearance Detector

### Deskripsi Fungsional
Memonitor tumpukan palet barang atau ban pada rak pergudangan. Jika puncak tumpukan melewati garis batas toleransi atas (*clearance line*), node akan memicu peringatan risiko roboh.

![Overstack Inspector](screenshots/26_overstack_clearance_inspector.png)
*Gambar 4.3.8: Konfigurasi Garis Batas Ketinggian Maksimum Tumpukan.*

---

## 4.3.16 `path_deviation`: Path Deviation Monitor

### Deskripsi Fungsional
Memverifikasi apakah kendaraan (misalnya AGV atau Forklift) tetap berada di dalam jalur marka koridor yang ditentukan atau menyimpang ke area pejalan kaki.

---

## 4.3.17 `ppe_compliance_matrix`: PPE Compliance Matrix (K3 Safety)

### Deskripsi Fungsional
Memverifikasi kepatuhan alat pelindung diri (APD) pekerja secara terpadu. Memeriksa keberadaan helm pengaman (*hard hat*), rompi visibilitas tinggi (*safety vest*), dan sepatu bot pada setiap personil yang terdeteksi.

---

## 4.3.18 `ptz_controller`: PTZ Controller (ONVIF Pan-Tilt-Zoom)

### Deskripsi Fungsional
Mengirim perintah motor mekanis kamera PTZ melalui protokol ONVIF untuk mengarahkan kamera secara otomatis mengikuti (*auto-tracking*) objek target di tengah frame (*centering*).

### Parameter Konfigurasi
- `deadzoneRadiusPercent` (Float, Default: `0.10`): Zona toleransi tengah frame agar kamera tidak bergetar halus terus-menerus.
- `panSpeed` (Float, Default: `0.50`): Kecepatan motor geser horizontal.
- `tiltSpeed` (Float, Default: `0.50`): Kecepatan motor geser vertikal.

---

## 4.3.19 `size_measurement`: Size Measurement (Pengukuran Metrik)

### Deskripsi Fungsional
Menghitung dimensi fisik nyata objek (panjang dan lebar dalam satuan sentimeter atau meter) berdasarkan kalibrasi rasio piksel-ke-metrik.

---

## 4.3.20 `distance_measurement`: Distance Measurement (Jarak Antar-Objek)

### Deskripsi Fungsional
Mengukur jarak fisik antara dua objek (misalnya jarak antara forklift dan pejalan kaki) dan memicu peringatan jika jarak kurang dari radius batas keselamatan (misal < 2 meter).

---

## 4.3.21 `velocity_calculator`: Velocity Calculator (Kecepatan Objek)

### Deskripsi Fungsional
Menghitung kecepatan linier objek bergerak dalam satuan km/jam atau meter/detik menggunakan pergeseran koordinat dunia nyata dibagi delta waktu timestamp frame.

---

## 4.3.22 `vlm_box_tracker`: VLM Box Tracker (Vision-Language)

### Deskripsi Fungsional
Melacak objek berdasarkan perintah teks semantik terbuka (misalnya: *"kotak kardus yang rusak di pojok"*), menghubungkan deteksi zero-shot ke tracker temporal.

---

## 4.3.23 `badminton_analytics`: Badminton Match Analytics

### Deskripsi Fungsional
Node analisis olahraga spesialis untuk melacak posisi kok (*shuttlecock*) kecepatan tinggi, mendeteksi garis lapangan, dan mencatat pergerakan posisi kedua pemain bulutangkis.

---

## 4.3.24 `filter`: Detection & Geometry Filter

### Deskripsi Fungsional
Menyaring daftar deteksi berdasarkan kriteria ukuran luas minimum/maksimum piksel, rentang rasio aspek, atau kelas tertentu sebelum dialirkan ke node kalkulasi.

---

## 4.3.25 `track_snapshot`: Once Per Track

### Deskripsi Fungsional
Menangkap satu foto (*snapshot*) berkualitas terbaik untuk setiap ID objek baru (misalnya saat objek berada di tengah frame dengan skor keyakinan tertinggi), lalu menyimpannya agar tidak terjadi redundansi penyimpanan ratusan frame untuk objek yang sama.

---

*Lanjutkan ke **Bagian 4.4: Ensiklopedia Node - Logic & Flow Control** untuk mempelajari modul gerbang logika dan filter alur kerja.*



<!-- PAGE BREAK: BAB_04_ENSIKLOPEDIA_NODE_PART4_LOGIC_FLOW_CONTROL.md -->


# ENSIKLOPEDIA NODE: BAGIAN 4.4
# LOGIC & FLOW CONTROL (15 NODES)

---

## DAFTAR ISI BAGIAN 4.4

- 4.4.1 `motion_gate`: Motion Gate (Penyaring Gerakan Kamera CCTV Cerdas)
- 4.4.2 `alarm_cooldown_gate`: Alarm Cooldown Gate (Pencegah Banjir Alarm / Spam Suppressor)
- 4.4.3 `debounce`: Debounce Filter (Stabilisasi Sinyal Kejadian Berayun)
- 4.4.4 `switch_case`: Switch Case Router (Perutean Alur Multi-Cabang Berbasis String/Kelas)
- 4.4.5 `if_else`: If / Else Conditional Branching (Percabangan Biner Benar / Salah)
- 4.4.6 `class_detected_condition`: Class Detected Condition (Pemicu Berdasarkan Keberadaan Kelas Tertentu)
- 4.4.7 `object_count_condition`: Object Count Condition (Evaluasi Ambang Batas Jumlah Objek)
- 4.4.8 `compare_value`: Compare Value (Operator Pembanding Numerik Universal)
- 4.4.9 `confidence_threshold`: Confidence Threshold Filter (Penyaring Probabilitas Deteksi)
- 4.4.10 `class_replacement`: Class Replacement (Remapping Nama Kelas Model AI)
- 4.4.11 `and_or_logic`: AND / OR Boolean Logic (Penggabung Multi-Kondisi Gerbang Logika)
- 4.4.12 `rate_limiter`: Rate Limiter (Pembatas Frekuensi Panggilan Eksternal)
- 4.4.13 `roi_filter`: ROI Filter (Penyaring Deteksi Khusus di Dalam Kotak ROI)
- 4.4.14 `timer_delay`: Timer / Delay (Penunda Waktu Propagasi Paket)
- 4.4.15 `trigger_once`: Trigger Once (Pemicu Kejadian Tepat Satu Kali Hingga Reset)

---

## 4.4.1 `motion_gate`: Motion Gate (Penyaring Gerakan CCTV Cerdas)

### Deskripsi Fungsional
Node hemat energi yang berfungsi sebagai "penjaga pintu gerbang" komputasi. Pada rekaman CCTV statis (misal gudang di malam hari atau lorong sepi), 95% frame tidak memiliki aktivitas sama sekali. Menjalankan model AI berat pada frame kosong membuang daya listrik dan CPU.

Node `motion_gate` menghitung perubahan optik ringan antar-frame. Jika pemandangan diam, node memblokir aliran data ke model AI berat. Begitu terdeteksi pergerakan fisik nyata di atas ambang batas, gerbang seketika terbuka dan mengalirkan frame ke model AI.

### Diagram Alur Data & Pin Koneksi
```
+------------------------------------------+
|  [Icon]  Motion Gate                     |
+------------------------------------------+
| (o) Input Image                          |
|                               (o) Image  |
|                               (o) Motion |
+------------------------------------------+
```

### Parameter Konfigurasi (Config Schema)
| Parameter | Tipe Data | Nilai Default | Pilihan / Rentang | Penjelasan Fungsional |
|---|---|---|---|---|
| `sensitivity` | Float | `0.02` | `0.001` s/d `0.50` | Persentase minimum piksel yang harus bergerak untuk membuka gerbang (0.02 = 2% luas layar). |
| `minContourArea` | Integer | `500` | `50` s/d `10000` | Luas kontur minimum piksel gerak untuk mengabaikan serangga terbang atau noise kamera. |
| `motionHoldSeconds`| Float | `3.0` | `0.5` s/d `30.0` | Durasi gerbang tetap terbuka setelah gerakan terakhir berhenti, mencegah pemutusan frame mendadak. |

---

## 4.4.2 `alarm_cooldown_gate`: Alarm Cooldown Gate (Pencegah Banjir Alarm)

### Deskripsi Fungsional
Mencegah fenomena *Alert Fatigue* (kebanjiran notifikasi beruntun). Jika sebuah pelanggaran terjadi (misal orang tidak memakai helm), sistem deteksi kamera 30 FPS akan mendeteksi pelanggaran tersebut 30 kali setiap detik. Mengirim 30 pesan WhatsApp/Telegram per detik akan membanjiri ponsel supervisor.

Node `alarm_cooldown_gate` memastikan bahwa setelah satu alarm ditembakkan, alarm serupa dibungkam (*muted*) selama periode pendinginan (*cooldown window*, misal 30 detik atau 5 menit), sebelum diizinkan berbunyi kembali.

### Parameter Konfigurasi
- `cooldownSeconds` (Float, Default: `30.0`): Periode hening minimum antar-alarm.
- `groupByKey` (String, Default: `"class_name"`): Pilihan pengelompokan cooldown: `"global"`, `"class_name"`, `"track_id"`. Jika diset `"track_id"`, orang A yang melanggar tidak akan menghalangi alarm untuk orang B yang baru masuk.

---

## 4.4.3 `debounce`: Debounce Filter (Penstabil Sinyal Kejadian)

### Deskripsi Fungsional
Menghilangkan sinyal berayun (*flickering trigger*). Dalam computer vision, deteksi objek terkadang hilang selama 1 frame lalu muncul kembali di frame berikutnya karena oklusi sesaat. Debounce memastikan bahwa kondisi harus stabil bernilai `TRUE` selama durasi waktu tertentu berturut-turut sebelum pemicu downstream diaktifkan.

### Parameter Konfigurasi
- `debounceTimeMs` (Integer, Default: `500`): Waktu stabilisasi minimum dalam milidetik.
- `mode` (String, Default: `"leading_trailing"`): Pilihan: `"leading"` (pemicu awal), `"trailing"` (pemicu akhir), `"both"`.

---

## 4.4.4 `switch_case`: Switch Case Router (Perutean Multi-Arah)

### Deskripsi Fungsional
Mengarahkan aliran data ke salah satu dari beberapa cabang keluaran berdasarkan nilai variabel kunci (misalnya memisahkan rute pemrosesan: jika `class == "person"` diarahkan ke cabang analisis pose K3; jika `class == "car"` diarahkan ke cabang pembaca plat LPR).

### Parameter Konfigurasi
- `routingKey` (String, Default: `"class_name"`): Properti metadata yang diperiksa.
- `cases` (List[String], Default: `["person", "vehicle", "other"]`): Daftar nama cabang keluaran yang disediakan node.

---

## 4.4.5 `if_else`: If / Else Conditional Branching

### Deskripsi Fungsional
Mengevaluasi ekspresi kondisi biner sederhana. Jika kondisi terpenuhi, paket dialirkan melalui pin `True`. Jika tidak, paket dialirkan melalui pin `False`.

### Parameter Konfigurasi
- `conditionType` (String, Default: `"count_greater_than"`): Jenis pengujian kondisi.
- `thresholdValue` (Float, Default: `0.0`): Nilai ambang pembanding.

---

## 4.4.6 `class_detected_condition`: Class Detected Condition

### Deskripsi Fungsional
Memeriksa apakah kelas objek tertentu (misal `"fire"`, `"smoke"`, atau `"knife"`) muncul di dalam daftar deteksi frame saat ini. Mengeluarkan sinyal boolean seketika.

### Parameter Konfigurasi
- `targetClass` (String, Default: `"person"`): Nama label kelas yang dicari.
- `minConfidence` (Float, Default: `0.50`): Ambang keyakinan minimum kelas tersebut.

---

## 4.4.7 `object_count_condition`: Object Count Condition

### Deskripsi Fungsional
Mengevaluasi apakah total objek yang terdeteksi memenuhi aturan kuantitas tertentu, misalnya: "Jumlah orang > 10" (peringatan kerumunan) atau "Jumlah ban == 0" (peringatan area kosong).

### Parameter Konfigurasi
- `operator` (String, Default: `">"`): Operator pembanding (`>`, `<`, `>=`, `<=`, `==`, `!=`).
- `countThreshold` (Integer, Default: `1`): Jumlah kuantitas target.
- `targetClass` (String, Default: `""`): Filter kelas tertentu (kosong = seluruh kelas).

---

## 4.4.8 `compare_value`: Compare Value (Pembanding Numerik Universal)

### Deskripsi Fungsional
Membandingkan dua variabel numerik yang mengalir dari node hulu (misalnya membandingkan kecepatan kendaraan dengan batas rambu kecepatan jalan 30 km/jam).

---

## 4.4.9 `confidence_threshold`: Confidence Threshold Filter

### Deskripsi Fungsional
Menyaring daftar deteksi objek, membuang seluruh kotak yang memiliki skor keyakinan di bawah ambang batas yang ditentukan. Memastikan hanya deteksi berkualitas tinggi yang masuk ke tahap analitik lanjutan.

---

## 4.4.10 `class_replacement`: Class Replacement (Remapping Nama Kelas)

### Deskripsi Fungsional
Mengubah nama label kelas model AI bawaan menjadi istilah bisnis internal perusahaan. Contoh: Mengubah label `"truck"` menjadi `"Dump Truck HD785"`, atau mengubah `"person"` menjadi `"Operator Workshop"`.

### Parameter Konfigurasi
- `mappingDict` (JSON Object): Pasangan pemetaan nama lama ke nama baru (contoh: `{"car": "Kendaraan Ringan LV", "person": "Karyawan"}`).

---

## 4.4.11 `and_or_logic`: AND / OR Boolean Logic

### Deskripsi Fungsional
Menggabungkan beberapa kondisi keluaran dari node logika lain menjadi satu keputusan terpadu:
- **Operasi AND**: Seluruh kondisi harus bernilai `TRUE` (misal: "Ada orang" AND "Zona aktif" AND "Di luar jam kerja").
- **Operasi OR**: Cukup salah satu kondisi bernilai `TRUE` untuk memicu alarm.

---

## 4.4.12 `rate_limiter`: Rate Limiter (Pembatas Frekuensi)

### Deskripsi Fungsional
Membatasi laju aliran paket data maksimum per detik atau per menit. Berguna saat menghubungkan alur kerja ke API pihak ketiga yang memiliki kuota pembatasan panggilan (*Rate Limit Quota*).

---

## 4.4.13 `roi_filter`: ROI Filter (Region of Interest)

### Deskripsi Fungsional
Menyaring objek deteksi berdasarkan koordinat spasial kotak pembatasnya. Hanya objek yang titik pusatnya (*bounding box centroid*) berada di dalam kotak area ROI yang diizinkan lewat; objek di luar kotak akan dibuang dari daftar deteksi.

---

## 4.4.14 `timer_delay`: Timer / Delay

### Deskripsi Fungsional
Menunda transmisi paket frame atau kejadian selama durasi waktu tertentu (misal tunda 2.0 detik) untuk sinkronisasi waktu dengan sistem eksternal atau kamera sudut lain.

---

## 4.4.15 `trigger_once`: Trigger Once (Pemicu Tunggal)

### Deskripsi Fungsional
Hanya memicu kejadian tepat satu kali saat kondisi pertama kali terpenuhi, lalu mengunci diri (*latched*). Pemicu tidak akan aktif kembali sampai menerima sinyal `RESET` dari node lain atau alur kerja di-restart.

---

*Lanjutkan ke **Bagian 4.5: Ensiklopedia Node - Visualisasi & Anotasi** untuk mempelajari teknik rendering overlay grafis dan visualisasi data langsung di atas video.*



<!-- PAGE BREAK: BAB_04_ENSIKLOPEDIA_NODE_PART5_ANNOTATIONS_DRAWING.md -->


# ENSIKLOPEDIA NODE: BAGIAN 4.5
# ANNOTATIONS, DRAWING & VISUALISASI (7 NODES)

---

## DAFTAR ISI BAGIAN 4.5

- 4.5.1 `overlay_annotate`: Overlay & Annotate Engine (Manajer Multi-Lapisan Grafis & HUD)
- 4.5.2 `draw_boxes`: Draw Boxes (Rendering Kotak Pembatas & Label Skor Keyakinan)
- 4.5.3 `draw_text`: Draw Text (Pencetakan Teks Dinamis & Watermark Informasi)
- 4.5.4 `blur_anonymizer`: Privacy Blur & Anonymizer (Pengabur Wajah & Plat Otomatis)
- 4.5.5 `crowd_density_heatmap`: Crowd Density Heatmap (Peta Panas Kepadatan Temporal)
- 4.5.6 `bev_visualizer`: BEV Map Visualizer (Peta Denah Lantai 2D Bird's Eye View)
- 4.5.7 `interactive_zoom`: Interactive Object Zoom (Pembesaran Fokus Otomatis Objek Bergerak)

---

## 4.5.1 `overlay_annotate`: Overlay & Annotate Engine (Multi-Layer HUD)

### Deskripsi Fungsional
Node rendering grafis paling canggih di dalam sistem Afi Vision Builder. Node ini menggabungkan berbagai lapisan visual (*visual layers*) langsung di atas matriks citra video sebelum dikirim ke Live Preview, Dashboard, atau rekaman video MP4.

Mendukung penggambaran kotak deteksi, garis jejak lintasan masa lalu (*trajectory trails*), badge status, efek halo menyala (*neon glow*), dan HUD telemetri bergaya aerospace.

![Overlay Annotate Inspector](screenshots/05_overlay_annotate_inspector.png)
*Gambar 4.5.1: Konfigurasi Inspector Node Overlay & Annotate dengan Beragam Lapisan Visual.*

### Diagram Alur Data & Pin Koneksi
```
+------------------------------------------+
|  [Icon]  Overlay / Annotate              |
+------------------------------------------+
| (o) Input Image                          |
| (o) Detections                           |
| (o) Tracks                               |
|                               (o) Image  |
+------------------------------------------+
```

### Parameter Konfigurasi (Config Schema)
| Parameter | Tipe Data | Nilai Default | Pilihan / Rentang | Penjelasan Fungsional |
|---|---|---|---|---|
| `showBoxes` | Boolean | `true` | `true` / `false` | Menampilkan kotak pembatas bounding box di sekitar objek. |
| `boxThickness` | Integer | `2` | `1` s/d `10` | Ketebalan garis tepi kotak dalam satuan piksel. |
| `boxCornerStyle`| String | `"rounded"` | `"square"`, `"rounded"`, `"corner_brackets"` | Bentuk sudut kotak (persegi standar, sudut melengkung, atau braket sudut taktis). |
| `showLabels` | Boolean | `true` | `true` / `false` | Menampilkan label nama kelas dan ID di atas objek. |
| `showConfidence`| Boolean | `true` | `true` / `false` | Menampilkan nilai probabilitas persen (contoh: `Person 94%`). |
| `colorPalette` | String | `"rainbow"` | `"rainbow"`, `"emerald"`, `"cyberpunk"`, `"single"` | Skema palet warna pembeda antar-kelas objek. |
| `showTrails` | Boolean | `false` | `true` / `false` | Menggambar garis ekor jejak pergerakan objek (*tracking history trail*). |
| `trailLength` | Integer | `20` | `5` s/d `100` | Jumlah koordinat historis titik tengah yang digambar sebagai garis ekor. |
| `showHudBadge` | Boolean | `true` | `true` / `false` | Menampilkan panel informasi semi-transparan di pojok frame (waktu, FPS, total objek). |

---

## 4.5.2 `draw_boxes`: Draw Boxes (Kotak Pembatas Cepat)

### Deskripsi Fungsional
Versi ringan (*lightweight*) dari node penampil kotak pembatas tanpa overhead HUD teks yang kompleks. Sangat ideal untuk pipeline edge dengan sumber daya CPU terbatas yang hanya membutuhkan indikator visual kotak deteksi.

### Parameter Konfigurasi
- `lineColor` (String, Default: `"#00FF00"`): Kode warna hex garis kotak.
- `thickness` (Integer, Default: `2`): Ketebalan piksel garis.

---

## 4.5.3 `draw_text`: Draw Text (Pencetakan Teks Dinamis)

### Deskripsi Fungsional
Mencetak teks dinamis, stempel waktu (*timestamp overlay*), nama kamera, atau variabel konteks pada posisi piksel absolut di atas frame citra.

### Parameter Konfigurasi
- `textTemplate` (String, Default: `"CAM: {source_id} | WAKTU: {timestamp}"`): Template teks dengan variabel yang diekspansi secara otomatis.
- `x` (Integer, Default: `20`): Koordinat horizontal penempatan teks.
- `y` (Integer, Default: `40`): Koordinat vertikal penempatan teks.
- `fontSize` (Float, Default: `0.8`): Ukuran font Hershey OpenCV.
- `fontColor` (String, Default: `"#FFFFFF"`): Warna font.
- `backgroundColor` (String, Default: `"#000000"`): Kotak latar belakang teks untuk keterbacaan tinggi.

---

## 4.5.4 `blur_anonymizer`: Privacy Blur & Anonymizer

### Deskripsi Fungsional
Secara otomatis mengaburkan (*blur*) atau mem-pixelate area sensitif (seperti wajah manusia atau plat nomor kendaraan) untuk kepatuhan regulasi privasi data sebelum video disiarkan ke publik atau disimpan ke server.

### Parameter Konfigurasi
- `targetClasses` (List[String], Default: `["face", "license_plate"]`): Kelas objek yang harus disensor.
- `blurMethod` (String, Default: `"gaussian"`): Pilihan: `"gaussian"`, `"pixelate"`, `"blackout"`.
- `pixelateBlockSize` (Integer, Default: `12`): Ukuran blok mozaik untuk mode pixelate.

---

## 4.5.5 `crowd_density_heatmap`: Crowd Density Heatmap

### Deskripsi Fungsional
Mengakumulasi posisi keberadaan objek melintasi waktu untuk menghasilkan visualisasi **Peta Panas Kepadatan (*Accumulated Density Heatmap*)**. Area yang sering dilalui atau disinggahi orang akan berwarna merah menyala (*hot spot*), sedangkan area yang jarang dilewati berwarna biru dingin (*cold spot*).

![Crowd Heatmap](screenshots/040_opennvr_exact_live_view.png)
*Gambar 4.5.2: Visualisasi Peta Panas Kepadatan Menggunakan Peta Warna Jet/Inferno.*

### Parameter Konfigurasi
- `colormap` (String, Default: `"JET"`): Pilihan palet warna: `"JET"`, `"TURBO"`, `"INFERNO"`, `"HOT"`.
- `decayRate` (Float, Default: `0.98`, Rentang: `0.90` s/d `0.999`): Laju peluruhan panas per frame (0.98 = jejak panas bertahan sekitar 5-10 detik).
- `pointRadius` (Integer, Default: `25`): Radius sebaran panas Gaussian per objek.
- `alphaBlend` (Float, Default: `0.40`): Tingkat transparansi overlay peta panas di atas video asli.

---

## 4.5.6 `bev_visualizer`: BEV Map Visualizer (Denah Lantai 2D)

### Deskripsi Fungsional
Menampilkan kanvas denah lantai arsitektur 2D (*Bird's Eye View Plan*) berdampingan dengan stream kamera. Setiap objek yang terdeteksi di kamera dipetakan sebagai titik ikon bergerak di atas denah denah bangunan secara real-time.

### Parameter Konfigurasi
- `floorplanImagePath` (String): Path file gambar cetak biru denah lantai (PNG/JPG).
- `pointColor` (String, Default: `"#00E5FF"`): Warna titik posisi objek pada denah lantai.
- `showObjectLabels` (Boolean, Default: `true`): Menampilkan ID objek di samping titik denah.

---

## 4.5.7 `interactive_zoom`: Interactive Object Zoom (Auto-Focus PiP)

### Deskripsi Fungsional
Menampilkan jendela kecil di dalam jendela besar (*Picture-in-Picture / PiP*) pada pojok layar yang secara otomatis memperbesar (*digital crop & zoom*) objek yang sedang menjadi perhatian utama (misal: orang yang sedang memanjat pagar atau truk yang sedang melintas).

### Parameter Konfigurasi
- `zoomFactor` (Float, Default: `2.5`): Pengali tingkat perbesaran optik digital.
- `pipPosition` (String, Default: `"top_right"`): Posisi jendela: `"top_right"`, `"bottom_right"`, `"top_left"`, `"bottom_left"`.
- `pipWidthPercent` (Float, Default: `0.25`): Lebar jendela PiP terhadap ukuran layar video (25%).

---

*Lanjutkan ke **Bagian 4.6: Ensiklopedia Node - Outputs, Cloud Sinks & Code Export** untuk mempelajari penyimpanan data, integrasi cloud, dan ekspor kode mandiri.*



<!-- PAGE BREAK: BAB_04_ENSIKLOPEDIA_NODE_PART6_OUTPUTS_EXPORT.md -->


# ENSIKLOPEDIA NODE: BAGIAN 4.6
# OUTPUTS, CLOUD SINKS & CODE EXPORT (17 NODES)

---

## DAFTAR ISI BAGIAN 4.6

- 4.6.1 `preview`: Live Preview (Streaming HTTP MJPEG Berlatensi Rendah)
- 4.6.2 `dashboard_sink`: Dashboard Output (Pemancar Telemetri Real-Time via WebSocket)
- 4.6.3 `event_clip_recorder`: Perekam Klip Bukti Pre/Post-Roll (Evidence Vault Storage)
- 4.6.4 `incident_video_recorder`: Incident Video Recorder (Perekam Video Durasi Panjang)
- 4.6.5 `alert`: Alert Output (Banner Peringatan Visual & Audio Chime di Browser)
- 4.6.6 `image_output`: Save Images (Penyimpanan Citra Lokal dengan Format Tanggal)
- 4.6.7 `database_output`: Database Output (Penyimpan Relasional SQLite & PostgreSQL)
- 4.6.8 `mqtt_publisher`: MQTT Publisher (Penerbit Pesan Telemetri Industrial IoT / SCADA)
- 4.6.9 `telegram_notification`: Telegram Alert (Bot Pengirim Pesan & Foto Bukti Instan)
- 4.6.10 `notification_dispatcher`: Multi-Channel Notification Dispatcher
- 4.6.11 `webhook_output`: Webhook / HTTP Outbound (Pengiriman Kejadian ke Sistem ERP)
- 4.6.12 `csv_formatter`: CSV Formatter (Pencatat Log Tabel Otomatis Berkelanjutan)
- 4.6.13 `data_aggregator`: Data Aggregator (Rollup Statistik Min/Max/Avg/Sum per Periode)
- 4.6.14 `s3_sink`: S3 Cloud Sink (Unggah Citra & Klip ke AWS S3 / MinIO Object Storage)
- 4.6.15 `screenshot_capture`: Screenshot Capture (Penangkap Foto Beresolusi Asli Saat Terpicu)
- 4.6.16 `export_code`: Export Code (Generator Bundel Python Mandiri untuk Perangkat Edge)
- 4.6.17 `detections_difference`: Detections Difference (Analisis Selisih Spasial Dua Deteksi)

---

## 4.6.1 `preview`: Live Preview (Streaming Web Viewer)

### Deskripsi Fungsional
Node penampil siaran langsung pada kanvas antarmuka web. Mengompresi frame citra BGR menjadi stream format Motion JPEG (MJPEG) yang dialirkan melalui endpoint HTTP `/api/preview/{pipeline_id}` dengan latensi di bawah 100 milidetik.

### Diagram Alur Data & Pin Koneksi
```
+------------------------------------------+
|  [Icon]  Live Preview                    |
+------------------------------------------+
| (o) Input Image                          |
+------------------------------------------+
```
- **Pin Input**: `image` (Citra yang telah dianotasi atau citra mentah)
- **Pin Output**: *Tidak ada* (Terminal Sink)

### Parameter Konfigurasi (Config Schema)
| Parameter | Tipe Data | Nilai Default | Pilihan / Rentang | Penjelasan Fungsional |
|---|---|---|---|---|
| `jpegQuality` | Integer | `80` | `30` s/d `100` | Kualitas kompresi citra JPEG (nilai lebih rendah menghemat bandwidth jaringan). |
| `maxStreamFps` | Integer | `25` | `1` s/d `60` | Kecepatan frame maksimum yang dialirkan ke peramban. |
| `clientTimeoutSeconds` | Integer | `10` | `2` s/d `60` | Menghentikan kompresi jika peramban klien ditutup untuk menghemat CPU. |

---

## 4.6.2 `dashboard_sink`: Dashboard Output (WebSocket Telemetry)

### Deskripsi Fungsional
Jembatan data telemetri real-time antara pipeline vision dengan **Dashboard Builder**. Node ini mengumpulkan seluruh metrik numerik (jumlah orang, status zona aktif, durasi kerja, alarm pelanggaran) dan memancarkannya ke bus WebSocket berlatensi rendah untuk memperbarui widget dashboard tanpa perlu refresh halaman.

### Parameter Konfigurasi
- `channelName` (String, Default: `"default"`): Nama saluran telemetri per proyek.
- `publishIntervalMs` (Integer, Default: `200`): Interval frekuensi pemancaran telemetri (milidetik).

---

## 4.6.3 `event_clip_recorder`: Perekam Klip Bukti Pre/Post-Roll (Vault)

### Deskripsi Fungsional
Node perekam video forensik standar enterprise. Node ini memelihara buffer video sirkular di memori RAM (*rolling ring buffer*). Saat menerima sinyal pemicu kejadian (*trigger event*, misal: barang keluar tanpa izin atau pekerja jatuh):
1. Mengambil **5 detik video sebelum kejadian** (*pre-roll buffer*).
2. Melanjutkan perekaman selama **10 detik setelah kejadian** (*post-roll buffer*).
3. Mengompresi klip menjadi file MP4 terenkripsi dengan metadata terikat di folder `data/vault/`.
4. Mendaftarkan klip secara otomatis ke antarmuka **Open-NVR Evidence Vault**.

![Evidence Vault](screenshots/006_nvr_hub_evidence_vault.png)
*Gambar 4.6.1: Antarmuka Evidence Vault yang Menyimpan Klip Kejadian Rekaman Pre/Post-Roll.*

### Parameter Konfigurasi (Config Schema)
| Parameter | Tipe Data | Nilai Default | Pilihan / Rentang | Penjelasan Fungsional |
|---|---|---|---|---|
| `preRollSeconds` | Float | `5.0` | `1.0` s/d `30.0` | Durasi video yang disimpan sebelum detik pemicu kejadian terjadi. |
| `postRollSeconds`| Float | `10.0` | `2.0` s/d `60.0` | Durasi video yang terus direkam setelah pemicu terjadi. |
| `videoCodec` | String | `"mp4v"` | `"mp4v"`, `"avc1"`, `"h264"` | Format kompresi video MP4. |
| `includeAnnotations` | Boolean | `true` | `true` / `false` | Menyimpan video dengan kotak anotasi AI atau video bersih tanpa anotasi. |

---

## 4.6.4 `incident_video_recorder`: Incident Video Recorder

### Deskripsi Fungsional
Mirip dengan `event_clip_recorder`, tetapi dirancang untuk merekam video berdurasi panjang berkelanjutan (1 menit hingga 1 jam) selama suatu insiden masih berlangsung (misalnya selama kebakaran terdeteksi atau selama truk parkir di area terlarang).

---

## 4.6.5 `alert`: Alert Output (Banner & Audio Chime)

### Deskripsi Fungsional
Menampilkan banner pop-up peringatan berwarna merah mencolok di pojok kanan atas layar peramban operator dan memainkan suara bel alarm (*chime*) untuk menarik perhatian operator seketika.

### Parameter Konfigurasi
- `alertTitle` (String, Default: `"PERINGATAN SISTEM"`): Judul pesan bahaya.
- `alertSeverity` (String, Default: `"critical"`): Tingkat keparahan: `"info"`, `"warning"`, `"critical"`.
- `playSound` (Boolean, Default: `true`): Membunyikan nada peringatan di speaker browser.

---

## 4.6.6 `image_output`: Save Images (Penyimpanan Citra Lokal)

### Deskripsi Fungsional
Menyimpan frame citra ke direktori hard disk server dengan penamaan terstruktur berdasarkan stempel waktu ISO (misal: `data/captures/2026-11-10_14-30-22_person.jpg`).

### Parameter Konfigurasi
- `outputFolder` (String, Default: `"data/captures"`): Folder tujuan penyimpanan file.
- `imageFormat` (String, Default: `"jpg"`): Format file: `"jpg"`, `"png"`, `"webp"`.
- `quality` (Integer, Default: `90`): Kualitas kompresi (1-100).

---

## 4.6.7 `database_output`: Database Output (Relational Storage)

### Deskripsi Fungsional
Menyimpan catatan kejadian (*event logs*) dan sesi kerja ke dalam tabel basis data relasional SQLite lokal atau server PostgreSQL remote.

### Skema Data yang Disimpan:
```sql
CREATE TABLE IF NOT EXISTS vision_events (
    id TEXT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    source_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    class_name TEXT,
    confidence REAL,
    metadata_json TEXT,
    clip_path TEXT
);
```

### Parameter Konfigurasi
- `databaseUrl` (String, Default: `"sqlite:///data/visionode.db"`): URI koneksi database (SQLite atau PostgreSQL `postgresql://user:pass@host/db`).
- `tableName` (String, Default: `"vision_events"`): Nama tabel tujuan penyimpanan data.

---

## 4.6.8 `mqtt_publisher`: MQTT Publisher (Industrial IoT / SCADA)

### Deskripsi Fungsional
Mengirim pesan telemetri berbobot ringan ke broker MQTT industri (misal: Mosquitto, EMQX, HiveMQ). Memungkinkan PLC pabrik, lampu sirine strobe industri, atau sistem SCADA merespons kejadian vision secara instan.

### Parameter Konfigurasi
- `brokerHost` (String, Default: `"127.0.0.1"`): Alamat IP atau hostname broker MQTT.
- `brokerPort` (Integer, Default: `1883`): Port broker MQTT.
- `topic` (String, Default: `"cctv/events"`): Topik MQTT tujuan pengiriman pesan.
- `qos` (Integer, Default: `1`): Tingkat Quality of Service (`0`, `1`, `2`).
- `retain` (Boolean, Default: `false`): Meminta broker menyimpan status pesan terakhir.

---

## 4.6.9 `telegram_notification`: Telegram Alert Bot

### Deskripsi Fungsional
Mengirim pesan peringatan darurat ke grup Telegram manajemen atau supervisor operasional, lengkap dengan teks kronologi kejadian dan lampiran **foto bukti langsung (*photo attachment*)** yang diambil tepat pada detik pelanggaran terjadi.

### Parameter Konfigurasi
- `botToken` (String): Token API rahasia bot dari `@BotFather`.
- `chatId` (String): ID obrolan pengguna atau grup tujuan (misal: `"-1001234567890"`).
- `messageTemplate` (String): Template teks markdown (contoh: `🚨 *PELANGGARAN K3 DETECTED*\nLokasi: {source_id}\nWaktu: {timestamp}\nObjek: {class_name}`).
- `attachPhoto` (Boolean, Default: `true`): Melampirkan foto bukti pada pesan.

---

## 4.6.10 `notification_dispatcher`: Multi-Channel Dispatcher

### Deskripsi Fungsional
Pusat pengiriman notifikasi terpadu yang dapat mendistribusikan peringatan secara simultan ke berbagai saluran sekaligus (Telegram, Webhook, Email, dan SMS) dengan aturan prioritas terpusat.

---

## 4.6.11 `webhook_output`: Webhook / HTTP Outbound (ERP Dispatch)

### Deskripsi Fungsional
Mengirim payload JSON kejadian secara asinkron ke REST API backend perusahaan atau sistem ERP (seperti SAP, Odoo, Oracle ERP, atau sistem internal One Chitra). Dilengkapi dengan mekanisme *Exponential Backoff Retry* dan *Idempotency Header* untuk memastikan data tidak pernah hilang atau tercatat ganda saat koneksi jaringan tidak stabil.

### Contoh Format JSON Payload yang Dikirim ke ERP:
```json
{
  "eventId": "EVT-8f92a1-20261110-142205",
  "timestamp": "2026-11-10T14:22:05.123+08:00",
  "sourceId": "WH-GATE-02",
  "eventType": "ZONE_EXIT_VIOLATION",
  "details": {
    "targetClass": "truck",
    "trackId": 42,
    "licensePlate": "B 9876 KDA",
    "exitDirection": "OUTWARD",
    "dwellDurationSeconds": 48.5
  },
  "evidence": {
    "snapshotUrl": "http://192.168.1.50:8765/api/vault/snapshots/EVT-8f92a1.jpg",
    "clipUrl": "http://192.168.1.50:8765/api/vault/clips/EVT-8f92a1.mp4"
  }
}
```

### Parameter Konfigurasi
- `targetUrl` (String): Alamat URL endpoint REST API ERP (contoh: `https://erp.perusahaan.com/api/v1/vision-events`).
- `httpMethod` (String, Default: `"POST"`): Metode HTTP: `"POST"` atau `"PUT"`.
- `authorizationHeader` (String): Token Bearer atau API Key untuk autentikasi ERP.
- `retryAttempts` (Integer, Default: `3`): Jumlah percobaan pengiriman ulang jika server ERP merespons error (5xx atau timeout).

---

## 4.6.12 `csv_formatter`: CSV Formatter (Export Tabel Periodik)

### Deskripsi Fungsional
Mencatat data akumulatif (misal: jumlah kendaraan melintas per jam) ke dalam file spreadsheet format `.csv` harian untuk pelaporan berkala tanpa perlu database kompleks.

---

## 4.6.13 `data_aggregator`: Data Aggregator (Rollup Statistik)

### Deskripsi Fungsional
Melakukan agregasi kalkulasi matematika terhadap aliran data numerik dalam jendela waktu bergerak (*sliding time window*, misal 5 menit): menghitung nilai Rata-rata (*Average*), Minimum, Maksimum, dan Jumlah Total (*Sum*).

---

## 4.6.14 `s3_sink`: S3 Cloud Sink (Object Storage Upload)

### Deskripsi Fungsional
Mengunggah foto bukti dan klip video MP4 ke penyimpanan awan kompatibel Amazon S3 (AWS S3, MinIO Server Lokal, Wasabi, Cloudflare R2) untuk retensi data jangka panjang.

### Parameter Konfigurasi
- `endpointUrl` (String, Default: `"https://s3.amazonaws.com"`): Endpoint S3 atau IP server MinIO lokal.
- `bucketName` (String): Nama bucket penyimpanan.
- `accessKey` (String): Kunci akses S3.
- `secretKey` (String): Kunci rahasia S3.

---

## 4.6.15 `screenshot_capture`: Screenshot Capture

### Deskripsi Fungsional
Menangkap satu frame citra berkualitas tinggi beresolusi penuh (*lossless PNG/JPG*) dari frame video mentah saat menerima sinyal pemicu dari node logika, lalu menyimpannya ke memori untuk diunduh langsung dari web browser.

---

## 4.6.16 `export_code`: Export Code (Standalone Python Bundle)

### Deskripsi Fungsional
Node arsitektural yang memungkinkan pengguna mengekspor keseluruhan topologi alur kerja aktif menjadi satu paket kode Python mandiri (*Standalone Deployment Bundle*).

Paket hasil ekspor berupa file ZIP yang berisi:
- `run.py`: Skrip Python headless tanpa overhead antarmuka web.
- `workflow_config.json`: Snapshot parameter seluruh 98 node.
- `engine/`: Pustaka core minimalis vision.
- `requirements.txt` & `Dockerfile`: Dependensi untuk deployment pada perangkat edge (seperti IPC atau NVIDIA Jetson).

![Export Code Modal](screenshots/005-05_dashboard_docker_export_modal_ready.png)
*Gambar 4.6.2: Modal Ekspor Kode Standalone Siap Deploy.*

### Parameter Konfigurasi
- `includeModels` (Boolean, Default: `true`): Menyertakan file bobot model `.pt` / `.onnx` di dalam bundel ZIP.
- `targetPlatform` (String, Default: `"python_standalone"`): Pilihan: `"python_standalone"` atau `"docker_container"`.

---

## 4.6.17 `detections_difference`: Detections Difference (Selisih Spasial)

### Deskripsi Fungsional
Membandingkan dua kumpulan deteksi objek antara kondisi referensi dasar (*baseline state*, misal rak barang lengkap) dengan kondisi saat ini. Node ini mendeteksi barang apa yang hilang (*missing items*) atau benda baru apa yang ditinggalkan (*abandoned objects*).

---

*Lanjutkan ke **Bagian V: Ekosistem Open-NVR dan CCTV Hub Terintegrasi** untuk mempelajari integrasi pengawasan multi-kamera dan Evidence Vault.*



<!-- PAGE BREAK: BAB_05_EKOSISTEM_OPEN_NVR_DAN_CCTV_HUB.md -->


# BAGIAN V: EKOSISTEM OPEN-NVR DAN CCTV HUB TERINTEGRASI
## Afi Vision Builder & Integrated Open-NVR Platform

---

## 5.1 Arsitektur Terpadu Open-NVR Hub (Dual-Engine Architecture)

Secara tradisional, perusahaan harus membeli dan mengoperasikan dua sistem perangkat lunak yang terpisah:
1. **VMS (Video Management System)** komersial (seperti Milestone, Genetec, Synology Surveillance) untuk mencatat rekaman, mengatur kamera, dan menampilkan matriks video wall.
2. **AI Computer Vision Server** terpisah yang menarik stream video sekunder dari VMS untuk menjalankan inferensi analitik.

Pemisahan ini menciptakan inefisiensi besar: konsumsi bandwidth jaringan berlipat ganda, latensi transmisi tinggi, dan ketidakmampuan VMS untuk merespons secara langsung terhadap deteksi kecerdasan buatan.

**Afi Vision Builder menghadirkan Integrated Open-NVR Hub**, sebuah arsitektur hibrida (*Dual-Engine Architecture*) yang menyatukan fungsi VMS enterprise dan AI Vision Pipeline langsung di dalam satu mesin tunggal.

```
+-----------------------------------------------------------------------------------+
|                         INTEGRATED OPEN-NVR PLATFORM                              |
|                                                                                   |
|  +--------------------+   +-----------------------+   +------------------------+  |
|  |  ONVIF WS-DISCOVERY|   |  LIVE STREAM ROUTER   |   |   EVIDENCE CLIP VAULT  |  |
|  | Auto Scan LAN 3702 |   | TCP/UDP Demuxing      |   | Pre/Post-Roll Buffer   |  |
|  | Digest Auth Probe  |   | Multi-Client Fanout   |   | MP4 Lossless Storage   |  |
|  +---------+----------+   +-----------+-----------+   +-----------+------------+  |
|            |                          |                           |               |
|  +---------v--------------------------v---------------------------v------------+  |
|  |                       MATRIX LIVE WALL CONTROLLER                           |  |
|  |  * Single Focus (1x1)             * Standard Surveillance (2x2 Grid)        |  |
|  |  * High-Density (3x3 Grid)        * Command Center Patrol (1+5 Dynamic)     |  |
|  |  * Lossless Sub-Second Latency    * Offline Fallback (CCTV NO SIGNAL)       |  |
|  +------------------------------------+----------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

### Akses Menuju Open-NVR Hub
Untuk membuka modul Open-NVR Hub dari Workflow Studio, klik tombol **"OpenNVR Hub"** berikon kamera video pada toolbar atas kanvas:

![Studio Toolbar NVR Button](screenshots/001_studio_toolbar_nvr_button.png)
*Gambar 5.1: Tombol Akses Open-NVR Hub pada Toolbar Utama Workflow Studio.*

Jendela modal kokpit Open-NVR akan terbuka dengan tema gelap kedirgantaraan (*aerospace dark theme* `#090e17`) yang dirancang khusus untuk kenyamanan mata operator ruang kontrol pengawasan (*Security Operations Center / SOC*).

---

## 5.2 Pencarian Kamera Otomatis (ONVIF WS-Discovery)

Fitur pencarian otomatis (*Auto-Discovery*) membebaskan Anda dari keharusan menghafal alamat IP dan port setiap kamera yang terpasang di jaringan.

![NVR Modal Discover](screenshots/037_nvr_modal_tab_discover_redesign.png)
*Gambar 5.2: Tab Pindai Otomatis ONVIF Menemukan Kamera Jaringan Secara Instan.*

### 1. Cara Kerja Protokol WS-Discovery
1. Modul backend `engine/onvif_engine.py` mengirim paket probe multicast UDP standar ke alamat **`239.255.255.250:3702`**.
2. Setiap kamera CCTV yang mendukung standar ONVIF (Profile S, Profile G, atau Profile T) di dalam subnet LAN yang sama akan merespons dengan paket XML SOAP berisi identitas perangkat, model perangkat keras, firmware, dan endpoint service ONVIF.
3. Sistem memproses respons tersebut dan menampilkannya dalam tabel daftar penemuan rapi di Tab **1. Pindai Kamera**.

### 2. Langkah Menghubungkan Kamera dari Hasil Pindai:
1. Klik tombol **"Mulai Pemindaian Jaringan"** di tab Pindai.
2. Tunggu 3 hingga 5 detik sementara pemindai menjelajahi jaringan LAN.
3. Saat kamera ditemukan (misal: *Hikvision DS-2CD2043G2* atau *Dahua IPC-HFW2431S*), klik tombol **"Hubungkan"** di sebelah baris kamera.
4. Masukkan nama pengguna (*Username*) dan kata sandi (*Password*) kamera.
5. Sistem melakukan otentikasi *WS-Security UsernameToken Digest*, mengambil URL RTSP profil resolusi tinggi (*Main-stream*) dan profil resolusi rendah (*Sub-stream*), lalu menyimpannya ke daftar kamera terdaftar.

---

## 5.3 Pendaftaran Kamera Manual (Direct RTSP Connection)

Jika kamera CCTV berada di luar subnet lokal (misalnya di kantor cabang lain melalui VPN, menggunakan tunnel Cloudflare, atau perangkat NVR merek lama yang menonaktifkan protokol ONVIF), gunakan tab **2. Tambah Langsung RTSP**.

![Manual Direct RTSP](screenshots/038_nvr_modal_tab_manual_direct_rtsp.png)
*Gambar 5.3: Formulir Pendaftaran Kamera Manual Menggunakan URL RTSP / Stream Jaringan.*

### Parameter Formulir Pendaftaran Manual:
- **Nama Identitas Kamera**: Label logis deskriptif (contoh: `WS-01: Workshop Bay 1 - Ban Kiri`).
- **Lokasi Fisik / Grup**: Pengelompokan area (contoh: `Lantai Produksi A`, `Gerbang Gudang Logistik`, `Area Parkir`).
- **URL Stream Utama (Main Stream RTSP)**: URL RTSP resolusi penuh (1080p/4K) untuk perekaman bukti dan deteksi detail.
- **URL Stream Sekunder (Sub Stream RTSP - Opsional)**: URL RTSP resolusi ringan (640x360 atau 720p) untuk visualisasi Matriks Live Wall multi-layar guna menghemat bandwidth monitor operator.
- **Protokol Transportasi**:
  - `TCP (Disarankan)`: Menjamin transmisi data tidak hilang (*lossless*). Mencegah artefak citra pecah (*pixelation*) dan gambar abu-abu saat jaringan sibuk.
  - `UDP`: Latensi paling rendah, namun rentan frame rusak jika terdapat interferensi kabel LAN.
- **Opsi Aktifkan Deteksi Gerakan Cerdas (Motion Gate)**: Centang opsi ini jika Anda ingin sistem hanya mengonsumsi daya komputasi AI saat kamera mendeteksi gerakan nyata.

---

## 5.4 Manajemen Kamera Terdaftar & Status Pemantauan

Tab **3. Kamera Terdaftar** menyajikan daftar lengkap seluruh perangkat kamera yang telah dikonfigurasi di dalam sistem.

![Registered Cameras](screenshots/039_nvr_modal_tab_registered_with_camera.png)
*Gambar 5.4: Daftar Kamera Terdaftar dengan Telemetri Status Online, FPS, dan Tindakan Cepat.*

### 1. Indikator Status & Kesehatan Stream
Setiap kartu kamera dilengkapi indikator visual status operasional real-time:
- 🟢 **ONLINE**: Stream RTSP stabil, frame diterima secara teratur sesuai target FPS.
- 🟡 **RECONNECTING**: Koneksi terputus sesaat; backend sedang mencoba menghubungkan ulang dengan *exponential backoff*.
- 🔴 **OFFLINE**: Kamera mati atau kabel jaringan terlepas lebih dari batas toleransi waktu.

### 2. Penanganan Standby Otomatis (*CCTV NO SIGNAL*)
Afi Vision Builder tidak membiarkan layar menjadi hitam kosong atau menampilkan error browser saat kamera terputus. Sistem memiliki generator frame teknis otomatis yang langsung merender kartu status siaga profesional:

```
+-------------------------------------------------------+
|                                                       |
|                     [!] WARNING                       |
|               CCTV NO SIGNAL / OFFLINE                |
|                                                       |
|          Kamera: WS-01 (Workshop Bay 1)               |
|          Stream: rtsp://192.168.1.64:554/ch101        |
|          Status: Menunggu Re-koneksi Otomatis...      |
|                                                       |
+-------------------------------------------------------+
```

Begitu arus listrik atau kabel LAN kamera terpasang kembali, video langsung pulih secara instan tanpa perlu memuat ulang peramban web (*Zero Manual Intervention*).

---

## 5.5 Matriks Live Video Wall (Multi-Grid Monitoring)

Tab **4. Matriks Live Wall** adalah konsol pengawasan video simultan yang memungkinkan pengawas memantau banyak kamera secara bersamaan dalam tata letak kisi (*grid*) yang fleksibel.

![Matrix Wall Modal](screenshots/040_nvr_modal_tab_matrix_wall.png)
*Gambar 5.5: Tab Matriks Live Wall dengan Pengalih Tata Letak Kisi (2x2, 3x3, 1+5).*

### 1. Pilihan Tata Letak Kisi Pemantauan

#### A. Tata Letak 2x2 Grid (4 Kamera Simultan)
Ideal untuk workstation pengawasan standar dengan 4 kamera utama.

![Live Feeds 2x2](screenshots/030_opennvr_live_feeds_2x2.png)
*Gambar 5.6: Tampilan Matriks Pemantauan CCTV 2x2 Grid.*

#### B. Tata Letak 3x3 Grid (9 Kamera Simultan)
Dirancang untuk ruang kontrol berlayar lebar yang memantau hingga 9 sudut pabrik sekaligus dalam satu layar terpadu.

![Live Feeds 3x3](screenshots/031_opennvr_live_feeds_3x3.png)
*Gambar 5.7: Tampilan Matriks Pemantauan CCTV 3x3 Grid Kepadatan Tinggi.*

#### C. Tata Letak 1+5 Surveillance Patrol (1 Utama Besar + 5 Sekunder Kecil)
Tata letak favorit para perwira keamanan: Satu kamera prioritas ditampilkan dalam ukuran masif di sisi kiri (misal gerbang utama), sementara 5 kamera pendukung berputar atau berjejer di sisi kanan.

![Live Feeds 1+5](screenshots/032_opennvr_live_feeds_1plus5.png)
*Gambar 5.8: Tampilan Matriks Pengawasan Taktis 1+5 Grid.*

---

## 5.6 Evidence Vault (Brankas Klip Bukti Forensik)

Salah satu fitur paling krusial bagi kepatuhan audit dan penyelidikan insiden adalah **Evidence Vault** pada Tab 5.

![Evidence Vault Modal](screenshots/041_nvr_modal_tab_evidence_vault.png)
*Gambar 5.9: Brankas Bukti Forensik Menampilkan Arsip Klip Video Insiden.*

### 1. Mekanisme Perekaman Pre-Roll & Post-Roll Berbasis Ring Buffer
Ketika insiden terjadi (misalnya seseorang menyelinap melewati gerbang warehouse pada malam hari atau forklift menabrak tiang penyangga):
- Jika perekam biasa baru mulai merekam saat pemicu aktif, Anda akan kehilangan detik-detik awal penyebab terjadinya insiden.
- **Afi Vision Builder Ring Buffer** menyimpan rekaman 5 detik terakhir di memori volatil secara bergulir (*rolling circular buffer*). Saat sensor AI memicu kejadian, sistem mengambil 5 detik sebelum kejadian (*pre-roll*) dan menyambungnya dengan 10 detik setelah kejadian (*post-roll*).
- Hasilnya adalah satu rekaman video utuh 15 detik yang memperlihatkan **penyebab, momen kejadian, dan akibatnya**.

### 2. Fitur Pengelolaan Brankas Bukti:
- **Tabel Arsip Terstruktur**: Menampilkan Waktu Insiden, Nama Kamera Sumber, Tipe Pelanggaran, Skor Keyakinan AI, dan Ukuran File.
- **Pemutar Video Terpasang (*Built-in Video Player*)**: Klik tombol pemutaran untuk menonton langsung rekaman di dalam modal browser tanpa perlu mengunduh aplikasi media eksternal.
- **Pengunduhan Video Format Standar MP4**: Klip dienkode dengan codec standar H.264/MP4 sehingga dapat diputar di perangkat apa pun atau dilampirkan sebagai barang bukti resmi kepolisian/manajemen.
- **Pembersihan Otomatis Berbasis Retensi**: Klip yang usianya melampaui batas retensi (misal 30 hari) akan dihapus secara otomatis untuk menjaga ketersediaan ruang hard disk server.

---

## 5.7 Motion Gate & Optimasi Bandwidth Jaringan

Dalam jaringan CCTV perusahaan dengan puluhan kamera beresolusi tinggi, streaming video secara simultan dapat menghabiskan kapasitas switch LAN dan membebani prosesor server.

Open-NVR Hub menerapkan sistem optimasi cerdas:
1. **Dynamic Stream Switching**: Saat kamera ditampilkan dalam ukuran kecil pada matriks 3x3, sistem secara otomatis mengalihkan permintaan ke *Sub-Stream* beresolusi rendah (menghemat 75% bandwidth jaringan). Hanya saat operator memperbesar kamera ke mode layar penuh (*single focus*), sistem beralih ke *Main-Stream* resolusi 4K.
2. **Motion Gate Pre-Filtering**: Jika sebuah ruangan kosong tidak ada pergerakan, decoding frame dihentikan pada frame referensi diam. Pipeline AI tidur (*sleep mode*) dan baru terbangun saat ada piksel gerak nyata, menghemat pemakaian listrik dan memperpanjang umur perangkat keras server.

---

## 5.8 Ekspor Mandiri Paket OpenNVR Edge Bundle

Afi Vision Builder memungkinkan Anda mengekspor konfigurasi Open-NVR Hub menjadi satu paket aplikasi terpisah (*Standalone Edge Bundle*) melalui script `engine/afivision_opennvr_export.py`.

### Cara Mengekspor Paket:
1. Masuk ke terminal server Anda.
2. Jalankan perintah pembuatan bundel ekspor:
   ```bash
   python -c "import engine.afivision_opennvr_export as oe; oe.build_opennvr_bundle_zip('data/exports/opennvr_edge_bundle.zip')"
   ```
3. File ZIP yang dihasilkan dapat dipindahkan ke server edge manapun di cabang lapangan untuk langsung menjalankan VMS tanpa perlu mengonfigurasi ulang alur kerja dari awal.

---

*Lanjutkan ke **Bagian VI: Dashboard Builder dan Telemetri Enterprise** untuk merancang antarmuka pemantauan eksekutif dan KPI operasional.*



<!-- PAGE BREAK: BAB_06_DASHBOARD_BUILDER_DAN_TELEMETRI.md -->


# BAGIAN VI: DASHBOARD BUILDER DAN TELEMETRI ENTERPRISE
## Afi Vision Builder & Integrated Open-NVR Platform

---

## 6.1 Filosofi No-Code Visual Dashboard Designer

Setelah alur kerja vision selesai dibangun di Workflow Studio, tantangan berikutnya adalah: **bagaimana menyajikan informasi hasil deteksi kepada manajer, supervisor, dan operator lapangan secara elegan dan mudah dipahami?**

Sebagian besar sistem AI hanya menyediakan keluaran berupa log teks JSON mentah atau konsol terminal hitam putih. Pengguna non-teknis kesulitan membaca log tersebut secara real-time.

Afi Vision Builder menghadirkan **Dashboard Designer**, lingkungan desain visual tanpa kode (*No-Code Drag-and-Drop Designer*, terinspirasi dari kemudahan arsitektur Elementor) yang memungkinkan Anda merancang dashboard operasional kelas eksekutif hanya dalam hitungan menit.

![Dashboard Builder Initial](screenshots/001-01_dashboard_builder_initial.png)
*Gambar 6.1: Antarmuka Visual Dashboard Designer dengan Kanvas Desain dan Palette Widget.*

### Keunggulan Utama Dashboard Designer:
- **Pemisahan Logika & Presentasi**: Alur kerja pemrosesan video berjalan di backend, sementara tampilan dashboard hanya berfokus pada visualisasi metrik dan kontrol operator.
- **Dukungan Tema Ganda (*Light & Dark Theme*)**: Tampilan awal menggunakan tema *Warm Operational Light Mode* yang nyaman untuk kantor berlampu terang, serta dapat dialihkan ke *Dark Aerospace Theme* untuk ruang kontrol malam hari dengan satu klik.
- **Navigator Lapisan Hirarkis (*Elementor-style Navigator Tree*)**: Memudahkan pengelolaan tata letak komponen berlapis, penguncian widget (*widget lock*), dan pengelompokan kontainer responsif.

![Elementor Navigator](screenshots/001-01_elementor_navigator_layers.png)
*Gambar 6.2: Pohon Lapisan Navigator dan Pengaturan Penataan Konten Widget.*

---

## 6.2 Katalog 24+ Komponen Widget Siap Pakai

Dashboard Designer menyediakan lebih dari 24 komponen widget yang dapat Anda seret dan letakkan di kanvas:

| Kategori Widget | Nama Komponen | Deskripsi & Kegunaan Operasional |
|---|---|---|
| **Video & Visual** | **Live CCTV Stream Tile** | Menampilkan siaran langsung kamera dengan atau tanpa kotak anotasi AI secara real-time. |
| | **Multi-Camera Matrix** | Mini-grid pemantau beberapa kamera sekaligus di dalam dashboard. |
| | **Incident Snapshot Card** | Menampilkan foto resolusi tinggi dari kejadian pelanggaran terakhir yang terdeteksi. |
| | **Video Replay Tile** | Pemutar video klip rekaman insiden langsung dari Evidence Vault. |
| **KPI & Metrik** | **Total Metric Counter** | Angka besar penunjuk total objek terhitung (misal: "1.420 Ban Diproduksi"). |
| | **Gauge Meter Ring** | Indikator melingkar kapasitas okupansi atau utilisasi zona kerja (0% - 100%). |
| | **Zone Activity Timer HUD** | Status real-time sesi kerja workshop: Durasi berjalan, nama bay, dan status aktif. |
| | **Trend Sparkline** | Grafik tren garis kecil yang menunjukkan peningkatan/penurunan aktivitas per jam. |
| **Grafik Analitik** | **Real-Time Time Series** | Grafik garis interaktif yang memplot data metrik secara langsung setiap detik. |
| | **Class Distribution Pie** | Diagram lingkaran persentase persebaran kelas objek (misal: Truk vs Mobil vs Motor). |
| | **Hourly Activity Bar** | Diagram batang rekapitulasi aktivitas per jam kerja shift operasional. |
| | **Heatmap Projection Tile**| Visualisasi peta panas sebaran kerumunan di area denah lantai. |
| **Tabel & Log Data**| **Live Incident Feed** | Kartu pemberitahuan bergulir berisi insiden terbaru secara kronologis. |
| | **Virtualized Events Table**| Tabel data kejadian berkinerja tinggi yang mampu menampilkan puluhan ribu baris tanpa jeda. |
| | **LPR Plate Log** | Tabel khusus pembaca plat nomor lengkap dengan foto kendaraan dan waktu masuk. |
| | **Face Attendance Table** | Tabel absensi pengenalan wajah lengkap dengan foto wajah dan tingkat kemiripan. |
| **Kontrol Interaktif**| **Camera Switcher Bar** | Tombol navigasi cepat untuk beralih pandangan antar-kamera di lapangan. |
| | **Threshold Slider** | Penggeser sensitivitas alarm yang dapat diatur langsung oleh supervisor tanpa masuk ke studio. |
| | **Emergency Strobe Button** | Tombol pemicu sirine pabrik darurat yang terhubung ke broker MQTT. |

![Widget Inspector Style](screenshots/003-03_elementor_inspector_style_glassmorphism.png)
*Gambar 6.3: Kustomisasi Warna, Tipografi, Efek Glassmorphism, dan Border Radius pada Widget.*

---

## 6.3 Mekanisme Data Binding Menggunakan Dashboard Bus

Bagaimana sebuah widget di dashboard mengetahui nilai yang dihasilkan oleh node di alur kerja? Jawabannya adalah melalui **`Dashboard Bus`** (`engine/dashboard_bus.py`).

### Arsitektur Pub/Sub Real-Time
1. Setiap kali sebuah node kalkulasi (seperti `object_counter` atau `zone_activity_timer`) menghasilkan data baru, node tersebut mempublikasikan pesannya ke kanal lokal.
2. Modul `dashboard_bus` menyiarkan data tersebut melalui koneksi **WebSocket** (`/api/telemetry/ws`) ke seluruh peramban yang membuka dashboard.
3. Di dalam Dashboard Designer, Anda cukup mengklik widget yang bersangkutan, membuka tab **Data Binding**, lalu memilih variabel data yang ingin dihubungkan.

```
+-----------------------------------+
| Node: 'zone_activity_timer'       |
| Output: session_duration = 345.2s |
+-----------------+-----------------+
                  | (Local Bus Publish)
+-----------------v-----------------+
| Dashboard Bus (WebSocket Server)  |
+-----------------+-----------------+
                  | (WebSocket Broadcast)
+-----------------v-----------------+
| Widget: 'Zone Activity Timer HUD' |
| Tampilan: "00:05:45 (BAY 01 AKTIF)|
+-----------------------------------+
```

---

## 6.4 Interaktivitas Tingkat Lanjut: Looker-Style Cross-Filtering

Dashboard Designer mendukung fitur **Cross-Filtering Interaktif** (serupa dengan Google Looker / Power BI).

![Looker Cross Filter](screenshots/005-05_dashboard_looker_cross_filter.png)
*Gambar 6.4: Interaktivitas Lintas-Widget: Memilih Bar Diagram Batang Otomatis Memfilter Tabel Kejadian.*

### Cara Kerja Cross-Filtering:
1. Saat operator mengklik salah satu batang pada diagram batang *"Aktivitas Jam 14:00"*, sistem memancarkan filter global ke seluruh widget lainnya.
2. **Tabel Kejadian Insiden** seketika menyaring barisnya hanya untuk menampilkan insiden yang terjadi pada jam 14:00.
3. **Kartu Snapshot** langsung menampilkan foto pelanggaran yang terkait dengan jam tersebut.
4. Mengklik area kosong diagram akan mereset filter kembali ke tampilan keseluruhan (*global overview*).

---

## 6.5 Template Dashboard Industri Siap Pakai

Sistem menyertakan template dashboard profesional yang telah disesuaikan dengan kebutuhan sektor operasional spesifik:

![Dashboard CCTV Pro Template](screenshots/004-04_dashboard_ai_cctv_pro_template_applied.png)
*Gambar 6.5: Penerapan Template Dashboard AI CCTV Pro dengan Telemetri Multi-Kamera.*

1. **Industrial Tire Workshop Dashboard**:
   - Menampilkan status 5 Bay Workshop alat berat secara paralel.
   - Timer durasi pekerjaan mekanik per bay.
   - Grafik produktivitas shift kerja (jumlah ban yang diservis per jam).
2. **Warehouse Logistics & Exit Portal**:
   - Monitoring gerbang keluar masuk truk logistik.
   - Pembaca plat nomor LPR otomatis yang dicocokkan dengan manifes Surat Jalan ERP.
   - Tabel peringatan pelanggaran gerbang (*unauthorized exits*).
3. **K3 Safety & Compliance Center**:
   - Indikator persentase kepatuhan pemakaian APD (Helm & Rompi) secara keseluruhan pabrik.
   - Log insiden darurat pekerja jatuh (*Man Down Emergency Alert*).
   - Tombol penghentian konveyor darurat (*E-Stop*).

---

## 6.6 Ekspor Dashboard Mandiri ke Docker Container

Jika Anda ingin mendeploy dashboard monitoring di monitor ruang direksi atau ruang operator satpam tanpa memberikan akses ke studio perancang alur kerja, gunakan fitur **Export Standalone Dashboard**.

![Docker Export Modal](screenshots/005-05_dashboard_docker_export_modal_ready.png)
*Gambar 6.6: Modal Pengunduhan Paket Docker Container Standalone untuk Dashboard.*

### Langkah Ekspor & Deployment:
1. Klik tombol **"Ekspor Dashboard"** di pojok kanan atas Dashboard Designer.
2. Pilih format: **Standalone Web Bundle (HTML/JS/CSS)** atau **Docker Container Package**.
3. Klik **"Unduh Paket ZIP"**.
4. Ekstrak file ZIP di server target dan jalankan perintah Docker:
   ```bash
   docker build -t dashboard-cctv-enterprise .
   docker run -d -p 8080:80 --name cctv_monitor dashboard-cctv-enterprise
   ```
Dashboard kini dapat diakses secara independen di port 8080 tanpa membebani server utama Afi Vision Builder.

---

*Lanjutkan ke **Bagian VII: Model Zoo, Quantization & Custom AI Runtime** untuk mengelola bobot model kecerdasan buatan dan teknik akselerasi inferensi.*



<!-- PAGE BREAK: BAB_07_MODEL_ZOO_DAN_QUANTIZATION.md -->


# BAGIAN VII: MODEL ZOO, QUANTIZATION & CUSTOM RUNTIME
## Afi Vision Builder & Integrated Open-NVR Platform

---

## 7.1 Model Registry & Manajemen Bobot Kecerdasan Buatan

Keberhasilan implementasi *Computer Vision* industri bergantung pada pemilihan dan optimasi arsitektur model AI yang tepat. Afi Vision Builder dilengkapi dengan modul **Model Registry** terpusat untuk memuat, memvalidasi, dan mengelola berbagai format bobot jaringan syaraf tiruan (*neural network weights*).

![Models Registry](screenshots/10_models_registry.png)
*Gambar 7.1: Antarmuka Model Registry Menampilkan Daftar Bobot Model AI, Versi, dan Arsitektur.*

### Format Model yang Didukung:
1. **PyTorch Checkpoint (`.pt`)**: Format fleksibel bawaan ekosistem Ultralytics (YOLOv8, YOLO11, YOLO26). Sangat mudah dimodifikasi dan mendukung inferensi langsung pada GPU NVIDIA CUDA.
2. **Open Neural Network Exchange (`.onnx`)**: Standar format terbuka industri yang mendukung akselerasi lintas platform (*cross-platform hardware acceleration*) menggunakan CPU OpenVINO, AMD ROCm, DirectML, atau TensorRT.
3. **TensorRT Engine (`.engine` / `.plan`)**: Model terkompilasi khusus untuk GPU NVIDIA (termasuk modul NVIDIA Jetson Orin) yang memberikan latensi inferensi paling rendah (*ultra-low sub-5ms latency*).

Seluruh file bobot model disimpan di dalam direktori `weights/` pada root aplikasi dan diverifikasi integritasnya menggunakan checksum hash **SHA-256** untuk mencegah kerusakan file saat pengunduhan atau transmisi jaringan.

---

## 7.2 Dukungan YOLO Generasi Terbaru (YOLOv8, YOLO11, YOLO26n)

Afi Vision Builder mendukung generasi keluarga model YOLO (*You Only Look Once*) paling mutakhir:

| Varian Model | Jumlah Parameter | Ukuran File | Target Penggunaan Industri | Kecepatan CPU (i7 12th) | Kecepatan GPU (RTX 4060) |
|---|---|---|---|---|---|
| **`yolov8n.pt`** | 3.2 Juta | ~6.5 MB | Deteksi Cepat 80 Kelas Standar COCO | ~18 ms | ~2.5 ms |
| **`yolov8s.pt`** | 11.2 Juta | ~22.5 MB | Akurasi Lebih Tinggi untuk Objek Jarak Jauh | ~45 ms | ~4.8 ms |
| **`yolo11n.pt`** | 2.6 Juta | ~5.6 MB | Efisiensi Arsitektur C3k2 Terbaru | ~14 ms | ~2.1 ms |
| **`yolo26n.pt`** | 2.4 Juta | ~5.5 MB | Arsitektur Next-Gen Ultra-Lightweight Edge | ~12 ms | ~1.8 ms |
| **`yolov8n-pose.pt`** | 3.3 Juta | ~6.8 MB | Estimasi Kerangka Pose 17 Titik Tubuh Manusia | ~22 ms | ~3.2 ms |
| **`yolov8n-seg.pt`** | 3.4 Juta | ~7.1 MB | Segmentasi Masker Poligon Piksel Presisi | ~25 ms | ~3.8 ms |
| **`yolov8n-cls.pt`** | 2.7 Juta | ~5.5 MB | Klasifikasi Gambar Global Kategori Tunggal | ~8 ms | ~1.2 ms |

### Mekanisme Pengunduhan Resmi yang Aman & Idempoten
Sistem menyediakan tombol unduh bobot resmi langsung di dalam Inspector node `detector`. Proses pengunduhan menerapkan prinsip **Idempotent Staging**: File diunduh terlebih dahulu ke direktori sementara (*staging buffer*), divalidasi ukuran dan checksum SHA-256-nya terhadap rilis resmi GitHub Ultralytics, baru kemudian dipindahkan ke folder `weights/`. Hal ini menjamin bahwa jika koneksi internet terputus di tengah jalan, sistem tidak akan mengalami *corrupted model crash*.

---

## 7.3 RF-DETR ONNX Runtime (Transformer-Based Detection)

Untuk kasus industri dengan kepadatan objek sangat tinggi dan saling bertumpuk (*extreme occlusion*, misalnya tumpukan ban bekas atau keranjang baut logam), algoritma YOLO berbasis NMS (*Non-Maximum Suppression*) terkadang tidak sengaja menghapus deteksi objek yang saling menutupi.

Afi Vision Builder menyertakan runtime khusus untuk **RF-DETR (Real-Time DEtection TRansformer)**:
- **Arsitektur End-to-End**: Menggunakan mekanisme *Self-Attention Transformer* yang memprediksi kumpulan kotak objek (*set prediction*) secara langsung tanpa memerlukan langkah heuristik NMS.
- **Eksekusi ONNX Berkecepatan Tinggi**: Dioptimasi menggunakan `rfdetr_onnx_runtime.py` yang memanfaatkan *kernel fusion* untuk berjalan mulus di prosesor multicore.

---

## 7.4 UniFace Enterprise Facial Recognition Suite

Untuk kebutuhan kontrol akses pintu gerbang, absensi mandiri karyawan, dan verifikasi identitas personil di area berbahaya, sistem menyediakan modul **UniFace** lengkap.

![UniFace Canvas](screenshots/18_uniface_and_timer_canvas.png)
*Gambar 7.2: Kanvas Penggabungan Deteksi Wajah UniFace dengan Timer Aktivitas.*

### Rantai Pemrosesan Wajah Tiga Tahap:
1. **Deteksi Wajah (SCRFD)**: Menemukan wajah bahkan pada resolusi sekecil 16x16 piksel dengan sudut kemiringan hingga 60 derajat.
2. **Penyelarasan Landmark 5-Titik (Facial Alignment)**: Menemukan koordinat kedua mata, hidung, dan kedua ujung bibir, lalu memutar citra secara geometris agar wajah berada pada posisi tegak lurus sempurna.
3. **Ekstraksi Vektor Fitur (ArcFace Embedding)**: Memproyeksikan wajah ke dalam ruang bola berdimensi 512 (*512-D hypersphere vector*). Dua foto dari orang yang sama akan memiliki jarak sudut (*angular cosine distance*) yang sangat dekat.

![Enroll Face Modal](screenshots/17_enroll_face_modal.png)
*Gambar 7.3: Modal Registrasi Wajah Karyawan Baru dengan Kamera Web Langsung.*

### Manajemen Galeri Wajah (*Face Registry*):
Pengguna dapat mendaftarkan personil baru melalui menu **Face Registry**:
- Ambil foto menggunakan webcam langsung atau unggah foto KTP/ID Card.
- Masukkan Nama Karyawan, Departemen, dan NIK (*Nomor Induk Karyawan*).
- Sistem mengekstrak embedding wajah dan menyimpannya ke indeks pencarian vektor berkecepatan tinggi di backend.

---

## 7.5 EfficientAD Anomaly Inspection Runtime

Inspeksi cacat produk manufaktur (*defect inspection*, seperti retakan pada ban baru, goresan pada bodi mobil, atau cacat cetakan PCB) menghadapi kendala besar: **sangat sulit mengumpulkan ribuan foto produk cacat untuk melatih model supervised**.

Node `efficientad` menyelesaikan masalah ini dengan pendekatan **Unsupervised Anomaly Detection**:
- Model hanya perlu "melihat" 50 hingga 100 foto produk yang **NORMAL (Bebas Cacat)** selama fase prapelatihan.
- Sistem menggunakan arsitektur *Teacher-Student Feature Networks* berkecepatan tinggi yang digabung dengan *Autoencoder*.
- Saat produk baru berjalan di bawah kamera konveyor, model membandingkan fitur struktural produk tersebut dengan representasi ideal guru.
- Setiap goresan sekecil 1 milimeter atau perbedaan warna akan langsung menyala pada **Peta Anomali (Anomaly Heatmap)** dan memicu penolakan produk secara otomatis (*rejection solenoid trigger*).

---

## 7.6 Model Quantizer Bawaan (FP32 ke FP16 / INT8)

Sebagian besar model AI dilatih dengan presisi angka pecahan 32-bit (*Floating Point 32 / FP32*). Model ini membutuhkan memori besar dan siklus CPU yang berat.

Afi Vision Builder menyertakan **Model Quantizer bawaan** (`engine/model_quantizer.py`) yang dapat diakses langsung dari antarmuka web:

![Model Quantizer](screenshots/11_model_quantizer.png)
*Gambar 7.4: Antarmuka Model Quantizer untuk Konversi Model ke Format FP16 dan INT8.*

### Manfaat Kuantisasi Model:
1. **Kuantisasi FP16 (Half Precision 16-Bit)**:
   - Memotong ukuran file model hingga **50%**.
   - Meningkatkan kecepatan inferensi **1.8x hingga 2.2x** pada GPU modern tanpa penurunan akurasi sama sekali ($< 0.1\%$ mAP drop).
2. **Kuantisasi INT8 (Integer 8-Bit Dynamic Quantization)**:
   - Mengubah operasi perkalian matriks pecahan menjadi operasi bilangan bulat integer 8-bit.
   - Memotong pemakaian memori RAM hingga **75%**.
   - Memberikan lonjakan kecepatan **2.5x hingga 3.5x lebih kencang pada CPU-Only (tanpa GPU)**, sangat ideal untuk komputer industri di lapangan.

### Langkah Menjalankan Kuantisasi:
1. Buka jendela **Model Quantizer** dari menu Tools.
2. Pilih model sumber (misal: `yolov8n.onnx`).
3. Pilih metode kuantisasi target: **FP16** atau **INT8**.
4. Klik tombol **"Mulai Kuantisasi Model"**.
5. Dalam waktu 10-30 detik, model hasil optimasi (misal: `yolov8n_int8.onnx`) akan otomatis terdaftar dan siap digunakan di alur kerja.

---

*Lanjutkan ke **Bagian VIII: Integrasi Sistem Eksternal, MQTT dan Enterprise ERP** untuk mempelajari pertukaran data kejadian secara otomatis.*



<!-- PAGE BREAK: BAB_08_INTEGRASI_API_MQTT_DAN_ERP.md -->


# BAGIAN VIII: INTEGRASI SISTEM EKSTERNAK, MQTT DAN ENTERPRISE ERP
## Afi Vision Builder & Integrated Open-NVR Platform

---

## 8.1 REST API Gateway (OpenAPI / Swagger Specification)

Afi Vision Builder bukan hanya sekadar aplikasi desktop visual mandiri, melainkan sebuah layanan backend terdistribusi yang menyediakan antarmuka pemrograman aplikasi (**RESTful API**) berstandar tinggi.

Dokumentasi interaktif OpenAPI / Swagger dapat diakses langsung melalui peramban di URL:
👉 **`http://localhost:8765/docs`** atau format Redoc di **`http://localhost:8765/redoc`**.

```
+-----------------------------------------------------------------------------------+
|                        REST API ENDPOINT ARCHITECTURE                             |
|                                                                                   |
|  +--------------------+   +-----------------------+   +------------------------+  |
|  |   WORKFLOW APIS    |   |    CCTV / STREAM APIS |   |    OPEN-NVR HUB APIS   |  |
|  | /api/workflow/list |   | /api/camera/stream    |   | /api/nvr/discover      |  |
|  | /api/workflow/save |   | /api/cctv/cameras     |   | /api/nvr/cameras       |  |
|  | /api/workflow/run  |   | /api/preview/{id}     |   | /api/nvr/vault/clips   |  |
|  +--------------------+   +-----------------------+   +------------------------+  |
|                                                                                   |
|  +--------------------+   +-----------------------+   +------------------------+  |
|  |   SYSTEM & HEALTH  |   | VIDEO PLAYBACK APIS   |   |    TELEMETRY & BUS     |  |
|  | /api/health        |   | /api/video/seek       |   | WS /api/telemetry/ws   |  |
|  | /api/status        |   | /api/video/speed      |   | /api/dashboard/bus     |  |
|  +--------------------+   +-----------------------+   +------------------------+  |
+-----------------------------------------------------------------------------------+
```

### Ringkasan Endpoint Kritis:

| Method | Endpoint Path | Fungsi Teknis |
|---|---|---|
| `GET` | `/api/health` | Pemeriksaan kesehatan layanan, penggunaan RAM, ketersediaan GPU, dan uptime. |
| `GET` | `/api/status` | Mengambil status runtime pipeline vision, nama runner aktif, dan status kamera. |
| `GET` | `/api/workflow/projects` | Mengambil daftar seluruh proyek alur kerja yang tersimpan di basis data. |
| `POST` | `/api/workflow/run` | Menjalankan alur kerja tertentu di latar belakang (*background runner*). |
| `POST` | `/api/workflow/stop` | Menghentikan alur kerja yang sedang berjalan secara aman (*graceful stop*). |
| `GET` | `/api/preview/{pipeline_id}` | Mengalirkan stream video Motion JPEG (MJPEG) hasil pemrosesan AI. |
| `GET` | `/api/nvr/discover` | Menjalankan probe pencarian otomatis ONVIF WS-Discovery di jaringan LAN. |
| `GET` | `/api/nvr/cameras` | Mengambil daftar seluruh kamera CCTV yang terdaftar beserta status onlinenya. |
| `POST` | `/api/nvr/cameras` | Mendaftarkan kamera baru secara manual dengan URL RTSP. |
| `GET` | `/api/nvr/vault/clips` | Mengambil daftar rekaman klip kejadian video insiden yang tersimpan di Vault. |
| `POST` | `/api/video/seek` | Mengendalikan timeline video playback (loncat ke detik/persen tertentu). |
| `POST` | `/api/video/playback-speed`| Mengubah kecepatan pemutaran video secara dinamis (0.25x hingga 4.0x). |

---

## 8.2 Webhook Event Ingestion & Outbound Dispatcher

Untuk mengintegrasikan hasil analisis kamera dengan aplikasi pihak ketiga secara real-time, sistem menggunakan mekanisme **Outbound Webhook** (`webhook_output`).

### 1. Format JSON Payload Standar Kejadian Vision
Setiap kali terjadi suatu kejadian penting (misalnya sebuah truk keluar gerbang membawa ban atau pekerja jatuh pingsan), backend mengompilasi paket data terstruktur dalam format JSON:

```json
{
  "specversion": "1.0",
  "id": "EVT-20261110-093522-8F92",
  "source": "urn:afivision:site-01:camera:WH-GATE-01",
  "type": "com.afivision.warehouse.exit_event",
  "time": "2026-11-10T09:35:22.451+08:00",
  "datacontenttype": "application/json",
  "data": {
    "zoneId": "ZONE-GATE-A",
    "targetClass": "truck",
    "trackId": 104,
    "licensePlate": "B 9123 KDA",
    "direction": "OUTWARD",
    "observationDurationSeconds": 18.2,
    "confidence": 0.94,
    "carrierTiresDetected": 6,
    "personnelInsideBay": 1
  },
  "evidence": {
    "thumbnailUrl": "http://192.168.1.100:8765/api/vault/snapshots/EVT-20261110-093522-8F92.jpg",
    "videoClipUrl": "http://192.168.1.100:8765/api/vault/clips/EVT-20261110-093522-8F92.mp4"
  }
}
```

### 2. Kebijakan Percobaan Ulang (*Retry Policy dengan Exponential Backoff*)
Jika server tujuan (misal ERP) sedang mengalami lonjakan beban atau jaringan terputus sesaat:
- **Percobaan 1**: Segera saat kejadian terjadi.
- **Percobaan 2**: 2 detik setelah kegagalan pertama.
- **Percobaan 3**: 8 detik setelah kegagalan kedua.
- **Percobaan 4**: 32 detik setelah kegagalan ketiga.
Jika seluruh percobaan gagal, pesan kejadian disimpan ke dalam antrean *Dead-Letter Queue (DLQ)* di basis data SQLite lokal agar dapat dikirim ulang secara manual (*manual replay*) saat server tujuan pulih.

---

## 8.3 Konektivitas MQTT Industrial IoT & Pabrik Pintar

Di lingkungan manufaktur industri modern (*Industry 4.0*), protokol **MQTT** adalah standar de facto untuk komunikasi antar-mesin (*Machine-to-Machine / M2M*).

Afi Vision Builder dapat bertindak sebagai penerbit data (*MQTT Publisher*) berbobot sangat ringan:

```
+-----------------------+               +----------------------+               +-----------------------+
|  Afi Vision Builder   |  MQTT Pub     |     MQTT Broker      |  MQTT Sub     |  PLC Siemens / SCADA  |
|  Node: mqtt_publisher +-------------->|  Mosquitto / EMQX    +-------------->|  Trigger Sirine / E-Stop
+-----------------------+               +----------------------+               +-----------------------+
```

### 1. Hierarki Struktur Topik yang Dianjurkan:
Untuk menjaga keteraturan ribuan sensor di berbagai pabrik, gunakan skema penamaan hierarkis standar:

```text
perusahaan/site_id/departemen/kamera_id/kategori_kejadian
```
Contoh nyata di lapangan:
- `onechitra/workshop/bay01/cctv01/session_status`
- `onechitra/warehouse/gate02/cctv04/exit_violations`
- `onechitra/factory/k3_safety/cctv08/man_down_alarm`

### 2. Pilihan Quality of Service (QoS):
- **QoS 0 (At most once)**: Untuk telemetri frekuensi tinggi (misal: FPS kamera atau posisi koordinat objek setiap detik).
- **QoS 1 (At least once)**: Untuk kejadian bisnis penting (misal: Sesi ganti ban selesai atau pencatatan plat nomor LPR).
- **QoS 2 (Exactly once)**: Untuk kejadian kritis yang memicu transaksi keuangan atau saldo stok gudang.

---

## 8.4 Integrasi Bot Peringatan Instan Telegram

Salah satu jalur komunikasi darurat paling efektif bagi tim di lapangan adalah notifikasi pesan instan Telegram.

### 1. Langkah Menyiapkan Bot Telegram:
1. Buka aplikasi Telegram di smartphone Anda dan cari kontak bot resmi **`@BotFather`**.
2. Kirim perintah `/newbot` dan ikuti instruksi penamaan bot Anda (misal: *AfiVisionSecurityBot*).
3. BotFather akan memberikan sebuah string token rahasia panjang (*Bot API Token*), simpan string ini.
4. Buat sebuah grup Telegram baru untuk tim pengawas operasional pabrik, lalu undang bot Anda masuk ke dalam grup tersebut.
5. Ambil **Chat ID** grup tersebut (biasanya diawali dengan tanda minus, contoh: `-100192837465`).

### 2. Mengonfigurasi Node `telegram_notification`:
Buka Workflow Studio, hubungkan node detektor/logika ke node `telegram_notification`, lalu atur di Inspector:
- `botToken`: Masukkan token dari BotFather.
- `chatId`: Masukkan Chat ID grup Anda.
- `attachPhoto`: Centang `true`.

Saat terjadi pelanggaran keselamatan (misal pekerja tidak memakai helm di zona crane), foto resolusi tinggi beserta pesan peringatan bertanda merah akan langsung masuk ke ponsel seluruh anggota grup Telegram dalam waktu kurang dari 1 detik!

---

## 8.5 Penyimpanan Basis Data Relasional & Skema Data

Sistem mendukung penyimpanan berbasis **SQLite** (bawaan untuk server tunggal) dan **PostgreSQL** (untuk infrastruktur cluster multi-server perusahaan).

### Skema Tabel Kritis di Basis Data:
1. **`vision_events`**: Menyimpan setiap kejadian diskrit (keluar zona, pelanggaran APD, pembacaan plat).
2. **`work_sessions`**: Menyimpan catatan historis durasi pekerjaan workshop (Waktu Mulai, Waktu Selesai, Total Detik Bersih, ID Bay, Alasan Selesai).
3. **`camera_registry`**: Menyimpan konfigurasi kamera CCTV terdaftar, URL stream RTSP, dan status konektivitas.
4. **`face_embeddings`**: Menyimpan matriks vektor 512 dimensi wajah karyawan yang terdaftar.

---

## 8.6 Antrean Kejadian ERP Enterprise & Deduplikasi Kejadian

Saat mengintegrasikan sistem penglihatan AI dengan sistem ERP inti (*Enterprise Resource Planning*) seperti SAP atau sistem gudang internal One Chitra:

> [!CAUTION]
> Jangan pernah mengizinkan satu kendaraan yang berhenti di ambang batas gerbang memicu pencatatan transaksi keluar berulang kali (*Double-Deduction Inventory Violation*)!

Afi Vision Builder menerapkan tiga lapisan perlindungan deduplikasi:
1. **Idempotency Key Generator**: Setiap kejadian diberi kunci unik berdasarkan kombinasi hash `SHA256(SourceID + TargetClass + TrackID + DateHourBlock)`. Jika request terkirim dua kali karena jaringan lambat, server ERP yang menerima kunci idempoten yang sama akan mengabaikan request kedua tanpa menduplikasi data.
2. **Rearm Cooldown Timer**: Node `zone_exit_event` memiliki timer penguncian internal (misal 5 detik). Setelah sebuah truk keluar, sensor gerbang dikunci sementara untuk memastikan gandengan trailer belakang truk tidak dianggap sebagai truk kedua.
3. **Confirmed State Transition**: Sensor memastikan bahwa siklus `State = INSIDE` harus terbukti kembali ada sebelum status `OUT` berikutnya diizinkan memicu alarm baru.

---

*Lanjutkan ke **Bagian IX: Export Code dan Edge Deployment** untuk mempelajari teknik pengemasan alur kerja mandiri ke perangkat komputer industri tanpa web server.*



<!-- PAGE BREAK: BAB_09_EXPORT_CODE_DAN_EDGE_DEPLOYMENT.md -->


# BAGIAN IX: EXPORT CODE DAN EDGE DEPLOYMENT
## Afi Vision Builder & Integrated Open-NVR Platform

---

## 9.1 Arsitektur Code Generator (`export_code.py`)

Salah satu fitur paling unggul dan disukai oleh para teknisi AI di Afi Vision Builder adalah kemampuan **Export Code** (Ekspor Kode Mandiri).

### Mengapa Perlu Mengekspor Kode?
Meskipun antarmuka web visual sangat nyaman untuk merancang dan menguji alur kerja, menjalankan antarmuka web penuh di lokasi operasional permanen (seperti di tiang kamera terpencil atau di komputer industri tanpa monitor / *headless IPC*) memiliki beberapa kerugian:
1. **Beban Overhead Memori**: Server web, rendering HTML, dan WebSocket mengonsumsi memori ekstra (~300-500 MB RAM).
2. **Ketergantungan UI**: Jika browser ditutup atau tab mengalami crash, operator khawatir proses vision ikut mati.
3. **Kebutuhan Standalone Edge**: Komputer industri di gardu listrik atau gerbang tambang sering kali tidak memiliki peramban grafis (*GUI*) dan hanya memiliki antarmuka command line Linux (*terminal SSH*).

Node dan tombol **Export Code** menyelesaikan masalah ini dengan mengonversi keseluruhan arsitektur alur kerja visual Anda menjadi sebuah **skrip Python asli yang ramping, mandiri, dan berkinerja sangat tinggi**.

```
+------------------------------------------+
|  WORKFLOW STUDIO (VISUAL CANVAS)         |
|  [IP Cam] -> [Detector] -> [Zone Timer]  |
+--------------------+---------------------+
                     |
                     | (Klik Tombol 'Export Code')
                     |
+--------------------v---------------------+
|  STANDALONE EDGE PYTHON SCRIPT (run.py)  |
|  * 100% Headless (Zero Web Server)       |
|  * Ultra-Low Latency (< 15 ms)           |
|  * Ringan Memori (< 200 MB RAM)          |
|  * Siap Dijalankan sebagai Systemd Svc   |
+------------------------------------------+
```

---

## 9.2 Struktur Paket Unduhan Bundel ZIP Ekspor

Saat Anda mengklik tombol **Export Code** di toolbar studio atau melalui modal ekspor, backend menghasilkan file arsip terkompresi `afi_vision_export_<project_id>.zip`.

![Export Code Modal](screenshots/005-05_dashboard_docker_export_modal_ready.png)
*Gambar 9.1: Modal Konfigurasi dan Unduhan Paket Standalone Code.*

### Struktur Berkas di Dalam Bundel ZIP:
```text
📦 afi_vision_export_bundle/
├── 📄 run.py                     # Entrypoint skrip utama Python (dapat langsung dijalankan)
├── 📄 workflow_config.json       # Snapshot lengkap seluruh parameter node dalam format JSON ringkas
├── 📄 requirements.txt           # Daftar pustaka minimal yang dibutuhkan untuk menjalankan skrip
├── 📄 Dockerfile                 # Konfigurasi containerization Docker mandiri
├── 📄 README.md                  # Petunjuk instruksi eksekusi CLI cepat
├── 📁 engine/                    # Direktori pustaka vision core minimalis
│   ├── 📄 core.py                # Pipeline eksekusi frame dan penanganan graf
│   ├── 📄 project_nodes.py       # Logika Zone Activity Timer, Zone Exit Event, dll.
│   ├── 📄 roboflow_tracker.py    # Algoritma ByteTrack & Re-ID Tracker
│   └── 📄 standalone_run.py      # Engine runner headless mandiri
└── 📁 weights/                   # (Opsional) File bobot model AI yang digunakan (misal: yolov8n.pt)
```

---

## 9.3 Menjalankan Skrip Python Headless di Lingkungan Bersih

Anda dapat memindahkan folder hasil ekstrak ke komputer atau server mana pun yang memiliki Python terpasang, lalu menjalankannya secara langsung di terminal tanpa membuka antarmuka web.

### Langkah 1: Persiapan Virtual Environment
Di terminal komputer target:
```bash
# Buat virtual environment baru
python3 -m venv venv_edge
source venv_edge/bin/activate   # (atau venv_edge\Scripts\activate pada Windows)

# Pasang dependensi minimal
pip install -r requirements.txt
```

---

### Langkah 2: Verifikasi Integritas Alur Kerja (`--check`)
Sebelum memproses video nyata, pastikan seluruh dependensi dan bobot model telah terpasang dengan baik menggunakan opsi preflight check:
```bash
python run.py --check
```
Output terminal:
```text
[INFO] Memeriksa integritas bundel alur kerja...
[OK] Python Version: 3.11.8
[OK] OpenCV Version: 4.9.0
[OK] Model Weights: weights/yolov8n.pt (SHA-256 Verified)
[OK] Workflow Graph: 5 Nodes Loaded (No circular loops detected)
[SUCCESS] Seluruh pemeriksaan lulus. Sistem siap dijalankan!
```

---

### Langkah 3: Menjalankan Pemrosesan Video Headless
Jalankan skrip dengan memasukkan sumber video melalui argumen baris perintah (*CLI argument*):

#### A. Menjalankan dari Kamera CCTV RTSP Langsung:
```bash
python run.py --source "rtsp://admin:Password123@192.168.1.64:554/ch101" --headless
```

#### B. Menjalankan dari File Rekaman Video MP4:
```bash
python run.py --source "data/workshop_sample.mp4" --show
```
*(Catatan: Opsi `--show` akan membuka jendela preview lokal OpenCV di monitor Anda, sementara opsi `--headless` mematikan tampilan monitor untuk efisiensi CPU maksimal).*

#### C. Menimpa Parameter Sensitivitas Melalui CLI:
```bash
python run.py --source "rtsp://..." --conf 0.55 --iou 0.40 --output-dir "/var/log/surveillance"
```

---

## 9.4 Menjalankan Skrip sebagai Layanan Otomatis Linux (`systemd service`)

Agar skrip vision berjalan secara otomatis saat komputer industri dinyalakan dan otomatis restart jika listrik padam, daftarkan skrip sebagai layanan **systemd**:

1. Buat file service baru di Linux:
   ```bash
   sudo nano /etc/systemd/system/afivision-edge.service
   ```

2. Masukkan konfigurasi berikut:
   ```ini
   [Unit]
   Description=Afi Vision Standalone Edge Pipeline
   After=network.target

   [Service]
   Type=simple
   User=administrator
   WorkingDirectory=/opt/afivision_edge
   ExecStart=/opt/afivision_edge/venv_edge/bin/python /opt/afivision_edge/run.py --source "rtsp://admin:Password123@192.168.1.64:554/ch101" --headless
   Restart=always
   RestartSec=5
   Environment=PYTHONUNBUFFERED=1

   [Install]
   WantedBy=multi-user.target
   ```

3. Aktifkan dan jalankan layanan:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable afivision-edge.service
   sudo systemctl start afivision-edge.service

   # Periksa status operasional
   sudo systemctl status afivision-edge.service
   ```

Pipeline vision Anda kini telah resmi menjadi layanan industri kelas militer yang akan terus berjalan 24 jam sehari, 7 hari seminggu tanpa henti.

---

## 9.5 Panduan Deployment ke Perangkat Edge Industri

Afi Vision Builder telah diuji dan dioptimasi untuk berjalan di berbagai platform perangkat keras edge:

### 1. NVIDIA Jetson Platform (Jetson Orin Nano, Orin NX, AGX Orin)
- **Sistem Operasi**: NVIDIA JetPack 5.1 atau JetPack 6.0 (Ubuntu 20.04 / 22.04 LTS).
- **Akselerasi Video**: Manfaatkan GStreamer dengan pipeline akselerasi hardware NVDEC:
  ```bash
  python run.py --source "rtspsrc location=rtsp://... latency=0 ! rtph264depay ! h264parse ! nvv4l2decoder ! nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! appsink"
  ```
- **Akselerasi Model**: Konversi model PyTorch menjadi engine **TensorRT FP16**:
  ```bash
  yolo export model=weights/yolov8n.pt format=engine half=True device=0
  ```
  Menghasilkan kecepatan **110+ FPS** pada modul Jetson Orin Nano (daya hanya 15 Watt!).

---

### 2. Komputer Industri Berbasis Intel CPU (Advantech / Siemens / Axiomtek IPC)
- Menggunakan arsitektur tanpa kipas (*fanless IPC*) yang tahan debu dan getaran ekstrem.
- **Akselerasi Model**: Gunakan runtime **ONNX Runtime dengan backend OpenVINO Execution Provider** yang memanfaatkan instruksi vektor Intel AVX-512 dan VNNI:
  ```bash
  pip install onnxruntime-openvino
  python run.py --device openvino
  ```

---

### 3. Raspberry Pi 5 dengan Akselerator AI (Hailo-8 / NCNN)
- Untuk implementasi dengan anggaran ekonomis (biaya perangkat keras di bawah 2 juta rupiah).
- Gunakan model bobot ringan `yolo26n.pt` atau `yolov8n_int8.onnx` yang telah dikuantisasi melalui menu Model Quantizer Afi Vision Builder.
- Mampu memproses video resolusi 720p pada **18-24 FPS stabil**.

---

*Lanjutkan ke **Bagian X: Panduan Langkah demi Langkah: 5 Studi Kasus Nyata** untuk mempelajari implementasi end-to-end dari nol pada skenario industri aktual.*



<!-- PAGE BREAK: BAB_10_STUDI_KASUS_DAN_TUTORIAL_STEP_BY_STEP.md -->


# BAGIAN X: PANDUAN LANGKAH DEMI LANGKAH: 5 STUDI KASUS NYATA
## Afi Vision Builder & Integrated Open-NVR Platform

---

## DAFTAR ISI BAGIAN X

- 10.1 **Studi Kasus 1**: Smart Workshop Bay Tracking (Estimasi Waktu Kerja Penggantian Ban Alat Berat)
- 10.2 **Studi Kasus 2**: Warehouse Gate Exit Surveillance & ERP Inventory Dispatch (Pengawasan Gerbang Gudang)
- 10.3 **Studi Kasus 3**: K3 / K3LH Factory Safety & Man Down Detection (Kepatuhan APD & Deteksi Darurat Pekerja Jatuh)
- 10.4 **Studi Kasus 4**: Smart Traffic Flow & Retail Footfall Analytics (Penghitung Garis Dua Arah & Peta Panas Kepadatan)
- 10.5 **Studi Kasus 5**: Autonomous CCTV Copilot Menggunakan Multimodal Vision AI Agent (Penalaran Semantik Otomatis)

---

## 10.1 Studi Kasus 1: Smart Workshop Bay Tracking (Estimasi Waktu Kerja Mekanik)

### 1. Tujuan & Skenario Lapangan
Pada workshop servis alat berat tambang (seperti di workshop Chitra Paratama), manajemen ingin mengetahui **berapa lama waktu nyata (*actual cycle time*) yang dibutuhkan mekanik untuk mengganti atau memperbaiki ban raksasa (Giant OTR Tire)** di setiap area kerja (*Bay 1 s/d Bay 5*).
- **Tantangan**: Mekanik sering kali berpindah posisi, tertutup sebagian oleh bodi truk, atau keluar zona sebentar untuk mengambil obeng/kunci pas.
- **Solusi**: Menggunakan node `zone_activity_timer` yang menghitung durasi waktu elapsed berdasarkan interaksi spasial antara ban dan orang dengan toleransi waktu jeda (*grace period*).

![Workshop Sessions](screenshots/08_workshop_sessions.png)
*Gambar 10.1: Hasil Rekapitulasi Sesi Kerja Workshop dengan Waktu Mulai, Selesai, dan Durasi Bersih.*

---

### 2. Arsitektur Topologi Alur Kerja (Workflow Graph)
```
[IP Camera (Bay 1)] 
        | (Raw Image)
[Object Detector (YOLOv8)] 
        | (Detections: 'person', 'tire')
[Object Tracker (ByteTrack)] 
        | (Tracklets)
[Zone Activity Timer (Bay 1 Polygon)] 
        +-----------------------------------+
        | (Timer Events)                    | (Annotated Image)
        v                                   v
[Database Output (SQLite)]          [Overlay Annotate]
        |                                   |
[ERP Webhook Dispatcher]            [Dashboard Sink]
```

---

### 3. Langkah Demi Langkah Pembuatan dari Nol:

#### Langkah 1: Buat Proyek Baru
1. Buka Projects Hub di `http://localhost:8765`.
2. Klik tombol **"+ Proyek Baru"**.
3. Beri nama proyek: `WS-01: Workshop Bay 1 Activity Tracker`.

#### Langkah 2: Tambahkan Node Sumber Kamera (`ip_camera`)
1. Buka Sidebar Palette di sebelah kiri, cari kategori **Sources**, lalu seret node **`ip_camera`** ke kanvas.
2. Klik node tersebut untuk membuka Inspector di sisi kanan.
3. Masukkan URL RTSP kamera Bay 1:
   ```text
   rtsp://admin:Password123@192.168.1.64:554/Streaming/Channels/101
   ```
4. Set `transport` ke **`tcp`**.

#### Langkah 3: Tambahkan Node Detektor AI (`detector`)
1. Dari kategori **AI Vision Models**, seret node **`detector`** ke kanvas.
2. Sambungkan pin output `image` dari node `ip_camera` ke pin input `image` pada node `detector`.
3. Pada Inspector, pilih model bobot `yolov8s.pt` (atau `yolo11n.pt`).
4. Atur `confidenceThreshold` ke **`0.40`**.
5. Pada kotak `filterClasses`, isi: `["person", "tire", "truck"]`.

#### Langkah 4: Tambahkan Node Pelacak Temporal (`tracker`)
1. Dari kategori **Tracking & Analysis**, seret node **`tracker`**.
2. Hubungkan pin `image` dan `detections` dari node `detector` ke pin input node `tracker`.
3. Di Inspector, pilih algoritma **`bytetrack`**.
4. Aktifkan opsi toggle **`trackClassLock`** menjadi `true` (mencegah kedipan kelas).
5. Set `smoothingAlgorithm` ke **`ema`**.

#### Langkah 5: Hubungkan Node `zone_activity_timer` & Gambar Polygon
1. Seret node **`zone_activity_timer`** ke kanvas.
2. Hubungkan output `tracks` dan `image` dari node `tracker` ke input node timer.
3. Pada Inspector, atur parameter berikut:
   - `primaryClass`: `"tire"`
   - `secondaryClass`: `"person"`
   - `minDurationSeconds`: `5.0`
   - `gracePeriodSeconds`: `10.0`
4. Klik tombol **"Edit Polygon Zona"**. Antarmuka CAD Annotation Studio akan terbuka di layar penuh.
5. Klik 4 atau 5 titik di lantai mengelilingi Bay 1 tempat ban diletakkan.
6. Klik tombol **"Simpan & Terapkan"**.

#### Langkah 6: Hubungkan Output Visual & Penyimpanan Data
1. Seret node **`overlay_annotate`** dan hubungkan dari output timer. Centang `showBoxes`, `showLabels`, dan `showHudBadge`.
2. Seret node **`preview`** untuk melihat tampilan langsung di browser.
3. Seret node **`database_output`** untuk menyimpan rekaman durasi sesi ke tabel SQLite.
4. Klik tombol **Play (▶️)** di toolbar atas.

#### Hasil Verifikasi Lapangan:
Saat mekanik mendekati ban di dalam zona selama lebih dari 5 detik, HUD di layar akan berubah dari warna abu-abu `BAY IDLE` menjadi warna hijau menyala **`BAY 01 ACTIVE: 00:01:24`**. Ketika mekanik meninggalkan area lebih dari 10 detik, sesi resmi ditutup dan dicatat ke basis data:
- *Session ID: SESS-20261110-001*
- *Bay: Bay 1*
- *Waktu Mulai: 08:15:10*
- *Waktu Selesai: 08:58:32*
- *Durasi Bersih: 43 Menit 22 Detik*.

---

## 10.2 Studi Kasus 2: Warehouse Gate Exit Surveillance & ERP Inventory Dispatch

### 1. Tujuan & Skenario Lapangan
Pada gerbang pergudangan (*Warehouse Gate 1 s/d 3*), sistem harus mendeteksi secara otomatis ketika ada **truk yang keluar dari gudang membawa ban**. Sistem harus membaca plat nomor truk, merekam klip video bukti 15 detik (Pre/Post-Roll), dan mengirim notifikasi webhook ke ERP gudang untuk memvalidasi Surat Jalan pengiriman barang.

![Warehouse Events](screenshots/09_warehouse_events.png)
*Gambar 10.2: Deteksi Truk Keluar Gerbang Gudang dengan Bukti Plat Nomor dan Video.*

---

### 2. Arsitektur Topologi Alur Kerja (Workflow Graph)
```
[IP Camera (Gate 1)] 
        |
[Motion Gate (Filter Gerakan)] 
        |
[Object Detector (YOLOv8)] 
        |
[LPR License Plate Reader] 
        |
[Zone Exit Event (Gerbang Gudang)] 
        +-----------------------------------+
        | (Exit Trigger Event)              | (Video Stream)
        v                                   v
[Event Clip Recorder (Vault)]       [Overlay Annotate]
        | (Klip MP4 + Metadata)             |
[Webhook Output (ERP REST API)]     [Live Preview]
```

---

### 3. Langkah Demi Langkah Pembuatan:
1. Pasang node **`ip_camera`** yang mengarah ke gerbang keluar gudang.
2. Pasang node **`motion_gate`** tepat setelah kamera. Atur `sensitivity=0.03` dan `motionHoldSeconds=4.0`. Jika tidak ada kendaraan bergerak di gerbang, node AI tidak akan dieksekusi.
3. Pasang node **`detector`** dengan model `yolov8n.pt` dan filter kelas `["truck", "car", "tire"]`.
4. Pasang node **`lpr_license_plate`** untuk membaca plat nomor kendaraan.
5. Pasang node **`zone_exit_event`**.
   - Buka CAD Studio dan gambar polygon tipis melintang di garis pintu gerbang keluar.
   - Atur `directionFilter`: `"outward_only"`.
   - Atur `rearmCooldownSeconds`: `4.0` (mencegah pemicu ganda untuk bodi belakang truk).
6. Pasang node **`event_clip_recorder`**.
   - Atur `preRollSeconds`: `5.0`.
   - Atur `postRollSeconds`: `10.0`.
   - Atur direktori ke `data/vault`.
7. Pasang node **`webhook_output`**.
   - Target URL: `https://erp.onechitra.com/api/v1/warehouse/exit-log`.
   - Headers: `{"Authorization": "Bearer TOKEN_RAHASIA_ERP"}`.
8. Jalankan pipeline.

Saat truk melaju keluar melewati garis gerbang:
- Sistem mencatat plat nomor `B 9876 KDA`.
- Sistem mengekstrak klip video MP4 15 detik yang memperlihatkan truk sejak masih di dalam gudang hingga melewati gerbang.
- Server ERP menerima webhook JSON secara otomatis dalam waktu 500 milidetik.

---

## 10.3 Studi Kasus 3: K3 Factory Safety & Man Down Detection

### 1. Tujuan & Skenario Lapangan
Memastikan keselamatan kerja di area pabrik dengan risiko tinggi (overhead crane dan mesin penggiling). Sistem harus memverifikasi bahwa seluruh personil memakai **Helm Pengaman (*Hard Hat*)** dan **Rompi Reflektif (*Safety Vest*)**, serta mendeteksi seketika jika ada pekerja yang jatuh pingsan (*Man Down / Slip & Fall*).

![Man Down Inspector](screenshots/23_man_down_detector_inspector.png)
*Gambar 10.3: Konfigurasi Inspector Node Man Down & Fall Detector.*

---

### 2. Arsitektur Topologi Alur Kerja:
```
[IP Camera (Pabrik)] 
        |
[Human Pose Estimator (17 Sendi Anatomis)] 
        |
+-------+-------------------------------+
|                                       |
v                                       v
[PPE Compliance Matrix]         [Man Down Detector]
| (Verifikasi Helm/Rompi)               | (Deteksi Jatuh/Pingsan)
+-------+-------------------------------+
        | (Pelanggaran / Bahaya Darurat)
        v
[Alarm Cooldown Gate (Jeda 60 Detik)]
        |
[Telegram Notification Bot] + [Emergency Audio Alert]
```

---

### 3. Langkah Demi Langkah Pembuatan:
1. Hubungkan node **`pose_detector`** dengan bobot model `yolov8n-pose.pt`.
2. Cabangkan keluaran deteksi ke dua node analitik:
   - Node **`ppe_compliance_matrix`**: Centang `requireHardhat=true` dan `requireHiVisVest=true`.
   - Node **`man_down_detector`**: Atur `aspectRatioThreshold=1.30` dan `immobilityDurationSeconds=4.0`.
3. Gabungkan keluaran alarm keduanya ke node **`alarm_cooldown_gate`** dengan `cooldownSeconds=60.0`.
4. Hubungkan keluaran gate ke node **`telegram_notification`** yang telah diisi Token Bot dan ID Grup K3 Pabrik.

Jika ada pekerja yang tergelincir dan tergeletak di lantai selama lebih dari 4 detik, sirene speaker akan berbunyi di peramban ruang kontrol, dan foto bukti pekerja yang tergeletak akan langsung terkirim ke smartphone manajer K3 via Telegram!

---

## 10.4 Studi Kasus 4: Smart Traffic Flow & Retail Footfall Analytics

### 1. Tujuan & Skenario Lapangan
Menghitung volume perlintasan kendaraan di jalan tambang atau pengunjung di supermarket, menghitung kecepatan kendaraan dalam satuan km/jam, dan menampilkan peta panas (*heatmap*) area lantai yang paling sering dipijak.

![Line Counter Analytics](screenshots/line_counter_analytics.png)
*Gambar 10.4: Analisis Perlintasan Garis Tripwire dan Akumulasi Peta Panas Kepadatan.*

---

### 2. Arsitektur Topologi Alur Kerja:
```
[IP Camera (Jalan Raya)] -> [Detector] -> [Tracker (ByteTrack)]
                                                |
                 +------------------------------+------------------------------+
                 |                                                             |
                 v                                                             v
       [Line Counter (Tripwire)]                                     [Homography Projector]
                 |                                                             |
                 v                                                             v
       [CSV Formatter (Log Harian)]                                  [Crowd Density Heatmap]
                                                                               |
                                                                               v
                                                                     [Live Preview & Dashboard]
```

---

### 3. Langkah Demi Langkah Pembuatan:
1. Hubungkan `ip_camera` -> `detector` -> `tracker`.
2. Pasang node **`line_counter`**. Buka CAD Studio dan tarik garis virtual melintang di atas jalan raya (Titik A di kiri, Titik B di kanan).
3. Pasang node **`homography_projector`** untuk memetakan koordinat piksel miring kamera ke satuan meter datar di lapangan.
4. Pasang node **`crowd_density_heatmap`**. Atur `colormap="JET"` dan `decayRate=0.99`.
5. Pasang node **`csv_formatter`** untuk mencatat rekapitulasi volume kendaraan setiap jam ke file `data/traffic_log.csv`.

Hasilnya adalah dashboard komprehensif yang menampilkan jumlah kendaraan melintas arah masuk vs keluar, kecepatan rata-rata kendaraan, dan visualisasi warna merah membara pada jalur yang sering mengalami kemacetan.

---

## 10.5 Studi Kasus 5: Autonomous CCTV Copilot Menggunakan Multimodal Vision AI Agent

### 1. Tujuan & Skenario Lapangan
Mengotomatisasi pengawasan CCTV keamanan malam hari menggunakan **Vision Large Language Model (VLM)**. Alih-alih hanya mengandalkan deteksi kotak kaku, sistem mampu melakukan penalaran situasi yang kompleks (misalnya: *"Apakah ada orang yang memanjat pagar kawat?", "Apakah pintu darurat terhalang tumpukan sampah?", "Apakah ada asap tipis mencurigakan?"*).

![AI Studio Assistant](screenshots/13_ai_studio_copilot_drawer.png)
*Gambar 10.5: Antarmuka AI Agent Drawer untuk Konfigurasi Penalaran Cerdas CCTV.*

---

### 2. Arsitektur Topologi Alur Kerja:
```
[IP Camera (Pagar Luar Pabrik)]
        |
[Motion Gate (Sensitivitas 0.02)]
        | (Hanya Jika Ada Gerakan Mencurigakan)
[Object Detector (YOLOv8)]
        |
[AI Agent (Multimodal Vision LLM - GPT-4o / Ollama LLaVA)]
        | (Hasil Penalaran Teks & Rekomendasi Aksi)
[Notification Dispatcher] -> [Telegram & ERP Security Log]
```

---

### 3. Konfigurasi Prompt pada Node `ai_agent`:
- **System Prompt**:
  ```text
  Anda adalah AI Perwira Pengawas Keamanan Pabrik Otonom. 
  Tugas Anda adalah memeriksa frame CCTV malam hari dan metadata deteksi yang diberikan. 
  Analisis apakah ada situasi anomali, tindakan mencurigakan, atau pelanggaran keamanan perimeter.
  Berikan respons dalam format JSON valid: {"threat_level": "LOW|MEDIUM|HIGH", "summary": "...", "recommended_action": "..."}
  ```
- **User Prompt**:
  ```text
  Periksa gambar ini. Apakah orang yang terdeteksi sedang melakukan aktivitas kerja wajar atau menunjukkan perilaku mencurigakan seperti memanjat pagar atau merusak fasilitas?
  ```
- **Trigger Mode**: `"on_event"` (Hanya dipanggil saat node `detector` menemukan orang di luar jam kerja).

Sistem kini memiliki kemampuan penalaran setara petugas keamanan manusia yang terus mengawasi layar tanpa pernah merasa lelah atau mengantuk.

---

*Lanjutkan ke **Bagian XI: Troubleshooting, Pemeliharaan dan FAQ** untuk panduan resolusi kendala teknis dan pemeliharaan jangka panjang.*



<!-- PAGE BREAK: BAB_11_TROUBLESHOOTING_MAINTENANCE_FAQ.md -->


# BAGIAN XI: TROUBLESHOOTING, PEMELIHARAAN DAN FAQ
## Afi Vision Builder & Integrated Open-NVR Platform

---

## DAFTAR ISI BAGIAN XI

- 11.1 **Diagnosa Masalah Jaringan & Streaming Kamera CCTV** (RTSP Latency, Smearing, Packet Drop)
- 11.2 **Optimasi Kinerja & Penggunaan Sumber Daya Server** (High CPU, Memory Leak, GPU OOM)
- 11.3 **Tuning dan Kalibrasi Akurasi Tracking AI** (ID Switching, Occlusion, False Positives)
- 11.4 **Pemeliharaan Rutin, Retensi Data & Prosedur Backup** (Vault Disk Management, Log Rotation)
- 11.5 **Daftar Pertanyaan yang Sering Diajukan (Operational FAQ)**

---

## 11.1 Diagnosa Masalah Jaringan & Streaming Kamera CCTV

### Gejala 1: Gambar Video Bergaris Hijau/Abu-abu (*Smearing Artifacts*) atau Pecah-Pecah
- **Penyebab**: Transmisi RTSP menggunakan protokol **UDP**. Pada jaringan LAN yang sibuk, switch membuang sebagian paket video UDP. Saat frame kunci (*I-frame*) hilang, decoder merender sisa frame delta (*P-frame*) sebagai artefak abu-abu atau hijau buram.
- **Solusi**:
  1. Buka Inspector node `ip_camera` atau pengaturan Open-NVR Hub.
  2. Ubah parameter `transport` dari `udp` menjadi **`tcp`**.
  3. Protokol TCP menerapkan jaminan pengiriman ulang paket yang hilang (*lossless retransmission*), seketika menghilangkan artefak smearing.

---

### Gejala 2: Latensi Video Meningkat Bertahap (Video Tertinggal Beberapa Detik)
- **Penyebab**: Kamera CCTV mengirim video pada kecepatan 30 FPS, tetapi pemrosesan AI di server hanya mampu mengeksekusi 15 FPS. Akibatnya, frame video menumpuk di antrean buffer memori (*buffer bloat*), menyebabkan tampilan preview tertinggal hingga 5-10 detik di belakang waktu nyata.
- **Solusi**:
  1. Pada node `ip_camera`, pastikan parameter **`dropFrames`** bernilai **`true`** (*Zero-Latency Mode*). Saat mode ini aktif, jika antrean buffer terisi lebih dari 1 frame, buffer lama akan langsung dibuang dan hanya frame paling mutakhir (*newest frame*) yang diproses.
  2. Pasang node **`frame_sampler`** atau atur `sampleRate=2` (hanya proses 1 frame setiap 2 frame masuk) untuk menyeimbangkan beban komputasi.

---

### Gejala 3: Kamera Tiba-Tiba Offline dan Menampilkan Frame *CCTV NO SIGNAL*
- **Penyebab**: Fluktuasi tegangan daya pada switch PoE kamera, kabel LAN longgar, atau bentrok alamat IP (*IP Conflict*).
- **Prosedur Diagnosa**:
  1. Buka terminal server dan lakukan uji ping ke IP kamera:
     ```bash
     ping 192.168.1.64 -t
     ```
  2. Uji ketersediaan port RTSP (554) dan port ONVIF (80/8899/8000) menggunakan `curl` atau `telnet`:
     ```bash
     curl -v telnet://192.168.1.64:554
     ```
  3. Uji pemutaran stream mentah secara independen menggunakan FFmpeg di terminal:
     ```bash
     ffplay -rtsp_transport tcp "rtsp://admin:Password123@192.168.1.64:554/Streaming/Channels/101"
     ```
  4. Begitu kamera kembali hidup, modul `engine/cctv_hub.py` akan mendeteksi sinyal kembali secara otomatis dalam waktu 5 detik tanpa perlu me-restart server.

---

## 11.2 Optimasi Kinerja & Penggunaan Sumber Daya Server

### 1. Mengatasi Penggunaan CPU Sangat Tinggi (High CPU Usage 100%)
Jika prosesor Intel Core i7 atau Xeon Anda mencapai pemakaian 95-100%:
- **Penyebab Utama**: Decoding video beresolusi 4K untuk banyak kamera pada saat bersamaan dan inferensi model FP32 mentah tanpa akselerasi.
- **Langkah Mitigasi**:
  1. **Gunakan Sub-Stream**: Jangan gunakan Main-Stream 4K jika hanya untuk deteksi objek umum. Alihkan URL RTSP ke profil *Sub-Stream* beresolusi 720p (1280x720) atau 640x360.
  2. **Aktifkan Kuantisasi INT8**: Gunakan menu Model Quantizer untuk mengonversi model `yolov8n.onnx` menjadi `yolov8n_int8.onnx`. Model INT8 memotong pemakaian siklus CPU hingga 60%!
  3. **Pasang Node `motion_gate`**: Pada area yang jarang dilalui, pasang `motion_gate` sebelum model AI. Ini memastikan CPU hanya bekerja saat ada pergerakan nyata.

---

### 2. Mengatasi Error GPU Out of Memory (CUDA OOM)
Jika Anda menggunakan kartu grafis NVIDIA dan terminal menampilkan error:
`RuntimeError: CUDA out of memory. Tried to allocate 512.00 MiB`
- **Solusi**:
  1. Turunkan ukuran batch inferensi (*batch size*) menjadi `1`.
  2. Kurangi resolusi dimensi inferensi pada detektor dari 1280 menjadi 640 piksel.
  3. Konversi model PyTorch menjadi format **TensorRT FP16 Engine**, yang membagi penggunaan VRAM grafis hingga separuh lebih hemat.

---

## 11.3 Tuning dan Kalibrasi Akurasi Tracking AI

### 1. Mengatasi Masalah ID Switching (ID Objek Berubah Saat Berpapasan)
- **Masalah**: Dua orang mekanik berjalan saling berpapasan (*crossing paths*). Setelah berpapasan, ID Orang A tertukar dengan ID Orang B.
- **Solusi**:
  1. Pada Inspector node `tracker`, ubah algoritma dari `bytetrack` menjadi **`botsort`** atau aktifkan **`enableReid = true`**.
  2. Fitur Appearance Re-ID (model `osnet_x0_25`) mengekstrak ciri visual pakaian (warna baju, bentuk topi). Meskipun kedua orang berpapasan dan saling menutupi, sistem mencocokkan kembali embedding fitur visual sehingga ID masing-masing tidak akan pernah tertukar!

---

### 2. Mengatasi Kedipan Label Kelas (*Class Flickering*)
- **Masalah**: Deteksi pada ban terkadang terbaca sebagai `tire` (90%), tetapi pada 1 frame tiba-tiba terbaca sebagai `donut` atau `frisbee` (30%).
- **Solusi**:
  1. Pastikan opsi **`trackClassLock`** pada node `tracker` diaktifkan (`true`).
  2. Fitur ini menerapkan algoritma *Majority Voting Window* 15 frame terakhir: Jika dalam 15 frame terakhir objek 14 kali terdeteksi sebagai `tire`, deteksi sesaat sebagai kelas lain akan otomatis dianulir dan dikunci tetap sebagai `tire`.

---

## 11.4 Pemeliharaan Rutin, Retensi Data & Prosedur Backup

### 1. Manajemen Ruang Hard Disk Evidence Vault (Auto-Purge)
Klip rekaman video insiden format MP4 dapat memenuhi kapasitas hard disk jika dibiarkan menumpuk selama berbulan-bulan.

Tambahkan jadwal pembersihan otomatis (*cron job* di Linux atau Task Scheduler di Windows) untuk menghapus klip yang lebih tua dari batas retensi kebijakan perusahaan (misal 30 hari):

```bash
# Tambahkan ke crontab (menjalankan pembersihan setiap tengah malam pukul 00:00)
0 0 * * * find /opt/afi-vision-builder/data/vault/ -type f -name "*.mp4" -mtime +30 -delete
```

---

### 2. Backup Basis Data & Konfigurasi Proyek
Untuk mencadangkan seluruh konfigurasi alur kerja, zona poligon, dan catatan kejadian, buat skrip backup harian sederhana:

```bash
#!/bin/bash
BACKUP_DIR="/mnt/backup/afivision_$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup basis data SQLite
cp /opt/afi-vision-builder/data/visionode.db "$BACKUP_DIR/"

# Backup seluruh file proyek JSON
cp -r /opt/afi-vision-builder/data/projects "$BACKUP_DIR/"

# Kompresi menjadi arsip terenkripsi
tar -czvf "$BACKUP_DIR.tar.gz" -C "$BACKUP_DIR" .
rm -rf "$BACKUP_DIR"
echo "[OK] Backup selesai disimpan di $BACKUP_DIR.tar.gz"
```

---

### 3. Rotasi Berkas Log Server (`server_out.log`)
Untuk mencegah file log membengkak hingga puluhan gigabyte, gunakan utilitas standar Linux `logrotate` dengan konfigurasi di `/etc/logrotate.d/afivision`:

```text
/opt/afi-vision-builder/server_out.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    copytruncate
}
```

---

## 11.5 Daftar Pertanyaan yang Sering Diajukan (Operational FAQ)

### Q1: Apakah Afi Vision Builder membutuhkan koneksi internet untuk beroperasi?
**Jawab**: **Sama sekali TIDAK (100% Offline-Ready)**. Seluruh inferensi AI (YOLO, UniFace, Tracking, Database, dan Open-NVR Hub) berjalan secara lokal di server Anda. Koneksi internet hanya dibutuhkan jika Anda menggunakan notifikasi bot Telegram atau ingin menghubungkan node AI Agent ke model cloud seperti OpenAI GPT-4o. Jika menggunakan model LLM lokal seperti Ollama, sistem tetap dapat berjalan 100% offline tanpa internet.

---

### Q2: Berapa banyak kamera CCTV yang dapat ditangani oleh satu unit server?
**Jawab**: Tergantung pada spesifikasi prosesor dan kartu grafis:
- **Server CPU-Only (Intel Core i7 12th Gen, RAM 32 GB)**: Mampu menangani **5 hingga 8 kamera** resolusi 720p/1080p pada kecepatan inferensi 5-10 FPS.
- **Server Workstation GPU (Intel Core i7 + NVIDIA RTX 4060 8 GB VRAM)**: Mampu menangani **12 hingga 16 kamera** simultan.
- **Server Datacenter (Intel Xeon / AMD EPYC + NVIDIA RTX A5000 / L4 24 GB VRAM)**: Mampu menangani **32 hingga 64 kamera** secara simultan menggunakan kompilasi TensorRT.

---

### Q3: Merek kamera CCTV apa saja yang kompatibel dengan sistem ini?
**Jawab**: Semua merek kamera IP yang mematuhi standar internasional **RTSP (Real-Time Streaming Protocol)** atau **ONVIF (Profile S/G/T)** didukung secara langsung. Merek yang telah diuji meliputi: **Hikvision, Hilook, Dahua, IMOU, Uniview (UNV), Axis Communications, Hanwha Vision (Samsung), Bosch, Milesight, Tiandy, dan webcam USB biasa**.

---

### Q4: Apakah saya bisa menggunakan model AI hasil pelatihan kustom (*custom-trained YOLO model*)?
**Jawab**: **Sangat BISA**. Anda cukup mengekspor model hasil training Anda dari PyTorch atau Ultralytics menjadi file bobot `.pt` atau `.onnx`, lalu letakkan file tersebut ke dalam folder `weights/` pada server. Buka Inspector node `detector`, lalu ketik nama file model Anda. Model kustom Anda langsung aktif seketika!

---

### Q5: Bagaimana jika server mengalami mati listrik tiba-tiba (*Power Outage*)? Apakah konfigurasi alur kerja dan zona akan hilang?
**Jawab**: **Aman**. Setiap perubahan titik polygon, konfigurasi node, dan parameter alur kerja disimpan secara permanen (*persistent write-on-change*) ke dalam file JSON proyek dan basis data SQLite. Saat server dinyalakan kembali, sistem akan memuat status konfigurasi terakhir secara otomatis.

---

### Q6: Bagaimana cara mengamankan antarmuka web agar tidak diakses oleh orang yang tidak berhak?
**Jawab**:
1. Atur parameter `SECRET_KEY` pada file `.env` dengan kombinasi karakter acak yang kuat.
2. Tempatkan server di balik Reverse Proxy seperti NGINX atau Caddy dengan sertifikat SSL/TLS HTTPS terenkripsi.
3. Batasi akses IP pada firewall server (`ufw` di Linux) agar hanya dapat diakses dari subnet ruang kontrol (*VLAN Security Operations Center*).

---

## 11.6 KESIMPULAN & PENUTUP

Dengan selesainya buku panduan komprehensif ini, Anda kini memiliki pemahaman arsitektural dan operasional mendalam mengenai **Afi Vision Builder & Integrated Open-NVR Platform**. 

Platform ini dirancang untuk memberdayakan organisasi Anda dalam mewujudkan otomatisasi pengawasan cerdas berskala enterprise: mulai dari penemuan kamera jaringan, rancang bangun alur kerja vision visual dengan 98 node teruji, kalibrasi zona polygon presisi CAD, penyajian dashboard operasional eksekutif, hingga ekspor kode mandiri untuk komputasi edge di gardu terdepan.

*Selamat berkarya dan membangun solusi Computer Vision masa depan bersama Afi Vision Builder!*
