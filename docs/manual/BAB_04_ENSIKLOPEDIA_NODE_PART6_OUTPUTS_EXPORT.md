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

![Evidence Vault](../screenshots/006_nvr_hub_evidence_vault.png)
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

![Export Code Modal](../screenshots/005-05_dashboard_docker_export_modal_ready.png)
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
