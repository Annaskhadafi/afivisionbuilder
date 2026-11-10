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

![Export Code Modal](../screenshots/005-05_dashboard_docker_export_modal_ready.png)
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
