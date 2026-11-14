# 🚀 AFI Vision Builder

<p align="center">
  <b>Enterprise Visual Computer Vision Workflow Studio, OpenNVR CCTV Ingestion Hub & Real-Time Operational Dashboard Platform</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Ultralytics-YOLO26%20%7C%20YOLOv8-00FFFF?style=for-the-badge&logo=yolo&logoColor=black" alt="YOLO" />
  <img src="https://img.shields.io/badge/OpenNVR-Single--Source%20Ingest-10b981?style=for-the-badge&logo=cctv&logoColor=white" alt="OpenNVR" />
  <img src="https://img.shields.io/badge/Dashboard-No--Code%20Designer-8b5cf6?style=for-the-badge&logo=looker&logoColor=white" alt="Dashboard" />
  <img src="https://img.shields.io/badge/Nodes-98%2B%20Modular%20Nodes-f59e0b?style=for-the-badge" alt="Nodes" />
  <img src="https://img.shields.io/badge/Templates-43%20Paired%20Solutions-ec4899?style=for-the-badge" alt="Templates" />
  <img src="https://img.shields.io/badge/Tests-100%25%20Verified%20(Unit%20%2B%20E2E)-success?style=for-the-badge&logo=pytest&logoColor=white" alt="Tests" />
</p>

<p align="center">
  <a href="#-gambaran-umum">Gambaran Umum</a> •
  <a href="#-5-pilar-arsitektur-utama">5 Pilar Arsitektur</a> •
  <a href="#-fitur-unggulan">Fitur Unggulan</a> •
  <a href="#-katalog-node-vision">Katalog Node (98+)</a> •
  <a href="#-43-template-industri-siap-pakai">43 Template Industri</a> •
  <a href="#-instalasi--eksekusi-cepat">Panduan Cepat</a> •
  <a href="#-ekspor-kode--deployment">Ekspor & Deployment</a>
</p>

---

## 🌟 Gambaran Umum

**AFI Vision Builder** adalah platform visual tanpa-kode (*no-code / low-code*) terpadu untuk merancang, menguji, dan menerapkan pipeline **Computer Vision & Video Analytics** berskala industri secara real-time. 

Aplikasi ini menyatukan tiga fungsi penting yang sebelumnya terpisah dalam sistem terpisah:
1. **Visual Workflow Studio**: Perancangan alur kerja AI visual berbasis kanvas kabel kurva Bézier dengan 98+ node modular.
2. **OpenNVR CCTV Hub**: *Single Source of Truth* (SSoT) untuk penarikan video stream kamera fisik (RTSP / ONVIF) tanpa membebani perangkat CCTV, dilengkapi Live Matrix Wall dan Evidence Vault rekaman insiden.
3. **Operational Dashboard Designer**: Kanvas perancangan dasbor pemantauan real-time ala Elementor/Looker dengan sakelar CCTV Player `[🟢 Mode AI | 📹 Raw NVR]`, joystick kendali PTZ, serta pemutar klip video bukti insiden.

Semua alur kerja yang dirancang dapat langsung diekspor menjadi skrip Python mandiri (`run.py`) atau paket Docker Compose tanpa dependensi antarmuka web, siap di-deploy ke edge device (Raspberry Pi, Jetson, PC industri) maupun server cloud produksi.

---

## 🏛️ 5 Pilar Arsitektur Utama

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                     1. AFI OpenNVR CCTV Hub (SSoT)                     │
 │   ONVIF Discovery • Shared Ingest Buffer • Live Matrix Wall 2x2/3x3    │
 └───────────────────┬────────────────────────────────┬───────────────────┘
                     │ Zero-Copy In-Memory Frames     │ MP4 Video Vault
                     ▼                                ▼
 ┌──────────────────────────────────────┐     ┌───────────────────────────┐
 │       2. Visual Workflow Studio      │     │  3. Operational Dashboard │
 │  98+ Nodes • CAD Calibration Studio  │────▶│ Elementor-Style Drag/Drop │
 │ YOLO26/v8 • ByteTrack • BEV Projector│     │ Live AI/Raw Toggle • PTZ  │
 └───────────────────┬──────────────────┘     └───────────────────────────┘
                     │ Standalone Code Export
                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                 4. Production Edge & Docker Deployment                 │
 │     Headless Python Scripts • ONNX Runtime Native • Docker Compose     │
 └────────────────────────────────────────────────────────────────────────┘
```

### 1. 🏢 OpenNVR CCTV Hub & Single Source Ingest (SSoT)
* **Single Ingest Per Camera (`SharedCameraStream`)**: Aliran RTSP/ONVIF ditarik satu kali ke dalam memori bersama, lalu didistribusikan ke alur kerja AI dan dasbor pemantauan secara simultan. Menghilangkan masalah kamera fisik *freeze* atau *crash* akibat koneksi ganda.
* **Technical Standby Card (*CCTV NO SIGNAL*)**: Bila kamera mati atau koneksi terputus, sistem otomatis menyuplai frame teknis beranimasi halus (~16 FPS) dengan timestamp dan grid kalibrasi sehingga pipeline AI tidak terputus (*zero crash*).
* **Auto-Discovery & Direct RTSP**: Pemindaian jaringan lokal via WS-Discovery / SOAP Probing dan pendaftaran stream RTSP/HTTP langsung dalam hitungan detik.
* **Evidence Vault**: Perekaman ring buffer (5s pre-roll + 10s post-roll) yang otomatis menyimpan klip MP4 insiden saat terjadi pelanggaran K3 atau deteksi anomali.

### 2. ⚡ Visual Workflow Studio
* **98+ Node Modular**: Mulai dari preprocessing citra, deteksi objek (YOLOv8, YOLO26 NMS-Free, RF-DETR), segmentasi SAM 3, pose estimation, OCR, hingga analitik spasial tingkat lanjut.
* **1-Click Active / Bypass Mode**: Aktifkan atau lewati node secara instan via sakelar header kartu node tanpa perlu mencabut kabel kanvas.
* **CAD / Figma Grade Calibration Studio**: Area kalibrasi layar penuh beresolusi tinggi dengan mouse-wheel zoom (0.3x–8.0x), pan geser bebas, sub-pixel loupe magnifier 3x, serta editor garis hitung, poligon multi-zona, dan 4 titik proyeksi tanah BEV.
* **Python Script Sandbox**: Tulis fungsi OpenCV kustom `def process(frame, state):` langsung di peramban dengan validasi sintaks AST real-time dan preview 1-frame *Before vs After*.

### 3. 📊 No-Code Dashboard Designer
* **Kanvas Bebas Drag-and-Drop**: Susun dasbor operasional dengan grid snap, perataan otomatis, pemilihan ukuran kanvas (720p, 1080p, 2K, 4K, potret 9:16), dan tema terang berkelas (*light mode*).
* **Widget CCTV Player Interaktif**: Tombol instan `[🟢 Mode AI | 📹 Raw NVR]` untuk membandingkan anotasi visual AI dengan rekaman mentah, ditambah overlay joystick `🕹️ PTZ` (Pan, Tilt, Zoom, Stop).
* **Kolom Bukti & Pemutar Video Insiden**: Tombol `🎬 Bukti` pada widget tabel log insiden langsung membuka pemutar video rekaman MP4 modal untuk audit investigasi seketika.
* **43 Template Dasbor Otomatis (Zero Setup)**: Setiap alur kerja yang dibuat otomatis memiliki pasangan dasbor dengan susunan widget unik dan terhubung ke telemetri nyata (*DataBus*).

### 4. 🧠 Multi-Model AI Hub & Edge Quantizer
* **Model Registry Terpusat**: Manajemen bobot model lokal (`.pt`, `.onnx`, `.tflite`, `.engine`) dengan ekstraksi metadata otomatis dan proteksi path aman.
* **Integrasi VLM & AI Agent Multimodal**: Hubungkan alur kerja ke Vision-Language Model (OpenAI GPT-4o/5, 9router, Ollama) untuk inspeksi SOP dan penalaran visual kompleks.
* **Model Quantizer 1-Klik**: Kompresi model ke TFLite INT8/FP16 atau ONNX Dynamic INT8 langsung dari browser untuk pemangkasan ukuran hingga 75% pada perangkat edge.
* **Dukungan YOLO-World & Roboflow Universe**: Deteksi nol-latihan (*zero-shot*) via teks alami CLIP dan akses langsung ke 50.000+ model cloud Roboflow.

### 5. 🚀 Standalone Code Export & Edge Deployment
* **Ekspor Kode Mandiri (Standalone Python)**: Hasilkan satu berkas `run.py` mandiri yang mengemas alur kerja aktif, model, dan pipeline OpenCV untuk dijalankan tanpa antarmuka web.
* **Paket Docker 1-Klik**: Unduh arsip `.zip` siap pakai berisi `Dockerfile`, `docker-compose.yml`, dan dependensi lengkap untuk deployment instan di platform Dokploy, Portainer, atau server Kubernetes.

---

## ✨ Fitur Unggulan

| Kategori | Fitur & Deskripsi |
| :--- | :--- |
| **Kamera & NVR** | **SSoT Ingestion**, Auto-Scan ONVIF, Direct RTSP, PTZ Motor Control, Matrix Wall 2x2/3x3, Standby Card Graceful Fallback, dan Evidence Vault MP4 Recorder. |
| **Video Streams** | **Live YouTube Ingest (`yt-dlp`)**, Auto-Looping rekaman, Video Speed Controller (0.25x slow-mo hingga 4.0x fast-forward), dan Scrubbing / Seeking ke titik durasi tertentu. |
| **Deteksi & AI** | **Ultralytics YOLO26 NMS-Free**, YOLOv8, RF-DETR, SAM 3, YOLO-World zero-shot, UniFace ArcFace (Face Re-ID 512-D), MediaPipe 3D Hand Skeleton, dan PaddleOCR. |
| **Stabilitas Tracking** | **ByteTrack & BoT-SORT**, ReID Appearance Feature, Track Class Lock (anti-flicker), EMA Bounding Box Stabilizer, dan Consensus Voting multi-model. |
| **Analisis Spasial** | **Homography 2D BEV Projector**, Kalkulator Kecepatan (km/jam), Pengukur Jarak & Dimensi Fisik, Line Counter (Hysteresis Deadband), Multi-Zone Occupancy, dan Camera Focus Quality Score. |
| **K3 & Keselamatan** | **Safety PPE Compliance Matrix** (Helm, Rompi, Sepatu), Man Down & Fall Detector, Overstack Clearance Cargo, dan Alarm Cooldown Throttler. |
| **Dasbor & Visual** | **Interactive CCTV Player** (Mode AI / Raw NVR toggle), Joystick PTZ Overlay, Modal Bukti Insiden, 43 Paired Dashboards, 8 Google Fonts, dan Glassmorphism Styling. |
| **Integrasi & Sink** | **MQTT IoT / SCADA Gateway**, S3 Object Storage Cloud Sink (AWS / MinIO), Webhook Telegram / Slack, dan REST API. |

---

## 📦 Katalog Node Vision (98+ Nodes)

AFI Vision Builder dilengkapi dengan 98+ node modular yang terbagi dalam 7 kategori fungsional:

```text
[Sources & Ingest] ──▶ [Preprocessing] ──▶ [AI Inference] ──▶ [Tracking] ──▶ [Spatial Analytics] ──▶ [Outputs & Sinks]
```

<details>
<summary><b>Lihat Rincian Seluruh Kategori Node (Klik untuk Membuka)</b></summary>

### 1. Sumber Input Citra & Video (Sources)
* `input`: Input kamera webcam, file video MP4/MKV/AVI, RTSP URL, dan YouTube Stream via `yt-dlp`.
* `ip_camera`: Koneksi stream IP camera industri dengan manajemen retry otomatis.
* `nvr_source`: Integrasi langsung memori buffer OpenNVR Hub (Single-Source Ingestion).
* `video_speed_controller`: Kontrol kecepatan pemutaran (0.25x s/d 4.0x) dan scrubber seeking timeline.

### 2. Pra-Pemrosesan Citra & Filter (Preprocessing)
* `color_convert`, `brightness_contrast`, `blur_sharpen`, `undistort`: Kalibrasi visual citra.
* `clahe`: Peningkatan kontras adaptif untuk kondisi malam/rendah cahaya.
* `delta_filter`: Filter penghemat komputasi 70%+ untuk area pengawasan statis.
* `camera_focus`: Penilaian ketajaman fokus lensa berbasis variansi Laplacian.
* `auto_rotate_edges`: Pelurusan otomatis sudut rotasi objek dominan (*deskewing*).
* `slicer`: Slicing Aided Hyper Inference (SAHI) untuk objek mikro resolusi tinggi (4K/2K).

### 3. Inferensi AI & Detektor (Inference & Detectors)
* `detector`: YOLOv8, YOLO11, YOLO26 NMS-Free, dan custom model ONNX/TFLite/TensorRT.
* `rf_detr`: Transformer real-time object detector dengan akurasi tinggi.
* `yolo_world`: Detektor open-vocabulary berbasis teks prompt CLIP tanpa training ulang.
* `pose_detector`: YOLOv8 Pose 17-keypoints skeleton anatomis multi-warna.
* `face_detector` & `face_reid`: UniFace RetinaFace + ArcFace 512-D pengenal wajah.
* `hand_skeleton`: MediaPipe 21 sendi tangan 3D, deteksi cubit udara (pinch), dan pengenal gestur.
* `ocr_reader`: PaddleOCR DBNet + MobileNetV3 pembaca teks nomor plat & barcode.
* `ai_agent`: Multimodal VLM reasoning (GPT-4o/5, 9router, Ollama) untuk inspeksi SOP.

### 4. Pelacakan Objek & Stabilitas (Tracking & Filters)
* `tracker`: ByteTrack & BoT-SORT multi-object tracker.
* `reid`: Re-identification fitur visual appearance lintas oklusi.
* `track_class_lock`: Penguncian kelas dominan untuk mengeliminasi label flickering.
* `bbox_stabilizer`: Penghalusan posisi bounding box dengan Exponential Moving Average.
* `class_filter` & `confidence_filter`: Penyaringan kelas objek dan ambang batas per-kelas.
* `detections_consensus`: Fusi prediksi dari multi-model AI (IoU voting).

### 5. Pengukuran Spasial & Analitik Geometri (Spatial Analytics)
* `polygon_zone`, `multi_zone_occupancy`: Pemantauan kapasitas dan overstay multi-area.
* `line_counter`: Penghitung garis masuk/keluar dengan toleransi hysteresis deadband.
* `distance_measurement`: Pengukur jarak fisik antar objek (Euclidean meter/cm).
* `size_measurement`: Pengukur lebar, tinggi, dan luas fisik produk industri.
* `velocity_calculator`: Kalkulator kecepatan linier objek (km/jam atau m/s).
* `homography_projector` & `bev_visualizer`: Proyeksi perspektif tanah 2D Bird's Eye View (BEV).
* `overlap_analysis`: Analisis asosiasi spasial parent-child (misal: helm di atas kepala).
* `dynamic_zone`: Poligon area dinamis yang mengikuti unit anchor (truk/forklift).

### 6. Keselamatan Kerja & Industri K3 (Safety & Compliance)
* `ppe_compliance_matrix`: Matriks evaluasi kepatuhan APD (Helm, Rompi, Sepatu Safety).
* `man_down_detector`: Detektor orang jatuh dan ketidaksadaran di lantai kerja.
* `overstack_detector`: Pemantau batas ketinggian aman tumpukan kargo logistik.
* `dominant_color`: Verifikasi warna APD pekerja via ruang warna HSV adaptif.
* `lpr_license_plate`: Pembaca plat nomor kendaraan (ANPR) dengan regex Indonesia.

### 7. Output, Sinks & Notifikasi (Outputs & Sinks)
* `preview`: Live Preview video interaktif dengan layer anotasi visual komprehensif.
* `event_recorder`: Perekam klip bukti rekaman insiden (pre/post-roll MP4).
* `alarm_cooldown_gate`: Peredam badai spam notifikasi kejadian berulang.
* `mqtt_publisher`: Publisher telemetry kejadian ke PLC industri dan broker MQTT.
* `notification_dispatcher`: Notifikasi multi-kanal (Telegram Bot, Slack, Webhook).
* `s3_sink`: Unggah otomatis rekaman bukti kejadian ke AWS S3 / MinIO.
* `ptz_controller`: Pengendali motor kamera PTZ ONVIF (*auto-tracking*).
* `data_aggregator` & `csv_formatter`: Akumulasi statistik berkala dan ekspor CSV.
</details>

---

## 🏭 43 Template Industri Siap Pakai

Seluruh 43 alur kerja bawaan telah dilengkapi **video streaming YouTube aktif** serta **dasbor visual unik terpasang otomatis**:

```text
┌─────────────────────────────────┬─────────────────────────────────┬─────────────────────────────────┐
│       Smart Parking Lot         │       Retail Queue Manager      │       Vision Eye 360° Radar     │
│   Okupansi Slot P1..Pn & Plat   │   Panjang Antrean & Waktu Tunggu│  Blind-Spot Sektor Truk/Forklift│
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┤
│        AI Gym & Ergonomi        │    Workshop Zone Activity       │     Warehouse Logistics Exit    │
│  Hitung Repetisi & Audit Postur │   Akumulasi Jam Kerja Bengkel   │     Pencatatan Gerbang Muat     │
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┤
│      Safety PPE K3 Auditor      │       Conveyor Barcode Sorter   │     Highway Velocity Radar      │
│  Helm, Rompi & Sepatu Safety    │   Pemindaian Cepat Barang Cacat │   Kecepatan Nyata Arus Jalan    │
└─────────────────────────────────┴─────────────────────────────────┴─────────────────────────────────┘
```

Setiap template dapat dibuka langsung dari menu **Projects Hub**, dijalankan secara live, dan disesuaikan konfigurasinya sesuai kebutuhan lapangan.

---

## ⚡ Instalasi & Eksekusi Cepat

### Kebutuhan Sistem
* **Sistem Operasi**: Windows 10/11, Ubuntu 20.04/22.04+, macOS (Apple Silicon didukung).
* **Python**: Versi `3.10`, `3.11`, `3.12`, atau `3.13`.
* **Hardware**: CPU dual-core (rekomendasi quad-core ke atas); GPU NVIDIA (CUDA) opsional untuk akselerasi inferensi maksimal.

### Langkah Instalasi (3 Menit)

```bash
# 1. Klon repositori
git clone https://github.com/your-org/afi-vision-builder.git
cd afi-vision-builder

# 2. Buat dan aktifkan virtual environment
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# 3. Instal dependensi
pip install -r requirements.txt

# 4. Jalankan server aplikasi
python server.py
```

Buka peramban web di alamat:
```text
http://127.0.0.1:8765
```

### Notifikasi update dan penyimpanan proyek

Tombol **Update tersedia** di bilah atas membandingkan build aplikasi dengan commit terbaru branch `main` GitHub dan memeriksa ulang otomatis setiap jam. Klik untuk membuka detail perubahan; penerapan update dilakukan melalui redeploy host, tanpa perintah `git pull` dari pengguna aplikasi.

Untuk Docker/Dokploy, set build argument `VISONODE_BUILD_REVISION` ke SHA commit 40 karakter yang sedang dibuat agar status dapat dibandingkan. Data proyek (`projects.json` dan `projects/<id>/workflow.json`) disimpan pada `VISONODE_APP_DATA_DIR`; Compose memakai named volume `afi_vision_data`. Data tersebut diabaikan Git dan tidak disalin ke image atau dibuat ulang saat redeploy, jadi volume yang sama harus dipertahankan.

---

## 📦 Ekspor Kode & Deployment

Setiap alur kerja visual dapat diekspor secara mandiri melalui tombol **Export Code** di Studio:

```bash
# Hasil ekspor adalah satu paket folder mandiri:
exported_workflow/
├── run.py                 # Skrip eksekusi headless OpenCV & AI
├── requirements.txt       # Dependensi minimal yang dibutuhkan
├── workflow.json          # Definisi pipeline alur kerja
└── weights/               # Bobot model AI yang digunakan (.pt / .onnx)
```

Jalankan di server target tanpa antarmuka web:
```bash
python run.py --input "rtsp://admin:pass@192.168.1.50:554/stream1"
```

Tersedia pula opsi ekspor **Docker Compose Bundle** yang mengemas aplikasi ke dalam kontainer mandiri untuk deployment di Dokploy, Portainer, atau kluster cloud.

---

## 🧪 Pengujian & Penjaminan Kualitas

Aplikasi ini diverifikasi secara berkelanjutan dengan rangkaian pengujian berlapis:
* **Unit Tests (Pytest)**: Menguji integritas node vision, kalkulasi spasial, parser ONVIF, dan modul ekspor kode.
  ```bash
  python -m pytest tests/unit/
  ```
* **Real-Browser E2E Tests (Playwright)**: Memvalidasi interaksi antarmuka pengguna, pemutar video live, dan responsivitas dasbor secara nyata.
  ```bash
  npx e2e run tests/nvr_workflow_dashboard_integration.e2e.ts
  ```

---

## 📄 Lisensi & Pengembang

Dikembangkan oleh **Tim Rekayasa AI & Computer Vision Chitra Paratama**.  
Didistribusikan untuk otomasi pengawasan industri, keselamatan K3 pabrik, pergudangan modern, dan infrastruktur pintar.
