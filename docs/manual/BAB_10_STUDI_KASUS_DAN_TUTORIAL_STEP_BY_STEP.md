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

![Workshop Sessions](../screenshots/08_workshop_sessions.png)
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

![Warehouse Events](../screenshots/09_warehouse_events.png)
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

![Man Down Inspector](../screenshots/23_man_down_detector_inspector.png)
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

![Line Counter Analytics](../screenshots/line_counter_analytics.png)
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

![AI Studio Assistant](../screenshots/13_ai_studio_copilot_drawer.png)
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
