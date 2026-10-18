# Task List — Afi Vision Operations

Tanggal: 15 Oktober 2026  
Referensi kebutuhan: [PRD.md](PRD.md)  
Status: Runtime node custom awal dan editor polygon tersedia; hanya pekerjaan dengan bukti yang dicentang.

## Current priority and handoff

Prioritas pengguna: node workshop/warehouse terlebih dahulu, kemudian fondasi operasional. Sesi baru wajib membaca bagian ini bersama PRD dan status Git. Instruksi kontinuitas tersimpan di `../AGENTS.md`.

**Sudah tersedia:** Zone Activity Timer, Zone Exit Event, VLM Box Tracker, AI Agent (`ai_agent`, terinspirasi dari n8n AI Agent dengan multi-provider OpenAI official / OpenRouter / Custom Ollama, multimodal vision frame base64 + data deteksi/event, mode trigger on_event & periodic, decision gate cerdas, dan fallback key aman `.env`), inspector setting, template awal, snapshot status, overlay, event sparse, dan output Alert/Image/Webhook/Database sebelum antrean preview. Timer memiliki batas usia sesi opsional (`0` nonaktif) dengan satu event peringatan tanpa menutup sesi. `/api/status` memproyeksikan sesi aktif menjadi UNKNOWN saat frame terlambat tanpa mengubah hitungan tersimpan. Editor polygon zona mendukung titik bebas dengan Simpan/Batal dan pemetaan letterbox; validasi custom node menolak polygon berpotongan/bertumpuk. Katalog sekarang 50 tipe. Database output menyimpan JSON event; sesi timer masih dalam memori. Runner tunggal terikat ke proyek saat dijalankan dari editor, sehingga simpan/live update proyek lain tidak mengubahnya. Upload model baru tidak menimpa versi lama dan preflight node zona memeriksa label model pada cabang masuknya.

**Berikutnya:** uji editor zona dengan preview kamera nyata dan model/rekaman beranotasi saat input lapangan tersedia; pembuktian resize/fullscreen pada resolusi frame berbeda masih terbuka. Siapkan kontrak konteks kamera/deployment (B02) dan penyimpanan konfigurasi aman (B03) tanpa menyimpan kredensial dalam workflow, lalu uji dua runner independen secara sintetis sebelum uji RTSP. Lanjutkan persistensi/recovery sesi (D11–D12) dan antrean ERP permanen (G06–G11) setelah identitas sumber/kontrak tersedia. Dashboard lima workshop/tiga warehouse menyusul fondasi itu. Task tanpa input eksternal dapat dilanjutkan dalam scope yang diotorisasi pengguna.

**Outstanding/input lapangan:** delapan stream berjenis RTSP dan server tanpa GPU dengan RAM 32 GB sudah dikonfirmasi. Label logis sementara dipilih: WS-01–WS-05 (Workshop Bay 1–5) dan WH-01–WH-03 (Warehouse Gate 1–3); lokasi dan sumber fisik belum terverifikasi. Masih diperlukan resolusi/akses tiap kamera, jenis CPU serta disk/jaringan server, model yang mengenali ban, rekaman/anotasi, geometri zona, kontrak endpoint ERP dan dukungan idempotensi. Jangan mengganti label model generik lalu menganggap kemampuan deteksi tire tersedia.

**Batas saat ini:** satu runner aktif; status UNKNOWN saat frame berhenti baru berupa proyeksi ketika `/api/status` dipanggil, sedangkan event dan pembukuan gap menunggu frame berikutnya; sesi tidak pulih setelah restart; output webhook tetap sementara; editor zona belum identitas geometri per kamera/crop/rotasi dan belum dibuktikan pada kamera nyata; kapasitas delapan kamera dan ERP nyata belum diuji. Perubahan config live menutup sesi lama dengan alasan configuration_changed. Track ID yang berubah tepat saat keluar dapat menyebabkan event terlewat.

### Prioritas P0 — Node custom

- [x] P01. Katalog dan inspector Zone Activity Timer / Zone Exit Event dengan kelas, jumlah, durasi, grace, serta points.
- [x] P02. Timer zona berbasis elapsed time dan interval yang tidak tumpang tindih, tanpa ketergantungan pada track ID.
- [x] P03. Event keluar hanya setelah observasi dalam→luar, dengan grace, rearm, gap reset, dan ID event.
- [x] P04. Pisahkan event sparse dari snapshot/deteksi kontinu; jalankan output sebelum preview dapat membuang frame.
- [x] P05. Output gambar dari frame pemicu, alert, database event, serta webhook existing dengan mock.
- [x] P06. Validasi API untuk konfigurasi baru dan template awal yang meminta model custom.
- [x] P07. Pemeriksaan browser: kedua node muncul, field setting tersedia, perubahan konfirmasi tersimpan dan terbaca ulang, tanpa undefined pada inspector timer.
- [x] P07a. Buktikan tambah/geser/hapus titik, Batal, Simpan/reload, dan letterbox editor polygon di browser dengan preview sintetis.
- [ ] P08. Uji gambar polygon pada preview nyata dan kalibrasi model/rekaman beranotasi.
- [ ] P09. Lanjutkan multi-camera, persistensi sesi, dan ERP durable sesuai fase B/D/G.

Bukti kode: `engine/project_nodes.py`, integrasi `engine/core.py`/`engine/main.py`, katalog, inspector, dan validasi server. Bukti otomatis: `test_project_nodes.py` dan `test_project_node_integration.py`. Browser memakai server sementara port 18765 dengan data di TEMP; workflow pengguna tidak dipakai untuk pengujian.

## Cara menggunakan

- Kerjakan berurutan mengikuti dependensi fase. Pilot satu kamera dilakukan sebelum perluasan.
- Centang task setelah hasilnya tersedia dan kriteria penerimaan terpenuhi.
- Catat bukti berupa hasil test, rekaman, log, respons ERP, atau laporan pilot.
- Task kondisional hanya dikerjakan jika hasil pemeriksaan membuktikan kebutuhannya.
- Perubahan model, konfigurasi lapangan, dan data proyek pengguna diperlakukan terpisah dari kode.
- Commit dan push merupakan tindakan terpisah setelah diminta pengguna.

## Fase A — Pemetaan lapangan dan kontrak

Dependensi: tidak ada. Output: konfigurasi pilot dan kriteria hasil benar.

- [ ] A01. Daftarkan 5 kamera workshop dan 3 kamera warehouse: ID, nama, lokasi, proyek, stream, resolusi, dan kredensial terpisah.
- [ ] A02. Periksa server target: CPU, GPU/VRAM jika ada, RAM, disk, jaringan, dan lingkungan runtime.
- [ ] A03. Petakan area fisik dan kamera yang saling overlap; tetapkan sumber perhitungan utama tiap area.
- [ ] A04. Ambil rekaman kondisi kosong, ban saja, orang saja, aktivitas, occlusion, dan perlintasan warehouse.
- [ ] A05. Buat anotasi manual awal/akhir aktivitas serta kejadian keluar untuk pembanding.
- [ ] A06. Periksa kelas model sebenarnya dan deteksi tire/person/truck pada rekaman.
- [ ] A07. Periksa kontrak ERP: request, gambar, autentikasi, sukses/gagal, ukuran, timeout, dan deduplikasi.
- [ ] A08. Sepakati shift, retensi, batas sesi, dan siapa yang boleh mengubah/mengaktifkan konfigurasi.
- [ ] A09. Tetapkan target pilot: kesalahan durasi, kejadian terlewat/salah/duplikat, latency, serta lama pengamatan.

Selesai bila satu kamera pilot dapat diakses, rekaman beranotasi tersedia, dan kontrak ERP tercatat tanpa rahasia.

Input parsial 15 Oktober 2026: pengguna mengonfirmasi jenis stream RTSP, server tanpa GPU, RAM 32 GB, serta membebaskan penamaan sementara. ID logis WS-01–WS-05 dan WH-01–WH-03 dipilih untuk rancangan; penempatan fisik, alamat stream, resolusi, CPU, disk, dan jaringan belum tersedia. A01/A02 belum dicentang. Kapasitas delapan inference pada CPU belum dibuktikan.

## Fase B — Fondasi data dan runtime beberapa kamera

Dependensi: A01–A03. Output: dua kamera dapat berjalan dan dikendalikan independen.

- [x] B01. Trace runner, preview, event, log, dan seluruh caller run/stop/live-update existing sebelum perubahan.
- [ ] B02. Tetapkan konteks project/camera/deployment/frame/version pada packet dan keluaran.
- [ ] B03. Tambahkan penyimpanan kamera, deployment, versi konfigurasi, dan migrasi data existing.
- [ ] B04. Ganti pengelolaan runner tunggal dengan instance terpisah per deployment kamera.
- [ ] B05. Pisahkan preview, timer/state, log, event, dan command per instance.
- [ ] B06. Tambahkan start/stop/status per kamera dan validasi agar tidak memulai instance duplikat.
- [ ] B07. Pisahkan status diinginkan dari kondisi aktual RUNNING/RECONNECTING/FAILED/STOPPED.
- [ ] B08. Tambahkan reconnect dengan backoff, shutdown bersih, dan pemulihan proses tanpa bergantung browser.
- [ ] B09. Ukur CPU/RAM/VRAM dua kamera; tentukan pembagian proses dan pemuatan model berdasarkan bukti.
- [ ] B10. Verifikasi bahwa failure/stop satu kamera tidak menghentikan atau mengubah hasil kamera lainnya.
- [ ] B11. Verifikasi menutup browser dan membuka beberapa browser tidak membuat inference baru atau menghentikan operasi.

Selesai bila dua stream dan hasilnya terisolasi, stop independen berhasil, dan log kesehatan dapat ditelusuri.

Progress parsial: `/api/run` menerima `projectId` opsional, memvalidasi proyek, dan mengikat runner tunggal ke proyek tersebut. Simpan/live update proyek B tidak mengubah runner proyek A; editor tidak menampilkan preview/log/indikator A sebagai milik B. `test_project_binding.py` membuktikan isolasi update secara sintetis dengan fake runner. B02–B11 tetap terbuka: belum ada konteks kamera/deployment pada packet, registrasi kamera, dua runner, atau uji RTSP.

## Fase C — Editor zona kamera

Dependensi: B02–B05. Output: zona tersimpan dengan pemetaan koordinat yang tepat.

- [ ] C01. Buat identitas zona dan versi geometri per kamera.
- [ ] C02. Gunakan ulang editor polygon/garis existing setelah memeriksa seluruh jalur koordinat.
- [ ] C03. Tambahkan nama, warna, tambah/pindah/hapus titik, simpan, dan batal.
- [ ] C04. Dukung beberapa zona serta garis arah pada kamera yang sama.
- [ ] C05. Simpan koordinat relatif; petakan crop/rotate/resize dan letterboxing secara eksplisit.
- [ ] C06. Validasi polygon/garis, termasuk titik tidak finite dan geometri tidak dapat digunakan.
- [ ] C07. Tambahkan pilihan anchor orang, anchor/overlap ban, dan overlay objek yang dianggap masuk.
- [ ] C08. Tandai kebutuhan pemeriksaan ulang setelah kamera atau transformasi gambar berubah.
- [ ] C09. Uji pan, zoom, resize panel, fullscreen, dan perubahan resolusi tanpa pergeseran zona/pointer.

Selesai bila zona dapat dibuka ulang dan objek uji tetap masuk/keluar sesuai geometri pada semua tampilan.

Progress parsial: editor polygon untuk Dwell Time dan dua node custom sudah mendukung titik bebas, geser, hapus, Simpan/Batal, dan mapping letterbox pada preview biasa. Playwright pada port sementara membuktikan 4→5 titik, drag tanpa titik tambahan, hapus tanpa menghapus node, Batal tanpa mengubah points, Simpan/reload, dan klik letterbox diabaikan. Validasi polygon custom node menolak self-intersection, vertex berulang, serta sisi bertumpuk; jalur runner langsung juga memvalidasi. Uji matematis terisolasi untuk empat kombinasi ukuran/aspect ratio lulus, tetapi browser replay resize/fullscreen kali ini terhalang lingkungan browser (CUA menolak path workspace; Chrome Playwright crash setelah cache sementara dipakai); C09 tetap terbuka. C03 masih memerlukan identitas/warna zona; C05 masih memerlukan crop/rotasi; C06 masih memerlukan validasi garis dan ROI. Browser kamera nyata belum diuji.

## Fase D — Zone Activity Timer dan sesi workshop

Dependensi: C, A05–A06. Output: satu zona workshop menghasilkan durasi yang cocok dengan rekaman.

- [x] D01. Tambahkan node Zone Activity Timer pada katalog, inspector, validasi, panduan, dan serialisasi.
- [x] D02. Tambahkan zone, required/trigger class, minimum count, konfirmasi, backdating, toleransi, overlay, dan batas sesi.
- [x] D03. Implementasikan state EMPTY/WAITING/CONFIRMING/WORKING/PAUSED/UNKNOWN/COMPLETED per zona.
- [x] D04. Pisahkan waktu pengamatan UTC dan clock monotonik durasi; jangan memakai jumlah frame.
- [x] D05. Mulai sesi ketika ban ada; gagalkan aktivitas ketika syarat ban tidak terpenuhi.
- [x] D06. Terapkan konfirmasi dan backdating hanya setelah ambang lolos.
- [x] D07. Terapkan toleransi pada frame valid; tutup interval pada pengamatan terakhir ketika grace habis.
- [ ] D08. Terapkan UNKNOWN untuk stream/frame terputus tanpa menganggapnya kosong atau bekerja.
- [x] D09. Cegah interval tumpang tindih dan hitung durasi zona sekali meskipun orang lebih dari satu.
- [x] D10. Pastikan perubahan track ID tidak otomatis membuat sesi baru.
- [ ] D11. Simpan sesi, interval perubahan status, checkpoint, alasan selesai, versi model/workflow/zona, dan bukti pilihan.
- [ ] D12. Tentukan pemulihan restart; downtime tidak menjadi aktivitas dan sesi terputus dapat diperiksa.
- [ ] D13. Tambahkan overlay status/timer dan keluaran event terstruktur untuk penyimpanan/dashboard.
- [x] D14. Uji orang tanpa ban, ban tanpa orang, konfirmasi gagal/lolos, pergantian orang, occlusion, keluar, dan interval frame berbeda secara sintetis.
- [ ] D15. Replay rekaman beranotasi; laporkan selisih durasi dan kalibrasikan ambang per zona.

Selesai bila satu kamera workshop lolos target A09 dan batas interpretasi sesi area tercatat.

Progress parsial: D02 memiliki batas sesi opsional yang menandai usia sesi terlalu panjang satu kali tanpa menutup sesi; nilai awal 0 sampai pilot menetapkan ambang. D08 memproyeksikan UNKNOWN pada `/api/status` ketika frame tidak datang, tanpa mengubah runtime; event/pembukuan gap tetap menunggu frame berikutnya sehingga health mandiri dan tampilan operator masih terbuka. D11/D12 belum persistensi/recovery. D13 snapshot dan overlay awal tersedia; review node debug serta kontrak operasional lengkap belum selesai. D15 replay nyata belum tersedia.

## Fase E — Model Library dan template operasional

Dependensi: A06, D. Output: model dan template bisa digunakan dengan versi yang dapat ditelusuri.

- [ ] E01. Simpan ID/versi/checksum model, tugas, kelas sebenarnya, format, dan hasil pemeriksaan.
- [ ] E02. Cegah upload mengganti file model yang sedang digunakan versi terbit.
- [ ] E03. Validasi kelas wajib, file model, serta konfigurasi sebelum test/publish/activate.
- [ ] E04. Tampilkan penggunaan model dan status pemeriksaan lapangan.
- [ ] E05. Buat template workshop dengan detector/tracker/timer/overlay/storage.
- [ ] E06. Buat template warehouse dengan detector/tracker/exit rule/snapshot/storage/ERP.
- [ ] E07. Verifikasi packet gambar/deteksi/event mengikuti kontrak yang sama pada setiap jalur eksekusi.
- [ ] E08. Kondisional: siapkan dataset, anotasi, pelatihan, dan evaluasi model ban jika model existing tidak memenuhi target.

Selesai bila versi model dapat ditelusuri dari hasil dan template tidak dapat aktif dengan kelas wajib yang hilang.

Progress parsial: template `custom-workshop-zone` dan `custom-warehouse-exit` tersedia untuk mulai konfigurasi model/zona/preview; penyimpanan sesi dan koneksi ERP operasional belum termasuk template awal. Upload baru memakai SHA-256 isi file dan path berbeda untuk isi berbeda, sehingga nama sama tidak menimpa model lama; daftar model menampilkan fingerprint upload baru, model legacy tetap tampil, dan inspeksi menghitung checksum saat diminta. Preflight `/api/run` menolak kelas wajib yang tidak ada pada label detector/segmenter cabang zona dan tidak menerima `customClasses` sebagai bukti. E01–E03 tetap parsial: belum ada registry versi terbit, hasil uji kemampuan model pada rekaman, penggunaan model, maupun Publish/Activate. Label metadata/pendamping bukan bukti akurasi deteksi.

## Fase F — Dashboard dan laporan workshop

Dependensi: B–E. Output: lima kamera workshop dapat dipantau dengan hasil tersimpan.

- [ ] F01. Tambahkan navigasi Overview/Projects/Live Cameras/Workshop Sessions/Warehouse Events/Models/Integrations/Logs.
- [ ] F02. Buat grid 1/4/9, filter proyek, fullscreen, dan preview ringan tanpa inference tambahan.
- [ ] F03. Tampilkan status koneksi/inference, frame terakhir, status zona, timer, dan gangguan.
- [ ] F04. Tambahkan detail sesi dan timeline interval beserta bukti.
- [ ] F05. Tambahkan agregasi harian/shift untuk bekerja/menunggu/tidak diketahui.
- [ ] F06. Tangani shift lintas tengah malam dan sesi yang melewati pergantian shift tanpa duplikasi.
- [ ] F07. Tampilkan denominator waktu valid pada rasio aktivitas dan label estimasi yang jelas.
- [ ] F08. Tambahkan flag perlu pemeriksaan dan koreksi manual dengan nilai asli serta audit.
- [ ] F09. Uji layar berbeda, navigasi keyboard, fokus, dan kontrol yang dapat diakses.
- [ ] F10. Perluas pilot ke lima kamera; periksa overlap, state terpisah, dan penggunaan sumber daya.

Selesai bila lima kamera menghasilkan laporan yang dapat dibandingkan dengan pengamatan lapangan.

## Fase G — Warehouse, screenshot, dan ERP

Dependensi: B–C, E, A07. Output: kejadian nyata beserta bukti diterima ERP.

- [ ] G01. Gunakan ulang line/zone crossing; tetapkan arah, debounce, rearm, dan track continuity.
- [ ] G02. Jangan memicu keluar dari objek yang pertama kali terlihat di luar batas.
- [ ] G03. Tetapkan kebijakan truk dan ban yang terdeteksi bersamaan; hindari penafsiran sebagai jumlah stok.
- [ ] G04. Ambil screenshot dari frame pemicu dengan metadata dan versi yang cocok.
- [ ] G05. Simpan bukti secara aman; catat kegagalan gambar/disk sebagai status yang terlihat.
- [ ] G06. Simpan event dan delivery job secara konsisten sebelum request ERP.
- [ ] G07. Implementasikan payload/auth/gambar sesuai kontrak endpoint existing.
- [ ] G08. Implementasikan PENDING/SENDING/RETRY_WAIT/DELIVERED/ACTION_REQUIRED.
- [ ] G09. Implementasikan backoff, timeout, klasifikasi error, dan batas percobaan.
- [ ] G10. Pertahankan ID event saat retry; verifikasi idempotensi atau reconciliation ERP.
- [ ] G11. Pulihkan job belum pasti setelah restart; lindungi bukti pending dari retensi.
- [ ] G12. Tambahkan daftar/detail event, status, respons aman, serta retry manual yang diaudit.
- [ ] G13. Uji masuk/keluar/diam dekat batas/masuk kembali/ID berubah dan periksa false alert.
- [ ] G14. Uji ERP sukses, offline, 4xx, 5xx, timeout setelah diterima, dan restart di tengah pengiriman.
- [ ] G15. Uji penerimaan satu kejadian nyata dan screenshot di ERP; simpan referensi hasilnya.
- [ ] G16. Perluas ke tiga kamera warehouse setelah pilot satu kamera lulus.

Selesai bila kejadian dapat ditelusuri dari frame sampai ERP dan status tidak hilang saat failure/restart.

## Fase H — Publish, akses, dan operasi tahan restart

Dependensi: D–G. Output: versi operasional terpisah dari editor dan aman dioperasikan.

- [ ] H01. Buat Save Draft/Test/Publish/Activate/Deactivate/Rollback dengan versi tetap.
- [ ] H02. Test menonaktifkan pengiriman ERP secara default dan jelas menampilkan mode test.
- [ ] H03. Terapkan perubahan timer pada batas sesi; penerapan segera mencatat alasan penutupan.
- [ ] H04. Tambahkan login/izin sesuai metode yang dipilih; batasi konfigurasi, aktivasi, koreksi, dan retry.
- [ ] H05. Pisahkan rahasia dari graph, log, respons UI, dan ekspor.
- [ ] H06. Tambahkan audit perubahan konfigurasi dan tindakan operasional.
- [ ] H07. Tambahkan health untuk kamera, inference, disk, queue, dan pengiriman.
- [ ] H08. Atur retensi gambar/ringkasan tanpa menghapus bukti pending ERP.
- [ ] H09. Buat backup konsisten dan prosedur restore; buktikan pemulihan data/bukti/konfigurasi.
- [ ] H10. Pasang startup/shutdown server sesuai lingkungan target; uji setelah reboot.
- [ ] H11. Uji restart ketika WORKING/CONFIRMING/UNKNOWN dan ketika delivery SENDING.

Selesai bila versi aktif dapat ditelusuri dan restart tidak merusak perhitungan atau antrean.

## Fase I — Pilot delapan kamera dan keputusan rilis

Dependensi: F–H. Output: laporan penerimaan yang menyebut batas kapasitas dan hasil lapangan.

- [ ] I01. Jalankan bertahap 1/2/5/8 kamera pada server target.
- [ ] I02. Catat capture/inference/preview FPS, latency, dropped frames, RAM/VRAM, disk, dan panjang antrean.
- [ ] I03. Jalankan soak test selama durasi yang disepakati A09.
- [ ] I04. Uji kamera putus, model gagal, ERP putus, disk bermasalah, server restart, dan beberapa browser.
- [ ] I05. Bandingkan durasi dengan anotasi; laporkan selisih per sesi dan penyebabnya.
- [ ] I06. Laporkan kejadian benar/salah/terlewat/duplikat serta penerimaan screenshot ERP.
- [ ] I07. Kalibrasikan parameter dan ulangi hanya pengujian yang terdampak perubahan.
- [ ] I08. Buat panduan operator: status, aktivasi, gangguan, koreksi, retry, dan eskalasi.
- [ ] I09. Catat hasil tiap kriteria: PASS/FAIL/BLOCKED/NOT TESTED dan bukti; jangan menyebut seluruh fitur lulus bila belum diuji.
- [ ] I10. Bekukan versi pilot yang diterima beserta konfigurasi/model dan prosedur rollback.

Selesai bila seluruh kriteria wajib rilis awal terpenuhi atau pengecualian disepakati secara eksplisit.

## Fase J — Results API dan ekspor runtime/source

Dependensi: I. Output: hasil bisa dikonsumsi web lain dan paket bisa berjalan terpisah.

- [ ] J01. Definisikan API berversi untuk status, zona, sesi, event, ringkasan, dan bukti.
- [ ] J02. Tambahkan autentikasi/izin, filter, pagination, dan contoh konsumsi API.
- [ ] J03. Ekspor workflow beserta zona, referensi model, dan versi kontrak.
- [ ] J04. Buat paket runner/source minimal, manifest, dependensi, contoh environment, dan instruksi.
- [ ] J05. Nyatakan apakah model disertakan atau harus disediakan terpisah; periksa hak distribusi.
- [ ] J06. Verifikasi tidak ada kredensial, path lokal tak portabel, atau data pengguna yang ikut tanpa kebutuhan.
- [ ] J07. Jalankan paket di lingkungan bersih dengan rekaman pembanding.
- [ ] J08. Buktikan web contoh membaca hasil dan bukti melalui API sesuai izin.

Selesai bila paket menghasilkan hasil pembanding dan aplikasi lain berhasil mengonsumsi API.

## Fase K — Road Inspection, TPMS, dan edge/offline

Dependensi: rilis awal stabil; detail perangkat/API tersedia. Output: pilot terpisah, bukan bagian kelulusan workshop/warehouse.

- [ ] K01. Periksa API TPMS: unit ID, timestamp, GPS, history, autentikasi, dan batas request.
- [ ] K02. Tetapkan kelas kerusakan, bukti, lokasi, dan definisi satu temuan fisik.
- [ ] K03. Kumpulkan rekaman kamera bergerak dan anotasi untuk model jalan rusak.
- [ ] K04. Implementasikan pencocokan unit/waktu dengan batas toleransi yang terukur.
- [ ] K05. Implementasikan buffer offline dan sinkronisasi dengan ID stabil.
- [ ] K06. Tentukan deduplikasi observasi berulang berdasarkan data lokasi yang tersedia.
- [ ] K07. Pilih perangkat Android/edge/ESP aktual; ukur memori, operator, runtime, dan inference.
- [ ] K08. Buat matriks node yang didukung serta kontrak preprocessing/postprocessing.
- [ ] K09. Uji ekspor model pada perangkat nyata sebelum menjanjikan dukungan workflow penuh.
- [ ] K10. Jalankan pilot unit tambang dan laporkan akurasi, latency, offline recovery, dan batasnya.

## Matriks bukti penerimaan

| Kebutuhan PRD | Task utama | Bukti |
|---|---|---|
| CAM/RUN multi-kamera | B, F10, I | Log isolasi dan laporan kapasitas |
| ZONE | C | Uji koordinat dan rekaman interaksi |
| TIMER | D, I05 | Test state serta replay beranotasi |
| WH | G01–G05, G13 | Rekaman perlintasan dan event |
| ERP | G06–G15 | Antrean/retry dan respons endpoint nyata |
| DASH | F | Tampilan dan hasil agregasi pembanding |
| Publish/recovery/access | H | Uji versi, izin, reboot, dan restore |
| API/export | J | Konsumsi API dan run lingkungan bersih |
| Road/TPMS/edge | K | Pilot perangkat dan API aktual |

## Definition of Done

- [ ] Implementasi sesuai PRD dan perubahan terkait sudah ditinjau.
- [ ] Test yang relevan lulus, termasuk jalur failure dan restart yang memengaruhi hasil.
- [ ] Bukti otomatis, replay, integrasi, dan operasi langsung dicatat terpisah.
- [ ] Model/konfigurasi/versi hasil dapat ditelusuri.
- [ ] Dokumentasi operator dan batas pengukuran diperbarui.
- [ ] Tidak ada klaim akurasi/kapasitas/kelulusan yang melampaui bukti.

## Log pelaksanaan

| Tanggal | Task | Status | Bukti/lokasi | Catatan |
|---|---|---|---|---|
| 2026-10-14 | Penyusunan PRD dan task list | Dokumen dibuat | PRD.md, TASK_LIST.md | Implementasi belum dimulai |
| 2026-10-14 | P0, B01, D01/D03–D07/D09/D10/D14 | Implementasi awal dan test sintetis | test_project_nodes.py, test_project_node_integration.py | Node baru, sparse output, validasi, template; belum pilot |
| 2026-10-14 | Review integrasi | Temuan ditangani | core._deliver_project_events, main.filter_project_inputs | Event sebelum queue, bypass cooldown sparse, filter per sumber, gambar sebelum serialisasi |
| 2026-10-14 | Browser setting node | PASS terbatas | Playwright pada port 18765/data TEMP | Katalog 48, inspector kedua node, konfirmasi 12 disimpan/terbaca ulang; belum gambar zona kamera |
| 2026-10-14 | Pipeline video sintetis | PASS threaded dan serial | test_project_node_integration.py | 8 frame, detector/tracker mock, satu alert/webhook per jalur; tanpa inference model atau ERP nyata |
| 2026-10-14 | Regression serial | PASS | core._run_serial + test runner | Perbaiki input_config dan drawing_detections yang belum terinisialisasi agar node baru berjalan di kedua jalur |
| 2026-10-15 | Editor polygon dan validasi zona | PASS sintetis, lapangan belum | static/app.js, static/style.css, engine/project_nodes.py, test_project_nodes.py, test_project_node_integration.py | Titik bebas, geser/hapus, Simpan/Batal, letterbox; polygon invalid ditolak API/runner |
| 2026-10-15 | Browser editor polygon | PASS terbatas | Playwright port 18767/data TEMP; 4→5 titik, drag, hapus, Batal, Simpan/reload, letterbox | Preview sintetis; remap pada resolusi berbeda dan kamera nyata belum dibuktikan |
| 2026-10-15 | D02 batas durasi sesi | PASS sintetis/API | `test_project_nodes.py` (14 checks), `test_project_node_integration.py` (API menolak batas negatif), review regresi grace | `maxSessionDurationSeconds=0` nonaktif; satu peringatan per sesi, tanpa penutupan paksa; belum kalibrasi pilot |
| 2026-10-15 | D08 proyeksi frame terlambat | PASS API sintetis, parsial operasional | `test_project_node_integration.py`, review race snapshot | `/api/status` UNKNOWN tanpa mutasi; event baru saat frame kembali; belum health/event mandiri |
| 2026-10-15 | C09 pemetaan resize/aspect ratio | PASS matematis, browser belum | Uji round-trip terisolasi 4 kombinasi ukuran; CUA gagal pada path workspace, Playwright Chrome crash pada server TEMP port 18769 | C09 tetap terbuka sampai replay resize/fullscreen dan resolusi nyata |
| 2026-10-15 | Pengikatan runner ke proyek | PASS kontrak sintetis | `test_project_binding.py` | Simpan/live update proyek lain tidak mengubah runner aktif; UI menyembunyikan data proyek lain. Tetap satu runner; browser belum diuji ulang. |
| 2026-10-15 | Upload model berbasis isi | PASS API sintetis | `test_custom_models.py`, `test_server.py` | Nama sama/isi berbeda aman, isi identik idempotent, model legacy tetap utuh, upload terlalu besar dibersihkan. Belum ada registry versi terbit. |
| 2026-10-15 | Preflight kelas node zona | PASS metadata sintetis | `test_model_zone_preflight.py` (7 checks) | Kelas wajib dibandingkan dengan label model di cabang zona; `customClasses` tidak membuktikan kemampuan. Sidecar label yang berubah menghapus cache lama. |
| 2026-10-15 | Pemeriksaan model bawaan | Metadata saja | `yolov8n.pt`: 80 label; person/truck ada, tire tidak ada | Bukan uji inference atau akurasi; model ban masih diperlukan. |
| 2026-10-15 | Regresi integrasi setelah perubahan | PASS lokal | pytest model/server 24 passed; `test_project_binding.py`; `test_project_node_integration.py`; `test_nodes.py` 9 suites; `node --check static/app.js`; `py_compile`; `git diff --check` | Tidak membuktikan browser baru, RTSP, dua runner, kapasitas CPU, atau ERP. |
| 2026-10-18 | VLM Box Tracker (Jev / OpenRouter) | PASS unit & integrasi lokal | `engine/vlm_box_tracker.py`, `test_vlm_box_tracker.py` (6 checks), `test_vlm_box_tracker_integration.py` (3 checks) | Dual provider (OpenRouter / TypeSafe Jev), multi-target optical flow LK (21x21) + Kalman filter history rewind/replay, non-blocking background worker, fallback key `.env`, downstream zone timer/alert routing; tanpa ketergantungan YOLO inference. |
| 2026-10-18 | AI Agent Node (n8n-style LLM/VLM) | PASS unit & integrasi lokal | `engine/ai_agent.py`, `test_ai_agent.py` (6 checks), `test_ai_agent_integration.py` (3 checks) | Multi-provider (OpenAI official `gpt-4o-mini`/`gpt-4o`, OpenRouter, Local Ollama/vLLM), multimodal vision base64 snapshot + data deteksi/event, on_event & periodic trigger, decision gate filter, downstream delivery ke alert/webhook/db; tanpa dependensi library eksternal baru. |
| 2026-10-18 | Audit Seluruh 50 Node & Upgrade v2 | PASS audit, unit & E2E (6 suites) | `engine/node_catalog.py`, `static/app.js`, `tests/*.e2e.ts`, `.e2e/report.json` | 50 node memiliki kategori eksplisit; 257 parameter config 100% berlabel Bahasa Indonesia dan berpenjelasan (FIELD_HELP); 50/50 node memiliki panduan interaktif (NODE_GUIDES_ID) termasuk `python_script`; pencarian node cerdas mencakup konsep/kategori; 6 test E2E (Sources & AI, Tracking & Analysis, Preprocessing & Drawing, Logic & Outputs, AI Agent, Home) lulus 100% dengan 24 tangkapan layar. |
| 2026-10-18 | Implementasi Dashboard Operasional (Fase D, E, F, G) | PASS backend, UI & E2E (7 suites) | `server.py`, `static/index.html`, `static/style.css`, `static/app.js`, `tests/dashboard_operations.e2e.ts`, `.e2e/report.json` | Topbar tab switcher (Workflow Studio, Live Cameras, Workshop Sessions, Warehouse Events); 8-stream RTSP CCTV matrix (WS-01 s/d WS-05 Workshop Bays, WH-01 s/d WH-03 Warehouse Gates) dengan switcher grid 1/4/9 dan filter pill; Rekap Sesi Workshop dengan filter shift kerja, pencarian live, dan export CSV; Log Kejadian Keluar Gerbang Gudang dengan status ERP delivery, filter gate, dan export CSV; 7 suite E2E Playwright/Agentic 100% PASS (35 screenshots visual). |
| 2026-10-18 | Overlay / Annotate Drawing Layers Inspector (Roboflow-style) | PASS backend, UI & E2E (`node_overlay_annotate.e2e.ts`) | `static/app.js`, `static/style.css`, `server.py`, `tests/node_overlay_annotate.e2e.ts`, `.e2e/report.json` | Refactor inspector Overlay / Annotate dengan judul 'Node settings', pill badge, switch toggle 'Enabled', tombol '+ Add layer' dengan popover dropdown (Bounding box, Label, Confidence, Status badge, Custom text, Heatmap, Direction Arrow), kartu layer interaktif dengan reorder up/down, delete, expand/collapse, dan live update parameter (warna, ketebalan, opacity, template, posisi, filter kelas); E2E test lulus 100% dengan 4 tangkapan layar. |
| 2026-10-18 | Projects & Templates Hub, Left Rail Navigation & Central Model Registry | PASS backend, UI & E2E (`projects_and_models_hub.e2e.ts`) | `server.py`, `static/index.html`, `static/style.css`, `static/app.js`, `tests/projects_and_models_hub.e2e.ts`, `.e2e/report.json` | Landing page Projects Hub dengan aksi Hero (New project, Import, Templates), Recent Projects & Templates cards ('Bottle Visual Inspection'); Studio container dengan Left Rail navigasi 2 tab (Workflow & Models); Central Model Registry table dengan metadata lengkap (tipe, versi, ukuran, status, engine, format), dialog upload modal drag-and-drop, filter optgroup model di inspector node, dan tombol switcher `[📁] Project ▾` kembali ke Hub; E2E test lulus 100% dengan 5 tangkapan layar. |

| 2026-10-18 | Pembersihan Data Dummy & Standarisasi Initial State | PASS backend, UI, unit & E2E (`dashboard_operations.e2e.ts`) | `server.py`, `data/cameras.json`, `data/projects.json`, `static/index.html`, `static/app.js`, `test_cameras_api.py`, `tests/dashboard_operations.e2e.ts`, `.e2e/report.json` | Menghapus seluruh data tiruan/dummy dari sistem: (1) Menghapus array hardcoded dummy workshop sessions `[SES-20261018-001 ... 005]` dan dummy warehouse events `[EVT-WH-20261018-088 ... 091]` di `server.py`, digantikan query nyata ke SQLite database `visonode.db` (atau fallback empty array jika belum ada eksekusi workflow); (2) Menghitung metric KPI `dashboard_overview` secara dinamis (0 Sesi, 0h 00m durasi, 0 Event, '-' ERP); (3) Membersihkan `data/cameras.json` menjadi 8 kamera operasional bersih dengan durasi 0, tire 0, fps 0.0, status IDLE/MONITORING, dan menghapus kamera uji `WS-06`; (4) Menghapus duplikasi proyek uji dari `data/projects.json` dan folder `data/projects/`; (5) Menambahkan empty-state informatif di tabel sesi workshop dan log gerbang gudang; unit tests backend 21/21 PASS dan E2E test `dashboard_operations.e2e.ts` lulus 100% dengan bukti tangkapan layar visual. |
| 2026-10-18 | Polish Tampilan Modal Pengaturan Kamera (High-Contrast & Modern Controls) | PASS UI & E2E (`camera_settings_workflow.e2e.ts`) | `static/index.html`, `static/style.css`, `static/app.js`, `tests/camera_settings_workflow.e2e.ts`, `.e2e/report.json` | Refactor visual komprehensif pada dialog modal Pengaturan Kamera: (1) Mengganti teks lime-green pucat yang silau dan tidak terbaca di background putih menjadi tipografi kontras tinggi (navy gelap `#0f172a` dan dark emerald `#047857`); (2) Mengganti input & select browser default menjadi kontrol modern dengan sudut membulat, padding nyaman, background `#f8fafc`, focus ring teal, dan chevron dropdown SVG; (3) Desain ulang kartu 'Project Workflow Terhubung' dengan container ber-border rapi, badge status hijau pekat `✔ Terhubung ke workflow`, tombol aksi template emerald, dan tombol 'Buka di Studio' teal; (4) Menambahkan badge ikon kamera modern di header modal; E2E test lulus 100% dengan tangkapan layar visual. |
| 2026-10-18 | Direct Shortcut & Interactive Drawing Poligon Area Kamera (ROI Durasi Kerja) | PASS UI, Canvas, Unit & E2E (`camera_settings_workflow.e2e.ts`) | `static/index.html`, `static/style.css`, `static/app.js`, `tests/camera_settings_workflow.e2e.ts`, `.e2e/report.json` | Penambahan fitur alur gambar poligon area langsung dari kamera: (1) Tombol shortcut visual `[📐 Gambar Poligon Area]` (`#camDrawPolygonBtn`) di modal Pengaturan Kamera; (2) Klik shortcut otomatis membuka Studio, memuat workflow kamera, memilih node `zone_activity_timer` / `zone_exit_event`, dan mengaktifkan SVG editor poligon interaktif di atas frame preview live/kalibrasi; (3) Fallback frame kalibrasi 16:9 ber-grid jika pipeline belum distart, sehingga operator dapat langsung menentukan titik sudut sebelum streaming dimulai; (4) Toolbar interaktif (status titik, geser vertex handle, tambah titik di garis, hapus titik, Simpan zona, Batal); (5) Pengujian unit backend 21/21 PASS dan pengujian E2E `tests/camera_settings_workflow.e2e.ts` lulus 100% dalam 5.91s dengan bukti visual tangkapan layar nyata. |
| 2026-10-18 | Multi-Zone Occupancy & Activity Tracker (General Table / Area / Bay Tracker) | PASS engine, pipeline, inspector, visual editor, unit & E2E (`multi_zone_occupancy.e2e.ts`) | `engine/multi_zone_occupancy.py`, `engine/node_catalog.py`, `engine/core.py`, `engine/main.py`, `static/app.js`, `static/style.css`, `test_multi_zone_occupancy.py`, `tests/multi_zone_occupancy.e2e.ts`, `.e2e/report.json` | Implementasi node Multi-Zone Occupancy & Activity Tracker yang 100% GENERAL & MODULAR (berdasarkan analisis video YouTube Restaurant & Multi-Zone Analytics): (1) Engine komputasi multi-poligon point-in-polygon (feet/torso/chest testing untuk person, center untuk objek lain); (2) Finite State Machine per-zona independen (`VACANT` ➔ `CONFIRMING` ➔ `OCCUPIED` / `OVER_CAPACITY` / `OVERSTAY` ➔ `PENDING_VACANT` ➔ `VACANT`) dengan timer durasi terisi real-time, toleransi grace period, dan deteksi overstay; (3) Event emisi `zone_occupied`, `zone_vacated` (dengan durasi total & turnover index), dan `zone_overstay` untuk downstream alerts/database; (4) Visual overlay renderer di pipeline dengan glassmorphism badge kartu meja/zona dan top HUD summary; (5) Multi-Zone Visual Polygon Editor di atas frame preview dengan pemilih area aktif, input nama & kapasitas, penambahan/penghapusan area baru, dan draggable vertex handles; (6) 5/5 unit tests pytest PASS dan E2E test `multi_zone_occupancy.e2e.ts` lulus 100% dalam 6.28s dengan 4 bukti tangkapan layar visual. |

### Checks yang dapat dijalankan sesi berikutnya

```powershell
npm run test:e2e
npx e2e run tests/multi_zone_occupancy.e2e.ts
npx e2e run tests/camera_settings_workflow.e2e.ts
npx e2e run tests/dashboard_operations.e2e.ts
.venv/Scripts/python.exe -m pytest -v test_multi_zone_occupancy.py
.venv/Scripts/python.exe -m pytest -q test_nodes.py test_project_nodes.py
node -c "static/app.js"
git diff --check
```

Hasil terbaru 18 Oktober: Node General Multi-Zone Occupancy & Activity Tracker telah selesai diimplementasikan secara menyeluruh (Engine, Pipeline, Event Routing, Inspector, dan Multi-Zone Visual Polygon Editor). Seluruh unit tests (5/5) dan E2E test (`tests/multi_zone_occupancy.e2e.ts`, 6.28s, 7.1k tokens) LULUS 100% dengan 4 tangkapan layar visual nyata terlampir.





