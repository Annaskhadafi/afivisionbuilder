# PRD — Afi Vision Operations

Tanggal: 14 Oktober 2026  
Status: Implementasi node proyek dimulai; kelulusan operasional tetap memerlukan pilot.  
Dokumen pelaksanaan: [TASK_LIST.md](TASK_LIST.md)

## 1. Tujuan produk

Mengembangkan Afi Vision Builder menjadi aplikasi web Python untuk merancang, menjalankan, dan memantau beberapa proyek computer vision pada satu server khusus. Editor visual tetap menjadi tempat konfigurasi; dashboard operasional menampilkan banyak kamera, status zona, hasil, dan kesehatan proses.

Proyek awal:

1. **Tire Workshop:** estimasi durasi aktivitas pekerjaan per zona berdasarkan keberadaan ban dan orang. Sumber awal: 5 kamera.
2. **Tire Warehouse:** alert saat truk atau ban keluar melalui batas yang ditentukan, lalu kirim screenshot dan metadata ke ERP. Sumber awal: 3 kamera.
3. **Road Inspection:** tahap lanjutan untuk kamera pada unit tambang dan integrasi API TPMS.

## 2. Keputusan yang sudah disepakati

| Kebutuhan | Keputusan |
|---|---|
| Infrastruktur awal | Satu server khusus, banyak kamera |
| Sumber kamera awal | RTSP untuk 5 kamera workshop dan 3 kamera warehouse; identitas serta resolusi tiap kamera belum diberikan |
| Label kamera sementara | WS-01 sampai WS-05: Workshop Bay 1–5; WH-01 sampai WH-03: Warehouse Gate 1–3. Ini label konfigurasi awal, bukan pemetaan fisik yang sudah diverifikasi. |
| Server awal | Tanpa GPU, RAM 32 GB; jenis CPU dan kapasitas inference belum diperiksa |
| Workshop | 5 kamera; zona digambar pada kamera |
| Syarat pekerjaan | Ban ada dalam zona dan orang berada cukup lama dalam zona |
| Zona tanpa ban | Tidak dihitung sebagai pekerjaan |
| Pengaturan waktu | Melalui node dan dapat berbeda antar-zona |
| Konfirmasi aktivitas | Waktu awal dapat ikut dihitung setelah konfirmasi lolos |
| Kondisi ban | Beragam, termasuk terlihat sebagian; perlu toleransi dan kalibrasi |
| Warehouse | 3 kamera; kejadian truk/ban keluar zona |
| Inventory | Sistem existing tetap menjadi sumber inventory |
| ERP | Endpoint sudah tersedia; kontrak teknis belum diperiksa |
| Dashboard | Mendukung tampilan banyak kamera |
| Ekspor | Workflow, paket kode/runtime, dan API hasil |
| TPMS | API tersedia; field dan kemampuan historis belum diperiksa |

## 3. Pengguna dan akses

| Peran | Tindakan |
|---|---|
| Admin | Mengelola proyek, kamera, model, integrasi, pengguna, dan retensi |
| Konfigurator | Menggambar zona, mengedit workflow, menguji, menerbitkan versi |
| Operator | Melihat kamera dan hasil, memeriksa gangguan, melakukan tindakan operasional sesuai izin |
| Supervisor | Membaca rekap, bukti, dan mengoreksi sesi dengan alasan |
| Aplikasi ERP | Menerima kejadian beserta screenshot |
| Aplikasi eksternal | Membaca hasil melalui API sesuai izin |

Perubahan konfigurasi, aktivasi, pengiriman ulang, dan koreksi data harus mencatat pelakunya. Kredensial kamera dan integrasi tidak ditampilkan pada log atau ekspor.

## 4. Lingkup rilis

### 4.1 Rilis operasional awal

- Proyek Workshop dan Warehouse.
- Registrasi 8 kamera dan beberapa zona per kamera.
- Zone Activity Timer, sesi workshop, dan rekap durasi.
- Deteksi keluar berarah, bukti screenshot, dan antrean ERP.
- Dashboard banyak kamera dan riwayat hasil.
- Draf, versi terbit, aktivasi, penghentian, dan pemulihan proses.
- Penyimpanan tahan restart, akses pengguna, log, backup, dan retensi.
- Pilot dengan rekaman serta kamera lapangan.

### 4.2 Rilis lanjutan

- Results API dan paket runtime/source yang diuji di lingkungan bersih.
- Road Inspection dan pencocokan dengan API TPMS.
- Android/offline atau perangkat edge dengan daftar kemampuan yang didukung.

### 4.3 Batas pengukuran

- Durasi workshop adalah estimasi aktivitas zona dari keberadaan objek; belum membuktikan tindakan mekanik secara langsung.
- Satu zona menghasilkan satu sesi area. Beberapa ban dalam zona belum menghasilkan durasi masing-masing ban.
- Pergantian ban tanpa zona pernah kosong bisa tetap menjadi satu sesi area.
- Waktu dua orang bekerja bersamaan tidak dijumlahkan menjadi jam-orang.
- Kejadian warehouse bukan transaksi saldo inventory. ERP menentukan tindakan bisnis lanjutannya.
- Ban yang tertutup muatan truk tidak diasumsikan dapat dideteksi.
- Ekspor model tidak otomatis mengekspor seluruh workflow ke Android/ESP.

## 5. Kondisi aplikasi saat penyusunan

Pemeriksaan sumber menemukan editor workflow, penyimpanan proyek, upload model, tracking, zona dwell, line counter, preview, log, dan webhook bergambar.

Kesenjangan utama:

- `server.py` menggunakan satu runner aktif; pengoperasian beberapa kamera memerlukan pengelolaan instance terpisah.
- Dwell Time menghitung berdasarkan track ID dan menghapus waktu saat track hilang; timer workshop memerlukan state zona.
- Pengiriman webhook memakai thread sementara dan belum menyediakan antrean permanen dengan riwayat hasil pengiriman.

Fitur existing akan digunakan ulang setelah pengujian pada alur baru. Keberadaan kode tidak dianggap sebagai bukti keberhasilan lapangan.

### Perkembangan implementasi — 14 Oktober 2026

Prioritas pengguna diperbarui: node custom lebih dahulu, kemudian fondasi operasional mengikuti dependensi. Dua node sudah ditambahkan ke katalog dan inspector: `zone_activity_timer` dan `zone_exit_event` (katalog saat ini 48 tipe). Tersedia template Workshop dan Warehouse yang meminta pemilihan model custom; template tidak mengasumsikan YOLO bawaan mengenali ban.

Runtime awal menyediakan status/durasi zona, sesi dalam memori, event perubahan status, dan event OUT dengan ID unik. Output event dilaksanakan sebelum antrean preview yang dapat membuang frame: Alert, Image Output, Webhook, dan Database Output existing. Screenshot berasal dari frame event; database menyimpan event JSON dalam tabel events existing. Pengiriman webhook memakai transport existing dan **belum** menjadi antrean ERP tahan restart.

Snapshot node tersedia di `/api/status` pada `projectNodes`; ini belum dashboard multi-kamera atau penyimpanan sesi historis permanen. Konfigurasi yang berubah saat workflow live menutup sesi sebelumnya dengan alasan `configuration_changed`, lalu memulai state baru; penerapan pada batas sesi melalui Publish belum tersedia.

Bukti awal: test durasi/exit sintetis, routing graph, validasi API, output gambar/database/webhook mock, pipeline video sintetis pada runner threaded dan serial, serta pemeriksaan inspector di browser. Kamera lapangan, model ban, pengiriman ERP nyata, replay beranotasi, dan kapasitas delapan kamera belum diverifikasi. Detail check dan outstanding ada di task list.

### Perkembangan editor zona — 15 Oktober 2026

Editor polygon pada preview untuk Dwell Time, Zone Activity Timer, dan Zone Exit Event sekarang membuka titik yang sudah tersimpan, mendukung tambah/geser/hapus titik, serta menyediakan Simpan dan Batal. Koordinat dihitung dari area gambar aktual saat preview memakai `object-fit: contain`; mengganti proyek atau menghapus node menutup editor. Tombol field `points` pada node zona memakai editor polygon yang sama. ROI Filter tetap memakai alat persegi yang sesuai dengan konfigurasi rectangle.

Konfigurasi dua node custom sekarang menolak polygon yang berpotongan sendiri, vertex berulang, dan sisi yang saling bertumpuk melalui API maupun jalur runner langsung. Polygon runtime yang rusak dengan kurang dari tiga titik tidak lagi dianggap mencakup seluruh frame. Validasi polygon ini belum mencakup editor garis dan geometri ROI Filter. Editor pada fullscreen/modal, pemetaan crop/rotasi kamera, identitas zona per kamera, serta pengujian pada preview kamera nyata tetap menjadi pekerjaan terpisah.

Pemeriksaan Playwright pada preview sintetis membuktikan tambah titik ke-5, geser tanpa menambah titik baru, hapus titik tanpa menghapus node, Batal tanpa mengubah konfigurasi, Simpan yang bertahan setelah reload, serta klik letterbox yang diabaikan. ResizeObserver memperbarui posisi overlay pada perubahan container; pemetaan ketika resolusi frame nyata berubah masih perlu diuji.

### Perkembangan timer dan status frame — 15 Oktober 2026

Zone Activity Timer memiliki `maxSessionDurationSeconds` opsional; `0` menonaktifkan batas sampai kalibrasi pilot. Saat batas usia sesi terlampaui pada observasi valid, node menandai sesi dan mengirim satu `zone_activity_event` dengan alasan `max_session_duration_exceeded`, tanpa memaksa sesi selesai. Jika ban sementara tidak terlihat, peringatan menunggu hasil toleransi kehilangan ban agar sesi yang kemudian ditutup mundur tidak salah ditandai. Flag tetap ada pada event penutupan dan kembali kosong pada sesi baru.

`/api/status` sekarang memproyeksikan sesi timer aktif sebagai `UNKNOWN` ketika usia frame terakhir melampaui `maxObservationGapSeconds`. Proyeksi ini hanya untuk pembacaan status: tidak mengubah interval tersimpan, tidak menerbitkan event, dan belum menjadi health multi-kamera. Frame valid berikutnya menghitung rentang tanpa observasi satu kali melalui runtime timer. Status layar, event kamera terputus secara mandiri, serta pemulihan restart masih perlu dikerjakan.

### Perkembangan pengikatan proyek dan model — 15 Oktober 2026

Satu runner yang tersedia sekarang dapat diikat ke ID proyek saat dijalankan. Menyimpan atau mengirim live update proyek lain tidak mengubah runner tersebut; editor menyembunyikan preview/log/indikator dari proyek lain. Endpoint lama tanpa ID proyek tetap tersedia untuk workflow mandiri. Ini pengamanan runner tunggal, belum manajemen delapan kamera atau isolasi deployment.

Upload model baru disimpan di direktori berdasarkan SHA-256 isi file. Nama file sama dengan isi berbeda menghasilkan dua berkas; upload ulang isi identik memakai berkas yang sama. Model lama di direktori utama tidak ditimpa. Daftar model menampilkan fingerprint untuk upload baru, sedangkan inspeksi menghitung checksum model lama saat diminta. Belum ada versi terbit, catatan penggunaan model, atau jejak model pada setiap hasil runtime.

Sebelum `/api/run`, node zona aktif memeriksa kelas yang dibutuhkan terhadap label yang dapat dibaca dari model detector/segmenter pada cabang masuknya. `customClasses` tidak menjadi bukti kemampuan model. Label yang tidak tersedia menyebabkan error konfigurasi; label metadata atau file pendamping tetap hanya deklarasi dan harus diuji pada rekaman beranotasi. Metadata `yolov8n.pt` yang tersedia berisi `person` dan `truck`, tetapi tidak berisi `tire`; model tersebut belum memenuhi kebutuhan workshop/warehouse berbasis ban. Validasi Publish/Activate menunggu fase H.

## 6. Struktur produk

| Halaman | Kebutuhan |
|---|---|
| Overview | Ringkasan kamera, zona aktif, sesi, kejadian, dan gangguan |
| Projects | Kamera, workflow, model, hasil, dan konfigurasi per proyek |
| Live Cameras | Grid 1/4/9, filter proyek, fullscreen, zona, dan status |
| Workflow Studio | Editor node, validasi, test, publish, dan pilihan versi |
| Workshop Sessions | Timeline, durasi, filter shift, bukti, dan koreksi |
| Warehouse Events | Kejadian keluar, screenshot, dan status ERP |
| Models | Upload, kelas sebenarnya, versi, pemeriksaan, dan penggunaan |
| Integrations | ERP dan selanjutnya TPMS |
| Logs & Health | Log dan gangguan per kamera/proses/integrasi |
| Settings | Akses pengguna, shift, retensi, penyimpanan, dan server |

## 7. Kamera dan zona

### CAM-01 — Registrasi kamera

Simpan ID tetap, nama, proyek, lokasi fisik, referensi kredensial, sumber stream, resolusi, frekuensi inference, dan workflow terbit yang digunakan. Status mencakup koneksi, frame terakhir, kesehatan inference, serta gangguan penyimpanan.

### ZONE-01 — Editor zona

- Gambar polygon pada frame kamera; beri ID, nama, dan warna.
- Tambah, pindah, dan hapus titik; simpan atau batalkan edit.
- Dukung beberapa zona dan garis berarah per kamera.
- Koordinat disimpan relatif terhadap gambar dan dipetakan ke gambar yang benar.
- Pan, zoom, resize, fullscreen, dan letterboxing tidak mengubah ketepatan pointer.
- Perubahan crop, rotasi, atau posisi kamera membutuhkan pemeriksaan zona.
- Tolak polygon/garis yang tidak valid.

### ZONE-02 — Aturan masuk zona

Orang dapat menggunakan titik bawah-tengah bounding box. Ban dapat memakai titik tengah atau rasio irisan dengan zona. Pilihan dan ambangnya dapat dikalibrasi. Overlay harus menunjukkan objek yang dianggap masuk.

Zona fisik yang dilihat beberapa kamera memiliki satu sumber perhitungan utama pada rilis awal. Penggabungan identitas lintas kamera belum termasuk.

## 8. Zone Activity Timer

### TIMER-01 — Pengaturan node

| Parameter | Fungsi | Nilai awal pilot |
|---|---|---|
| Zone | Referensi zona kamera | Wajib |
| Required class | Kelas ban pada model | Diverifikasi |
| Required minimum | Minimum ban | 1 |
| Trigger class | Kelas orang pada model | Diverifikasi |
| Trigger minimum | Minimum orang | 1 |
| Confirmation seconds | Lama kondisi sebelum bekerja | 10 detik |
| Count from confirmation start | Sertakan interval konfirmasi setelah lolos | Aktif |
| Person absence grace | Toleransi kehilangan orang | 3 detik |
| Tire absence grace | Toleransi kehilangan ban | 15 detik |
| Maximum observation gap | Jeda antar-frame sebelum pengamatan dianggap terputus | 5 detik |
| Maximum session duration | Tandai sesi terlalu panjang tanpa menutupnya | 0 (nonaktif; kalibrasi saat pilot) |
| Overlay/evidence | Status, timer, dan screenshot perubahan | Dapat dipilih |

Nilai awal adalah usulan yang bisa diubah per zona, bukan angka penerimaan final. Toleransi hanya berlaku pada frame valid; stream putus masuk status pengamatan terputus.

Saat tidak ada frame, pembacaan `/api/status` menampilkan proyeksi `UNKNOWN` setelah ambang gap; perubahan interval tersimpan dan event baru dipastikan ketika observasi berikutnya tiba. Grace diukur dari observasi positif terakhir; waktu selama kehilangan sementara tampil sebagai menunggu dan dapat dikoreksi menjadi bekerja jika objek kembali dalam grace. Durasi tersebut belum keputusan final sebelum grace terselesaikan.

Nama config runtime: `zoneName`, `points`, `requiredClasses`, `requiredCount`, `triggerClasses`, `triggerCount`, `confirmationSeconds`, `countFromStart`, `personGraceSeconds`, `requiredGraceSeconds`, `maxObservationGapSeconds`, `maxSessionDurationSeconds`, `showOverlay`. Pilihan bukti otomatis per transisi belum diimplementasikan pada node awal.

### TIMER-02 — State dan interval

| State | Kondisi | Efek |
|---|---|---|
| EMPTY | Ban dipastikan tidak ada | Tidak ada sesi aktif |
| WAITING | Ban ada, orang belum memenuhi syarat | Sesi aktif; waktu menunggu |
| CONFIRMING | Kondisi pemicu ada, belum mencapai ambang | Interval sementara |
| WORKING | Kondisi lolos konfirmasi | Waktu bekerja |
| PAUSED | Orang dipastikan pergi; ban masih ada | Waktu jeda/menunggu |
| UNKNOWN | Kamera atau pengamatan tidak valid | Waktu tidak diketahui |
| COMPLETED | Ban dipastikan keluar | Sesi ditutup |

- Sesi dimulai dari keberadaan ban yang valid, bukan kedatangan orang.
- Konfirmasi singkat yang gagal tidak menjadi waktu bekerja.
- Bila konfirmasi lolos dan backdating aktif, interval bekerja dimulai pada awal konfirmasi valid.
- Minimum orang dihitung pada zona; pergantian orang tidak mengulang timer jika syarat tetap terpenuhi.
- Kehilangan singkat dalam toleransi dapat dijembatani. Jika toleransi habis, batas interval kembali ke pengamatan valid terakhir.
- Interval bekerja, menunggu, dan tidak diketahui tidak boleh tumpang tindih atau dihitung dua kali.
- Tracking ID membantu pengamatan tetapi bukan kunci permanen sesi zona.
- Durasi memakai clock monotonik selama proses hidup, bukan jumlah frame; timestamp kejadian memakai waktu UTC dengan tampilan zona waktu proyek.
- Setelah restart, state diselesaikan sebagai terputus atau dipulihkan dengan batas pengamatan yang eksplisit. Downtime tidak menjadi waktu bekerja.
- Pergantian shift membagi agregasi waktu tanpa menggandakan sesi.

### TIMER-03 — Contoh penerimaan

Ban ada pukul 08.00.00, orang masuk 08.02.00, konfirmasi lolos 08.02.10. Dengan backdating aktif, bekerja dimulai 08.02.00. Orang terakhir terlihat 08.12.00 dan toleransi habis 08.12.03: interval ditutup 08.12.00. Jika ban masih ada, sesi masuk PAUSED.

## 9. Warehouse dan ERP

### WH-01 — Pemicu keluar

Gunakan perlintasan garis berarah atau transisi dalam-ke-luar zona. Objek pertama kali terdeteksi di luar tidak otomatis dianggap keluar. Tetapkan debounce, rearm setelah masuk kembali, dan aturan penggabungan deteksi saat kalibrasi. Cooldown waktu saja tidak cukup untuk menjelaskan satu kejadian fisik.

Node awal `zone_exit_event` menggunakan transisi polygon dan `trackId`. Config: `zoneName`, `points`, `classes`, `absenceGraceSeconds` (konfirmasi observasi luar, default 2 detik), `maxObservationGapSeconds` (default 5 detik), `showOverlay`. Objek harus terlihat di luar secara berkesinambungan; kehilangan pengamatan memutus konfirmasi. Track yang hilang tidak dianggap keluar. Perubahan ID saat perlintasan dapat membuat event terlewat dan harus diukur pada pilot; reidentifikasi lintas ID belum tersedia.

Event runtime: `zone_activity` untuk snapshot kontinu, `zone_activity_event` untuk perubahan status, dan `zone_exit` untuk kejadian keluar. Event sparse membawa `sourceNodeId`, `eventId`, `observedAt` UTC, dan metadata zona; event keluar juga membawa track, kelas, bbox, serta arah OUT. Snapshot/event tidak dijumlahkan sebagai objek pada occupancy preview. Output action downstream menerima event sparse, bukan snapshot kontinu atau seluruh stream deteksi.

### WH-02 — Bukti

Screenshot harus berasal dari frame pemicu. Simpan gambar, waktu frame, kamera, zona, objek, arah, versi workflow/model, serta ID kejadian. Overlay bukti boleh menampilkan batas dan kotak deteksi. Gagal menyimpan bukti terlihat sebagai kegagalan, tidak diam-diam dianggap lengkap.

### ERP-01 — Kontrak

Format request, gambar, autentikasi, timeout, batas ukuran, respons sukses, dan dukungan deduplikasi mengikuti endpoint ERP setelah diperiksa. Jangan mengasumsikan format baru sudah didukung.

### ERP-02 — Antrean permanen

- Simpan kejadian, referensi bukti, dan tugas pengiriman sebelum mengirim.
- Gunakan ID kejadian sama pada seluruh percobaan.
- State: PENDING, SENDING, RETRY_WAIT, DELIVERED, ACTION_REQUIRED.
- Catat jumlah percobaan, waktu berikutnya, hasil HTTP, dan referensi ERP tanpa membocorkan kredensial.
- Retry gangguan jaringan/server dengan jeda dan batas yang dapat diatur.
- Kesalahan autentikasi/format memerlukan tindakan, bukan retry tanpa akhir.
- Setelah restart, tugas SENDING yang belum pasti direkonsiliasi atau diulang dengan ID sama.
- Screenshot belum terkirim tidak dihapus oleh retensi biasa.
- Pengiriman adalah at-least-once; hasil bisnis tanpa duplikasi memerlukan dukungan idempotensi/reconciliation ERP.
- Pengiriman ulang manual harus diaudit.

## 10. Dashboard dan laporan

### DASH-01 — Banyak kamera

Grid 1/4/9, filter proyek, fullscreen, overlay, status kamera, waktu frame terakhir, dan navigasi ke sesi/kejadian. Preview grid dapat memiliki resolusi/FPS lebih rendah dari inference. Membuka banyak browser tidak membuat instance inference baru.

### DASH-02 — Workshop

Tampilkan status zona, timer berjalan, total bekerja, menunggu, tidak diketahui, riwayat sesi, timeline, dan rekap shift/hari. Rasio aktivitas menggunakan waktu pengamatan valid dengan denominator terlihat; bukan klaim produktivitas tenaga kerja.

Koreksi manual menyimpan nilai asli, nilai koreksi, alasan, pengguna, dan waktu. Sesi terlalu panjang, stream terputus, atau bukti tidak lengkap dapat ditandai perlu pemeriksaan.

### DASH-03 — Warehouse

Tampilkan kejadian, screenshot, sumber, waktu, arah, dan status pengiriman. Filter kamera/zona/tanggal/status; tampilkan alasan gagal dan tindakan yang diizinkan.

## 11. Workflow dan runtime

### RUN-01 — Versi operasional

Save Draft tidak mengubah workflow aktif. Test menggunakan mode aman tanpa pengiriman ERP secara default. Publish menghasilkan versi tetap yang mencatat model dan zona. Aktivasi menunjuk versi tertentu; rollback menunjuk versi sebelumnya.

Perubahan aturan timer berlaku pada batas sesi. Penerapan segera harus menutup sesi dengan alasan perubahan konfigurasi, bukan mencampur dua rumus dalam satu sesi.

### RUN-02 — Banyak kamera

Pengelola runtime menyimpan instance per kamera/deployment. Preview, state zona, log, dan hasil dipisahkan dengan ID. Stop satu deployment tidak menghentikan kamera lain. Kondisi diinginkan ACTIVE dipisahkan dari kondisi aktual RUNNING/RECONNECTING/FAILED/STOPPED.

Proses tidak bergantung pada tab browser. Restart, reconnect, dan pemulihan memakai jeda; tidak membuat restart loop tanpa batas. Perubahan model dan concurrency harus diuji terhadap penggunaan RAM/VRAM.

## 12. Model dan kontrak antar-node

Model registry menyimpan ID, versi, checksum, format, tugas, kelas sebenarnya, pemeriksaan, dan penggunaan. Model aktif tidak ditimpa upload baru. Workflow tidak boleh aktif bila kelas wajib atau file model tidak tersedia.

Kualitas deteksi ban diuji dari sudut kamera nyata. Mengganti label kelas tidak menambah kemampuan model. Pelatihan model menjadi pekerjaan kondisional jika model yang tersedia tidak memenuhi kebutuhan.

Packet gambar, deteksi objek, dan kejadian memiliki kontrak terpisah. Semua keluaran membawa konteks proyek, kamera, frame/waktu, dan versi deployment. Model/workflow terbit dapat ditelusuri dari hasil.

## 13. Data, penyimpanan, dan operasi

Entitas utama: projects, cameras, zone_versions, workflow_versions, deployments, model_versions, workshop_sessions, session_intervals, events, evidence, delivery_jobs, dan audit_entries. Daftar ini model konseptual, bukan kewajiban satu tabel per entitas.

Database lokal dengan penulis terkontrol dan file gambar menjadi kandidat awal satu server; benchmark menentukan kecukupannya. Jangan menambah layanan database/queue terpisah tanpa kebutuhan terukur.

- Penyimpanan kejadian dan antrean harus konsisten saat proses gagal.
- File bukti ditulis secara aman dan punya status bila belum lengkap.
- Catat kesehatan disk, proses, frame terakhir, queue, dan kegagalan inference.
- Retensi screenshot dapat berbeda dari ringkasan durasi; perlindungan bukti pending ERP wajib ada.
- Backup mencakup database, konfigurasi, dan bukti yang diperlukan; lakukan uji restore.
- Akses API dan gambar harus mengikuti izin pengguna; stream URL/token tidak bocor melalui payload.
- Konfigurasi shift mendukung lintas tengah malam. Penyimpanan waktu UTC, tampilan awal Asia/Makassar.

## 14. API dan ekspor

API hasil menyediakan kamera/status, zona, sesi, interval, kejadian, ringkasan, dan bukti dengan autentikasi, filter, pagination, serta versi kontrak.

Ekspor workflow mencakup graph, aturan, zona, dan referensi model. Paket source/runtime mencakup runner, konfigurasi, versi dependensi, contoh environment, instruksi, dan manifest. Model disertakan hanya jika distribusinya diizinkan; alternatifnya referensi/checksum. Rahasia tidak ikut ekspor.

Paket harus berhasil dijalankan di lingkungan bersih dengan hasil uji yang dapat dibandingkan. Android/edge memiliki target perangkat, runtime, preprocessing/postprocessing, dan matriks node tersendiri.

## 15. Road Inspection dan TPMS

Tahap berikutnya: unit ID, temuan jalan rusak, timestamp, bukti, lokasi bila tersedia, buffer offline, sinkronisasi, deduplikasi observasi berulang, serta pencocokan API TPMS. Periksa dahulu field API, sumber GPS, timestamp, history, dan rate limit. Kedekatan waktu tidak dianggap bukti sebab-akibat kerusakan ban.

## 16. Kriteria penerimaan

| Area | Bukti wajib |
|---|---|
| Timer | Replay beranotasi memverifikasi transisi, backdating, toleransi, dan durasi |
| Zona | Pointer/overlay tepat saat pan, zoom, resize, dan fullscreen |
| Isolasi | Stop/failure satu kamera tidak mencampur atau menghentikan kamera lain |
| Warehouse | Masuk/keluar/rearm menghasilkan kejadian sesuai anotasi, tanpa spam per frame |
| ERP | Bukti diterima endpoint nyata; timeout/retry/restart diuji dengan ID sama |
| Restart | Downtime tidak menambah bekerja; tugas kirim tetap tersedia |
| Dashboard | 8 kamera terdaftar; state, preview, dan hasil tidak tertukar |
| Kapasitas | Laporan FPS, latency, RAM/VRAM, reconnect, dan queue pada server target |
| Akses | Tindakan konfigurasi dan bukti mengikuti izin; rahasia tidak muncul di ekspor/log |
| Backup | Restore data, konfigurasi, dan bukti berhasil |

Sebelum pilot, sepakati batas kesalahan durasi, precision/recall kejadian, latency alert, lama soak test, dan target kapasitas. Nilai ini belum disepakati dan tidak boleh dinyatakan lulus sebelum tersedia.

## 17. Dependensi dan keputusan terbuka

- Spesifikasi server/GPU, resolusi, sumber stream, serta akses 8 kamera.
- Nama area, zona fisik, overlap antarkamera, dan rekaman contoh.
- Kelas dan kualitas model ban/person/truck pada kondisi nyata.
- Ambang waktu final, shift, retensi, serta batas sesi perlu pemeriksaan.
- Kontrak ERP, autentikasi, ukuran gambar, respons, dan dukungan idempotensi.
- Metode login/akses operasional dan pihak yang boleh mengaktifkan workflow.
- Contoh API TPMS serta perangkat Android/ESP untuk fase berikutnya.

## 18. Urutan peluncuran

Satu kamera workshop terbukti benar → lima kamera workshop → satu kamera warehouse dan ERP → tiga kamera warehouse → pilot delapan kamera → API/ekspor → Road Inspection/edge.

Setiap tahap memiliki bukti terpisah untuk logika otomatis, replay rekaman, integrasi, dan operasi langsung. Kelulusan pemeriksaan sumber atau unit test tidak menggantikan bukti operasional.
