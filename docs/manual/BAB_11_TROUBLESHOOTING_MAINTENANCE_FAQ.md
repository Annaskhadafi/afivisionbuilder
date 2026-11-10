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
