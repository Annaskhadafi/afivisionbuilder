# ENSIKLOPEDIA NODE: BAGIAN 4.1
# SOURCES (SUMBER INPUT) & IMAGE PREPROCESSING (19 NODES)

---

## DAFTAR ISI BAGIAN 4.1

1. **Kategori Sources (Sumber Input Video)**
   - 4.1.1 `input`: Input Universal (Webcam, File MP4, Mock Generator)
   - 4.1.2 `ip_camera`: IP Camera / CCTV Network Stream (RTSP, RTMP, HLS, HTTP)
   - 4.1.3 `video_speed_controller`: Video Speed & Timeline Scrubbing Controller
2. **Kategori Image Preprocessing (Pra-Pemrosesan Citra)**
   - 4.1.4 `auto_rotate_edges`: Deteksi Kemiringan Otomatis & Koreksi Rotasi Tepi
   - 4.1.5 `background_subtract`: Pengurangan Latar Belakang (MOG2 / KNN Background Subtraction)
   - 4.1.6 `blur_sharpen`: Penghalusan Gaussian Blur / Penajaman Citra (Sharpen Kernel)
   - 4.1.7 `brightness_contrast`: Kalibrasi Kecerahan, Kontras & Adaptif CLAHE
   - 4.1.8 `camera_focus`: Evaluasi Ketajaman & Fokus Lensa Kamera (Laplacian Variance)
   - 4.1.9 `color_convert`: Konversi Ruang Warna (BGR, RGB, HSV, Grayscale, LAB)
   - 4.1.10 `crop`: Pemotongan Area Citra Statis (Region of Interest / ROI Crop)
   - 4.1.11 `delta_filter`: Filter Perbedaan Gerak Antar-Frame (Temporal Frame Differencing)
   - 4.1.12 `frame_sampler`: Pengatur Frekuensi Frame / FPS Decimation
   - 4.1.13 `perspective`: Transformasi Perspektif Bird's Eye View / Keystone Correction
   - 4.1.14 `privacy_mask`: Masking Area Privasi & Pengecualian Deteksi (Exclusion Mask)
   - 4.1.15 `python_script`: Eksekusi Skrip Python Kustom Terisolasi (Sandboxed Runtime)
   - 4.1.16 `resize`: Skalasi Dimensi Citra (Bilinear, Nearest, Bicubic, Area)
   - 4.1.17 `rotate_flip`: Rotasi Sudut Tetap (90, 180, 270 Derajat) & Pembalikan Cermin (Flip)
   - 4.1.18 `slicer`: Pemotong Objek Kecil Berkecepatan Tinggi (SAHI - Slicing Inference)
   - 4.1.19 `undistort`: Koreksi Distorsi Lensa Fisheye & Wide-Angle (Camera Calibration)

---

## 4.1.1 `input`: Input Universal (Webcam / File Video)

### Deskripsi Fungsional
Node `input` berfungsi sebagai generator sumber citra awal untuk pengujian lokal, demonstrasi alur kerja, atau inferensi dari file video rekaman dan kamera web USB bawaan perangkat.

### Diagram Alur Data & Pin Koneksi
```
+------------------------------------------+
|  [Icon]  Input (Universal Source)        |
+------------------------------------------+
|                               (o) Image  |
+------------------------------------------+
```
- **Pin Input**: *Tidak ada* (Node Awal / Root Generator)
- **Pin Output**: 
  - `image` (`np.ndarray`): Matriks citra warna format BGR ukuran resolusi asli sumber.

### Parameter Konfigurasi (Config Schema)
| Parameter | Tipe Data | Nilai Default | Pilihan / Rentang | Penjelasan Fungsional |
|---|---|---|---|---|
| `sourceType` | String | `"sample"` | `"sample"`, `"webcam"`, `"file"`, `"url"` | Menentukan jenis media input yang akan dibaca. |
| `webcamIndex` | Integer | `0` | `0` s/d `10` | Indeks perangkat keras kamera web USB (0 = kamera default). |
| `videoPath` | String | `""` | Path lokal file | Alamat absolut atau relatif file video lokal (contoh: `data/sample.mp4`). |
| `loop` | Boolean | `true` | `true` / `false` | Memutar ulang file video secara otomatis saat mencapai akhir durasi. |
| `targetFps` | Integer | `30` | `1` s/d `60` | Membatasi kecepatan pembacaan frame per detik untuk mencegah *CPU spike*. |

### Algoritma & Perilaku Teknis
Node menggunakan `cv2.VideoCapture` yang dienkapsulasi dengan thread pembacaan asinkron. Jika sumber video mencapai akhir frame (*End of File / EOF*) dan opsi `loop=true`, penunjuk frame akan di-seek kembali ke frame 0 melalui `cap.set(cv2.CAP_PROP_POS_FRAMES, 0)`.

---

## 4.1.2 `ip_camera`: IP Camera / CCTV Network Stream

### Deskripsi Fungsional
Node tulang punggung integrasi pengawasan industri untuk menarik siaran langsung video (*live video stream*) dari kamera jaringan (IP Camera), NVR, DVR, atau encoder video industri melalui berbagai protokol jaringan.

### Diagram Alur Data & Pin Koneksi
```
+------------------------------------------+
|  [Icon]  IP Camera / CCTV Stream         |
+------------------------------------------+
|                               (o) Image  |
+------------------------------------------+
```
- **Pin Input**: *Tidak ada* (Node Awal)
- **Pin Output**:
  - `image` (`np.ndarray`): Citra frame BGR beresolusi tinggi langsung dari stream jaringan.

### Parameter Konfigurasi (Config Schema)
| Parameter | Tipe Data | Nilai Default | Pilihan / Rentang | Penjelasan Fungsional |
|---|---|---|---|---|
| `rtspUrl` | String | `"rtsp://..."` | URL RTSP Valid | Alamat RTSP lengkap kamera termasuk autentikasi user dan password. |
| `transport` | String | `"tcp"` | `"tcp"`, `"udp"`, `"http"` | Protokol transport RTSP. TCP sangat disarankan untuk mencegah *packet drop* dan artefak smearing. |
| `reconnectInterval` | Integer | `5` | `1` s/d `60` | Waktu tunggu (detik) sebelum mencoba menghubungkan ulang jika stream terputus. |
| `dropFrames` | Boolean | `true` | `true` / `false` | Membuang frame yang menumpuk di buffer saat inferensi AI lebih lambat dari FPS kamera (*Zero-Latency Mode*). |
| `hardwareDecode` | String | `"auto"` | `"auto"`, `"cpu"`, `"cuda"`, `"qsv"` | Akselerasi decoding perangkat keras menggunakan GPU NVIDIA NVDEC atau Intel QuickSync. |

### Contoh Format URL RTSP Berbagai Merek Kamera CCTV:
- **Hikvision / Hilook**: `rtsp://admin:Password123@192.168.1.64:554/Streaming/Channels/101` (Sub-stream: `/102`)
- **Dahua / IMOU**: `rtsp://admin:Password123@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0`
- **Uniview (UNV)**: `rtsp://admin:Password123@192.168.1.30:554/unicast/c1/s0/live`
- **Axis Communications**: `rtsp://root:Password123@192.168.1.50:554/axis-media/media.amp`

---

## 4.1.3 `video_speed_controller`: Video Speed & Timeline Scrubbing Controller

### Deskripsi Fungsional
Node pengendali playback video mutakhir yang memungkinkan akselerasi playback (0.25x hingga 4.0x), fungsi loncat timeline seketika (*seeking/scrubbing*), serta sinkronisasi dinamis via REST API `/api/video/seek` dan `/api/video/playback-speed`.

### Diagram Alur Data & Pin Koneksi
```
+------------------------------------------+
|  [Icon]  Video Speed & Timeline Control  |
+------------------------------------------+
| (o) Input Image                          |
|                               (o) Image  |
+------------------------------------------+
```
- **Pin Input**: `image` (Citra sumber video)
- **Pin Output**: `image` (Citra yang telah disinkronkan kecepatannya dengan overlay HUD opsional)

### Parameter Konfigurasi (Config Schema)
| Parameter | Tipe Data | Nilai Default | Pilihan / Rentang | Penjelasan Fungsional |
|---|---|---|---|---|
| `speedMultiplier` | Float | `1.0` | `0.25` s/d `4.0` | Faktor kecepatan pemutaran (misal: 0.5x slow motion, 2.0x fast forward). |
| `seekPercent` | Float | `0.0` | `0.0` s/d `100.0` | Posisi loncat timeline dalam persen durasi video. |
| `showOverlayHud` | Boolean | `true` | `true` / `false` | Menampilkan badge HUD transparan berisi indikator kecepatan dan posisi timeline pada pojok video. |
| `syncMode` | String | `"adaptive"` | `"adaptive"`, `"drop"`, `"wait"` | Mekanisme sinkronisasi frame rate untuk mempertahankan konsistensi clock visual. |

---

## 4.1.4 `auto_rotate_edges`: Deteksi Kemiringan & Koreksi Rotasi Otomatis

### Deskripsi Fungsional
Mengidentifikasi orientasi garis dominan pada citra (misalnya plat nomor, dokumen faktur, atau palet miring) dan memutar citra secara otomatis agar sejajar tegak lurus (*upright deskewing*).

### Parameter Konfigurasi
- `edgeThreshold1` (Integer, Default: `50`): Ambang batas bawah detektor tepi Canny.
- `edgeThreshold2` (Integer, Default: `150`): Ambang batas atas detektor tepi Canny.
- `houghThreshold` (Integer, Default: `100`): Akumulator batas minimum transformasi Hough Line.
- `maxAngleDegrees` (Float, Default: `45.0`): Batas rotasi koreksi maksimum untuk mencegah pemutaran citra terbalik.

---

## 4.1.5 `background_subtract`: Pengurangan Latar Belakang (Motion Mask)

### Deskripsi Fungsional
Memisahkan objek bergerak (*foreground*) dari pemandangan diam (*background*) menggunakan model statistik Gaussian Mixture (MOG2) atau K-Nearest Neighbors (KNN).

### Parameter Konfigurasi
- `algorithm` (String, Default: `"mog2"`): Pilihan antara `"mog2"` atau `"knn"`.
- `history` (Integer, Default: `500`): Jumlah frame historis yang digunakan untuk membangun model latar belakang.
- `varThreshold` (Float, Default: `16.0`): Ambang batas variansi Mahalanobis untuk mengklasifikasikan piksel gerak.
- `detectShadows` (Boolean, Default: `true`): Menandai bayangan objek sebagai warna abu-abu agar tidak dianggap sebagai benda solid.

---

## 4.1.6 `blur_sharpen`: Penghalusan Gaussian Blur / Penajaman Citra

### Deskripsi Fungsional
Melakukan pemfilteran spasial pada citra untuk mengurangi derau frekuensi tinggi (*high-frequency noise*) pada kamera malam, atau mempertajam tepi objek kabur sebelum masuk ke detektor AI.

### Parameter Konfigurasi
- `mode` (String, Default: `"blur"`): Pilihan `"blur"`, `"gaussian_blur"`, `"median"`, `"sharpen"`.
- `kernelSize` (Integer, Default: `5`): Ukuran matriks kernel ganjil (3, 5, 7, 9, 11). Nilai lebih besar menghasilkan keburaman lebih kuat.
- `sigmaX` (Float, Default: `1.5`): Deviasi standar kernel Gaussian pada sumbu X.
- `sharpenStrength` (Float, Default: `1.0`): Pengali intensitas unsharp masking untuk mode penajaman.

---

## 4.1.7 `brightness_contrast`: Kalibrasi Kecerahan, Kontras & CLAHE

### Deskripsi Fungsional
Mengoreksi kondisi pencahayaan ekstrem (ruangan gelap atau cahaya silau matahari) menggunakan transformasi linear $g(x) = \alpha \cdot f(x) + \beta$ atau algoritma adaptif CLAHE (*Contrast Limited Adaptive Histogram Equalization*).

### Parameter Konfigurasi
- `brightness` (Integer, Default: `0`, Rentang: `-100` s/d `100`): Penambah nilai offset piksel ($\beta$).
- `contrast` (Float, Default: `1.0`, Rentang: `0.1` s/d `3.0`): Pengali kontras citra ($\alpha$).
- `useClahe` (Boolean, Default: `false`): Mengaktifkan ekualisasi histogram lokal adaptif pada kanal Luminance (YCrCb atau LAB).
- `claheClipLimit` (Float, Default: `2.0`): Batas pemotongan kontras pada CLAHE untuk membatasi penguatan derau (*noise amplification*).
- `claheGridSize` (Integer, Default: `8`): Ukuran blok kisi kontekstual (misal: 8x8 piksel).

---

## 4.1.8 `camera_focus`: Evaluasi Ketajaman & Fokus Lensa Kamera

### Deskripsi Fungsional
Menilai kesehatan visual kamera secara otomatis dengan mengukur variansi operator Laplacian ($\sigma^2_{\Delta}$). Jika lensa buram karena debu, cipratan air, atau pergeseran fokus mekanis, node akan memicu peringatan pemeliharaan.

### Parameter Konfigurasi
- `blurThreshold` (Float, Default: `100.0`): Nilai skor fokus minimum. Frame dengan skor di bawah nilai ini dikategorikan `BLURRY` / buram.
- `warningCooldownSeconds` (Integer, Default: `60`): Jeda waktu minimum sebelum memicu kembali peringatan fokus rusak ke dashboard.

---

## 4.1.9 `color_convert`: Konversi Ruang Warna (Color Space)

### Deskripsi Fungsional
Mengonversi matriks citra BGR ke ruang warna lain untuk mempermudah analisis warna tertentu (misal: isolasi warna api pada HSV atau analisis pencahayaan murni pada LAB).

### Parameter Konfigurasi
- `targetSpace` (String, Default: `"rgb"`): Pilihan: `"rgb"`, `"gray"`, `"hsv"`, `"lab"`, `"ycrcb"`.

---

## 4.1.10 `crop`: Pemotongan Area Citra Statis (ROI Crop)

### Deskripsi Fungsional
Memotong persegi panjang statis dari frame video penuh untuk memfokuskan sumber daya inferensi AI hanya pada area kritis (misalnya hanya pada konveyor barang atau bay workshop tertentu), menghemat hingga 70% beban komputasi model AI.

### Parameter Konfigurasi
- `x` (Float, Default: `0.0`, Rentang: `0.0` s/d `1.0`): Koordinat normalisasi horizontal sudut kiri atas.
- `y` (Float, Default: `0.0`, Rentang: `0.0` s/d `1.0`): Koordinat normalisasi vertikal sudut kiri atas.
- `width` (Float, Default: `1.0`, Rentang: `0.0` s/d `1.0`): Lebar normalisasi area potongan.
- `height` (Float, Default: `1.0`, Rentang: `0.0` s/d `1.0`): Tinggi normalisasi area potongan.

---

## 4.1.11 `delta_filter`: Filter Perbedaan Gerak Antar-Frame

### Deskripsi Fungsional
Membandingkan frame saat ini $I_t$ dengan frame sebelumnya $I_{t-1}$ menggunakan pengurangan absolut $|I_t - I_{t-1}|$. Jika persentase piksel yang berubah berada di bawah ambang batas, frame diklasifikasikan statis dan tidak diteruskan ke node AI hilir.

### Parameter Konfigurasi
- `pixelThreshold` (Integer, Default: `25`): Selisih intensitas warna minimum agar satu piksel dianggap berubah.
- `minAreaRatio` (Float, Default: `0.005`): Rasio luas perubahan minimum terhadap total frame (0.5%) untuk meloloskan frame.

---

## 4.1.12 `frame_sampler`: Pengatur Frekuensi Frame (FPS Decimation)

### Deskripsi Fungsional
Mengatur frekuensi frame yang mengalir ke node berikutnya (misal: kamera mengirim 30 FPS, tetapi model AI hanya perlu mengeksekusi 5 FPS).

### Parameter Konfigurasi
- `sampleRate` (Integer, Default: `5`): Hanya meneruskan 1 frame setiap $N$ frame masuk.
- `maxFps` (Float, Default: `10.0`): Membatasi laju frame maksimum secara temporal (berdasarkan clock detik).

---

## 4.1.13 `perspective`: Transformasi Perspektif Bird's Eye View

### Deskripsi Fungsional
Menerapkan matriks homografi $3 \times 3$ untuk mengubah sudut pandang kamera miring (*angled perspective*) menjadi sudut pandang tegak lurus dari atas (*top-down bird's eye view*).

### Parameter Konfigurasi
- `sourcePoints` (List of Points): Empat titik sudut trapesium pada citra asli.
- `destPoints` (List of Points): Empat titik sudut persegi panjang datar pada citra hasil.
- `outputWidth` (Integer, Default: `640`): Lebar piksel citra hasil proyeksi.
- `outputHeight` (Integer, Default: `480`): Tinggi piksel citra hasil proyeksi.

---

## 4.1.14 `privacy_mask`: Masking Area Privasi & Pengecualian Deteksi

### Deskripsi Fungsional
Mengaburkan (*blackout* atau *blur*) polygon tertentu secara permanen dari frame sebelum masuk ke AI atau Live Preview. Sangat berguna untuk kepatuhan regulasi privasi data (GDPR/K3) untuk menutupi jendela kantor, layar komputer kasir, atau jalan raya umum di luar pabrik.

### Parameter Konfigurasi
- `maskPoints` (List of Coordinates): Titik-titik sudut polygon area yang ingin ditutup.
- `fillColor` (String, Default: `"black"`): Warna penutup: `"black"`, `"white"`, atau `"blur"`.

---

## 4.1.15 `python_script`: Eksekusi Skrip Python Kustom Terisolasi

### Deskripsi Fungsional
Node serbaguna bagi developer untuk menulis kode Python langsung di dalam Workflow Studio guna melakukan manipulasi matriks citra NumPy kustom, kalkulasi matematika, atau integrasi pustaka khusus tanpa memodifikasi kode inti backend.

### Parameter Konfigurasi
- `code` (String): Blok kode Python yang mendefinisikan fungsi `process(frame, detections, context)`.
- `timeoutSeconds` (Float, Default: `0.5`): Batas waktu eksekusi skrip untuk mencegah pembekuan (*freezing*) engine.

---

## 4.1.16 `resize`: Skalasi Dimensi Citra

### Deskripsi Fungsional
Mengubah resolusi spasial frame citra ke lebar dan tinggi target tertentu menggunakan interpolasi matematis teruji.

### Parameter Konfigurasi
- `width` (Integer, Default: `640`): Lebar citra baru.
- `height` (Integer, Default: `480`): Tinggi citra baru.
- `interpolation` (String, Default: `"linear"`): Pilihan: `"linear"` (cepat), `"area"` (terbaik untuk pengecilan), `"cubic"` (terbaik untuk pembesaran), `"nearest"`.
- `keepAspectRatio` (Boolean, Default: `true`): Mempertahankan rasio aspek asli dengan menambahkan bilah hitam (*letterboxing*).

---

## 4.1.17 `rotate_flip`: Rotasi Sudut Tetap & Pembalikan Cermin

### Deskripsi Fungsional
Memutar citra secara fisik sebesar 90°, 180°, atau 270° (searah jarum jam) atau membalik citra secara horizontal/vertikal. Berguna saat kamera CCTV fisik dipasang terbalik pada plafon atau dipasang vertikal (*portrait mode*).

### Parameter Konfigurasi
- `rotationAngle` (Integer, Default: `0`): Pilihan: `0`, `90`, `180`, `270`.
- `flipMode` (String, Default: `"none"`): Pilihan: `"none"`, `"horizontal"` (kiri-kanan), `"vertical"` (atas-bawah), `"both"`.

---

## 4.1.18 `slicer`: Pemotong Objek Kecil Berkecepatan Tinggi (SAHI)

### Deskripsi Fungsional
Mengimplementasikan teknik **Slicing Aided Hyper Inference (SAHI)**. Node ini mengiris frame resolusi tinggi (misal 4K atau 1080p) menjadi kisi-kisi ubin (*tiles*) yang saling bertumpukan (*overlapping patches*). Setiap ubin kemudian diproses secara terpisah oleh model detektor, memungkinkan deteksi objek mikroskopis yang terlalu kecil untuk dideteksi oleh YOLO standar.

### Parameter Konfigurasi
- `sliceHeight` (Integer, Default: `512`): Tinggi piksel setiap ubin irisan.
- `sliceWidth` (Integer, Default: `512`): Lebar piksel setiap ubin irisan.
- `overlapRatioHeight` (Float, Default: `0.2`): Rasio tumpang tindih vertikal antar-ubin (20%).
- `overlapRatioWidth` (Float, Default: `0.2`): Rasio tumpang tindih horizontal antar-ubin (20%).

---

## 4.1.19 `undistort`: Koreksi Distorsi Lensa Fisheye & Wide-Angle

### Deskripsi Fungsional
Menghilangkan efek distorsi cembung tong (*barrel distortion*) pada kamera CCTV bersudut pandang lebar (*wide-angle / fisheye lens*) menggunakan matriks intrinsik kamera ($K$) dan koefisien distorsi ($D$).

### Parameter Konfigurasi
- `cameraMatrix` (Matrix 3x3): Matriks fokal dan titik pusat optik $[[f_x, 0, c_x], [0, f_y, c_y], [0, 0, 1]]$.
- `distCoeffs` (Array 5-Elemen): Vektor distorsi radial dan tangensial $[k_1, k_2, p_1, p_2, k_3]$.

---

*Lanjutkan ke **Bagian 4.2: Ensiklopedia Node - AI Vision Models** untuk mempelajari modul inferensi kecerdasan buatan.*
