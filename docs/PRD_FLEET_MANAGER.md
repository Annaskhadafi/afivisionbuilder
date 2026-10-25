# Dokumen Persyaratan Produk (PRD) — Pengelola Layanan Alur Kerja (Workflow Fleet Manager)

**Nama Fitur:** Multi-Workflow Background Runner & Fleet Service Hub  
**Target Proyek:** `D:\[01] PROJECT\REA\webapp`  
**Tanggal:** 24 Oktober 2026  
**Status:** Disetujui (Approved) & Dalam Tahap Eksekusi  

---

## 1. Ringkasan Eksekutif & Latar Belakang

AFI Vision Builder sebelumnya beroperasi dengan paradigma *Single Active Canvas*, di mana hanya ada satu alur kerja yang dapat dijalankan secara aktif di studio kanvas. Ketika pengguna beralih proyek atau ingin memantau beberapa titik CCTV sekaligus (misalnya 1 kamera gerbang gudang, 1 kamera area parkir, dan 1 kamera meja kasir), sistem sebelumnya menolak eksekusi simultan dengan pesan kesalahan `409 workflow already running`.

Fitur **Workflow Fleet Manager** mentransformasi AFI Vision Builder dari sekadar editor prototipe kanvas menjadi **Mesin Visi Produksi Multi-Kanal (Multi-Pipeline Vision Engine)**. Pengguna dapat menyimpan banyak alur kerja, memilih alur kerja mana saja yang ingin dijalankan secara bersamaan di latar belakang (24/7), mengatur alur kerja mana yang diistirahatkan (idle/draft), serta memantau kesehatan seluruh aliran video secara visual melalui satu pusat kontrol (*Fleet Hub*).

---

## 2. Sasaran & Nilai Bisnis

1. **Eksekusi Paralel Mandiri:** Menjalankan hingga 5 alur kerja analitik secara bersamaan di latar belakang tanpa saling memblokir.
2. **Isolasi Kegagalan (Fault Isolation):** Gangguan pada satu stream kamera (misal koneksi RTSP terputus atau paket video korup) tidak boleh mematikan alur kerja lain maupun server utama.
3. **Efisiensi Beban Komputasi (FPS Governor):** Menyediakan kontrol *Target FPS* per alur kerja (pilihan 5, 10, 15 FPS atau Maksimal) agar inferensi model pada CPU laptop/PC lokal tetap adem dan tidak memicu *CPU throttling*.
4. **Sentralisasi Pemantauan (Matrix Monitor):** Menyajikan panel pemantau multi-layar (grid video) untuk melihat tangkapan kamera dari semua alur kerja aktif dalam satu pandangan mata.
5. **Keselarasan Studio Kanvas:** Alur kerja yang berjalan di latar belakang tetap dapat dibuka di kanvas tanpa menghentikan pemrosesan video yang sedang berlangsung.

---

## 3. Arsitektur Teknis

### A. Komponen Backend (`engine/fleet_manager.py`)
* **Registry Runner Terisolasi (`FleetManager`):**
  * Memelihara koleksi instance `core.WorkflowRunner` independen yang dipetakan berdasarkan `project_id`.
  * Setiap runner berjalan pada thread khususnya sendiri dengan penanganan eksepsi mandiri (`fail_safe`).
* **Siklus Hidup Alur Kerja (Lifecycle Methods):**
  * `start_workflow(project_id, target_fps=10)`: Memuat konfigurasi JSON alur kerja dari `workflow_store`, memvalidasi kelengkapan node, menginisiasi runner terisolasi, dan memulai proses inferensi.
  * `stop_workflow(project_id)`: Mengirim sinyal berhenti teratur dan membebaskan sumber daya memori/kamera.
  * `restart_workflow(project_id, target_fps=10)`: Mematikan alur kerja lama dan memuat ulang konfigurasi kanvas terbaru tanpa me-restart server.
  * `get_fleet_status()`: Menghimpun status waktu nyata seluruh proyek (kecepatan FPS riil, durasi aktif, pesan kesalahan, dan status aktif/berhenti).
  * `get_workflow_preview(project_id)`: Menyajikan frame gambar JPEG teranyar dari alur kerja untuk pratinjau matriks.
  * `stop_all()`: Penonaktifan bersih seluruh alur kerja saat server dimatikan.

### B. Lapisan Endpoint REST API (`server.py`)
* `GET /api/fleet/status`: Mengembalikan daftar seluruh proyek yang tersimpan beserta status runtime aktifnya.
* `POST /api/fleet/start`: Menerima payload `{ "projectId": str, "targetFps": int }` untuk menyalakan alur kerja.
* `POST /api/fleet/stop`: Menerima payload `{ "projectId": str }` untuk menghentikan alur kerja.
* `POST /api/fleet/restart`: Menerima payload `{ "projectId": str, "targetFps": int }` untuk memuat ulang alur kerja.
* `GET /api/fleet/preview/{project_id}`: Menyajikan snapshot frame JPEG terbaru untuk pemantauan multi-layar.

### C. Antarmuka Pengguna (`static/index.html`, `static/app.js`, `static/style.css`)
* **Tombol Akses Cepat:** Menambahkan tombol `🚀 Pengelola Layanan` pada bilah navigasi atas (topbar) lengkap dengan lencana jumlah alur kerja yang sedang aktif.
* **Modal Kontrol Fleet Hub:**
  * Tabel interaktif berisi nama alur kerja, jenis input kamera, pengaturan target FPS, indikator lampu status, dan sakelar toggle *ON/OFF*.
  * Bagian **Matriks Monitor Multi-Layar**: Panel pratinjau live yang menampilkan feed video kamera dari seluruh alur kerja yang sedang aktif secara berdampingan.
* **Integrasi Status Kanvas:**
  * Banner informatif pada kanvas studio jika alur kerja yang sedang diedit juga sedang aktif berjalan di latar belakang.

---

## 4. Kriteria Keberhasilan (Acceptance Criteria)

1. Pengguna dapat menyalakan minimal 2 alur kerja berbeda secara bersamaan dan keduanya menghasilkan FPS stabil (> 0 FPS).
2. Mematikan salah satu alur kerja tidak mempengaruhi kelancaran alur kerja yang lain.
3. Alur kerja yang mengalami kesalahan input kamera menampilkan label status `error` dengan pesan yang jelas tanpa membuat server padam.
4. Pratinjau video multi-layar dapat menampilkan feed dari masing-masing alur kerja aktif secara independen.
5. Seluruh unit test suite lulus pengujian tanpa regresi.
