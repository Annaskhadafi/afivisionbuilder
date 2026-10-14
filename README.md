# AFI Vision Builder 🚀

**AFI Vision Builder** adalah platform visual berbasis node-graph untuk merancang, menguji, dan menjalankan pipeline Computer Vision & AI secara interaktif tanpa perlu menulis kode rumit.

---

## 🌟 Fitur Utama

- **Node-Graph Editor Lengkap**: Kanvas visual interaktif untuk menyusun alur pengolahan citra dan deteksi objek.
- **44 Node Siap Pakai**:
  - **Input**: Kamera Web, IP Camera (RTSP/HTTP), Daheng Industrial Camera, Video File, Static Image.
  - **AI Models**: RF-DETR, Ultralytics YOLO (v8, v11, segmentasi, klasifikasi), SAM 3, ConvNeXt, EfficientAD Anomaly Inspection, ONNX, TFLite.
  - **Tracking**: ByteTrack, BoT-SORT (Camera Motion Compensation), OC-SORT.
  - **Analitik & Counting**: Multi-Line Counter (IN/OUT), Object Counter, Dwell Time (Zona Waktu Diam), ROI Filter.
  - **Logika & Percabangan**: If / Else, Compare Value, Confidence Threshold, Timer Delay, Debounce, Rate Limiter, AND / OR Logic, Trigger Once.
  - **Pemrosesan Citra**: Resize, Crop, Rotate / Flip, Color Conversion, Brightness / Contrast (Night Vision CLAHE), Blur / Sharpen (Gaussian, Median, Bilateral), Perspective Correction, Privacy Blur (Sensor Wajah/Plat).
  - **Output & Integrasi**: Live Preview, Event Alert, Image / Crop Output, SQLite Database Logger, HTTP Webhook.
- **Interactive UI**: Slider dinamis, auto-clamp pembatasan nilai, dan alat gambar area langsung di atas preview.
- **Auto CPU/GPU Fallback**: Mendukung akselerasi CUDA GPU dengan fallback otomatis ke CPU jika perangkat GPU tidak tersedia.

---

## ⚡ Cara Instalasi & Menjalankan (Windows)

### 1. Prasyarat
- **Python 3.10 / 3.11 / 3.12** terinstal di sistem.
- Pastikan opsi **"Add Python to PATH"** dicentang saat instalasi Python.

### 2. Instalasi Dependensi Otomatis
Cukup klik dua kali berkas:
```text
install.bat
```
Skrip ini akan secara otomatis membuat virtual environment (`.venv`), mengupdate pip, dan menginstall seluruh paket dependensi yang dibutuhkan.

### 3. Menjalankan Aplikasi
Cukup klik dua kali berkas:
```text
run.bat
```
Skrip ini akan mengaktifkan virtual environment, menyalakan server backend, dan otomatis membuka peramban web di:
👉 **http://127.0.0.1:8765**

---

## 🐧 Cara Instalasi & Menjalankan (Linux / macOS)

1. Berikan izin eksekusi pada skrip:
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

## 📂 Struktur Direktori

```text
afivisionbuilder/
├── engine/              # Runtime inti pemrosesan citra, inferensi AI, dan pelacakan
├── static/              # Frontend webapp (app.js, style.css, index.html)
├── data/
│   ├── models/          # Model AI (.pt, .onnx, dll)
│   ├── projects/        # File konfigurasi alur kerja (workflow.json)
│   ├── outputs/         # Hasil rekaman tangkapan event dan crop
│   └── uploads/         # Berkas media yang diunggah
├── server.py            # Backend server FastAPI
├── desktop_app.py       # Peluncur aplikasi desktop
├── requirements.txt     # Daftar dependensi Python
├── install.bat          # Skrip instalasi Windows
├── run.bat              # Skrip peluncuran Windows
├── install.sh           # Skrip instalasi Linux/macOS
├── run.sh               # Skrip peluncuran Linux/macOS
└── README.md
```

---

## 📄 Lisensi
Hak Cipta (c) AFI Vision Builder. Seluruh hak cipta dilindungi undang-undang.
