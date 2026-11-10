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

Hasil tangkapan layar otomatis akan tersimpan di direktori `.e2e/artifacts/web/.../screenshots/` sebagai bukti audit visual antarmuka.

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
