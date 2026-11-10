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
