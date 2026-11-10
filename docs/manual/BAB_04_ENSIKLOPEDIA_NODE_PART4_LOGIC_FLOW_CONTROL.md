# ENSIKLOPEDIA NODE: BAGIAN 4.4
# LOGIC & FLOW CONTROL (15 NODES)

---

## DAFTAR ISI BAGIAN 4.4

- 4.4.1 `motion_gate`: Motion Gate (Penyaring Gerakan Kamera CCTV Cerdas)
- 4.4.2 `alarm_cooldown_gate`: Alarm Cooldown Gate (Pencegah Banjir Alarm / Spam Suppressor)
- 4.4.3 `debounce`: Debounce Filter (Stabilisasi Sinyal Kejadian Berayun)
- 4.4.4 `switch_case`: Switch Case Router (Perutean Alur Multi-Cabang Berbasis String/Kelas)
- 4.4.5 `if_else`: If / Else Conditional Branching (Percabangan Biner Benar / Salah)
- 4.4.6 `class_detected_condition`: Class Detected Condition (Pemicu Berdasarkan Keberadaan Kelas Tertentu)
- 4.4.7 `object_count_condition`: Object Count Condition (Evaluasi Ambang Batas Jumlah Objek)
- 4.4.8 `compare_value`: Compare Value (Operator Pembanding Numerik Universal)
- 4.4.9 `confidence_threshold`: Confidence Threshold Filter (Penyaring Probabilitas Deteksi)
- 4.4.10 `class_replacement`: Class Replacement (Remapping Nama Kelas Model AI)
- 4.4.11 `and_or_logic`: AND / OR Boolean Logic (Penggabung Multi-Kondisi Gerbang Logika)
- 4.4.12 `rate_limiter`: Rate Limiter (Pembatas Frekuensi Panggilan Eksternal)
- 4.4.13 `roi_filter`: ROI Filter (Penyaring Deteksi Khusus di Dalam Kotak ROI)
- 4.4.14 `timer_delay`: Timer / Delay (Penunda Waktu Propagasi Paket)
- 4.4.15 `trigger_once`: Trigger Once (Pemicu Kejadian Tepat Satu Kali Hingga Reset)

---

## 4.4.1 `motion_gate`: Motion Gate (Penyaring Gerakan CCTV Cerdas)

### Deskripsi Fungsional
Node hemat energi yang berfungsi sebagai "penjaga pintu gerbang" komputasi. Pada rekaman CCTV statis (misal gudang di malam hari atau lorong sepi), 95% frame tidak memiliki aktivitas sama sekali. Menjalankan model AI berat pada frame kosong membuang daya listrik dan CPU.

Node `motion_gate` menghitung perubahan optik ringan antar-frame. Jika pemandangan diam, node memblokir aliran data ke model AI berat. Begitu terdeteksi pergerakan fisik nyata di atas ambang batas, gerbang seketika terbuka dan mengalirkan frame ke model AI.

### Diagram Alur Data & Pin Koneksi
```
+------------------------------------------+
|  [Icon]  Motion Gate                     |
+------------------------------------------+
| (o) Input Image                          |
|                               (o) Image  |
|                               (o) Motion |
+------------------------------------------+
```

### Parameter Konfigurasi (Config Schema)
| Parameter | Tipe Data | Nilai Default | Pilihan / Rentang | Penjelasan Fungsional |
|---|---|---|---|---|
| `sensitivity` | Float | `0.02` | `0.001` s/d `0.50` | Persentase minimum piksel yang harus bergerak untuk membuka gerbang (0.02 = 2% luas layar). |
| `minContourArea` | Integer | `500` | `50` s/d `10000` | Luas kontur minimum piksel gerak untuk mengabaikan serangga terbang atau noise kamera. |
| `motionHoldSeconds`| Float | `3.0` | `0.5` s/d `30.0` | Durasi gerbang tetap terbuka setelah gerakan terakhir berhenti, mencegah pemutusan frame mendadak. |

---

## 4.4.2 `alarm_cooldown_gate`: Alarm Cooldown Gate (Pencegah Banjir Alarm)

### Deskripsi Fungsional
Mencegah fenomena *Alert Fatigue* (kebanjiran notifikasi beruntun). Jika sebuah pelanggaran terjadi (misal orang tidak memakai helm), sistem deteksi kamera 30 FPS akan mendeteksi pelanggaran tersebut 30 kali setiap detik. Mengirim 30 pesan WhatsApp/Telegram per detik akan membanjiri ponsel supervisor.

Node `alarm_cooldown_gate` memastikan bahwa setelah satu alarm ditembakkan, alarm serupa dibungkam (*muted*) selama periode pendinginan (*cooldown window*, misal 30 detik atau 5 menit), sebelum diizinkan berbunyi kembali.

### Parameter Konfigurasi
- `cooldownSeconds` (Float, Default: `30.0`): Periode hening minimum antar-alarm.
- `groupByKey` (String, Default: `"class_name"`): Pilihan pengelompokan cooldown: `"global"`, `"class_name"`, `"track_id"`. Jika diset `"track_id"`, orang A yang melanggar tidak akan menghalangi alarm untuk orang B yang baru masuk.

---

## 4.4.3 `debounce`: Debounce Filter (Penstabil Sinyal Kejadian)

### Deskripsi Fungsional
Menghilangkan sinyal berayun (*flickering trigger*). Dalam computer vision, deteksi objek terkadang hilang selama 1 frame lalu muncul kembali di frame berikutnya karena oklusi sesaat. Debounce memastikan bahwa kondisi harus stabil bernilai `TRUE` selama durasi waktu tertentu berturut-turut sebelum pemicu downstream diaktifkan.

### Parameter Konfigurasi
- `debounceTimeMs` (Integer, Default: `500`): Waktu stabilisasi minimum dalam milidetik.
- `mode` (String, Default: `"leading_trailing"`): Pilihan: `"leading"` (pemicu awal), `"trailing"` (pemicu akhir), `"both"`.

---

## 4.4.4 `switch_case`: Switch Case Router (Perutean Multi-Arah)

### Deskripsi Fungsional
Mengarahkan aliran data ke salah satu dari beberapa cabang keluaran berdasarkan nilai variabel kunci (misalnya memisahkan rute pemrosesan: jika `class == "person"` diarahkan ke cabang analisis pose K3; jika `class == "car"` diarahkan ke cabang pembaca plat LPR).

### Parameter Konfigurasi
- `routingKey` (String, Default: `"class_name"`): Properti metadata yang diperiksa.
- `cases` (List[String], Default: `["person", "vehicle", "other"]`): Daftar nama cabang keluaran yang disediakan node.

---

## 4.4.5 `if_else`: If / Else Conditional Branching

### Deskripsi Fungsional
Mengevaluasi ekspresi kondisi biner sederhana. Jika kondisi terpenuhi, paket dialirkan melalui pin `True`. Jika tidak, paket dialirkan melalui pin `False`.

### Parameter Konfigurasi
- `conditionType` (String, Default: `"count_greater_than"`): Jenis pengujian kondisi.
- `thresholdValue` (Float, Default: `0.0`): Nilai ambang pembanding.

---

## 4.4.6 `class_detected_condition`: Class Detected Condition

### Deskripsi Fungsional
Memeriksa apakah kelas objek tertentu (misal `"fire"`, `"smoke"`, atau `"knife"`) muncul di dalam daftar deteksi frame saat ini. Mengeluarkan sinyal boolean seketika.

### Parameter Konfigurasi
- `targetClass` (String, Default: `"person"`): Nama label kelas yang dicari.
- `minConfidence` (Float, Default: `0.50`): Ambang keyakinan minimum kelas tersebut.

---

## 4.4.7 `object_count_condition`: Object Count Condition

### Deskripsi Fungsional
Mengevaluasi apakah total objek yang terdeteksi memenuhi aturan kuantitas tertentu, misalnya: "Jumlah orang > 10" (peringatan kerumunan) atau "Jumlah ban == 0" (peringatan area kosong).

### Parameter Konfigurasi
- `operator` (String, Default: `">"`): Operator pembanding (`>`, `<`, `>=`, `<=`, `==`, `!=`).
- `countThreshold` (Integer, Default: `1`): Jumlah kuantitas target.
- `targetClass` (String, Default: `""`): Filter kelas tertentu (kosong = seluruh kelas).

---

## 4.4.8 `compare_value`: Compare Value (Pembanding Numerik Universal)

### Deskripsi Fungsional
Membandingkan dua variabel numerik yang mengalir dari node hulu (misalnya membandingkan kecepatan kendaraan dengan batas rambu kecepatan jalan 30 km/jam).

---

## 4.4.9 `confidence_threshold`: Confidence Threshold Filter

### Deskripsi Fungsional
Menyaring daftar deteksi objek, membuang seluruh kotak yang memiliki skor keyakinan di bawah ambang batas yang ditentukan. Memastikan hanya deteksi berkualitas tinggi yang masuk ke tahap analitik lanjutan.

---

## 4.4.10 `class_replacement`: Class Replacement (Remapping Nama Kelas)

### Deskripsi Fungsional
Mengubah nama label kelas model AI bawaan menjadi istilah bisnis internal perusahaan. Contoh: Mengubah label `"truck"` menjadi `"Dump Truck HD785"`, atau mengubah `"person"` menjadi `"Operator Workshop"`.

### Parameter Konfigurasi
- `mappingDict` (JSON Object): Pasangan pemetaan nama lama ke nama baru (contoh: `{"car": "Kendaraan Ringan LV", "person": "Karyawan"}`).

---

## 4.4.11 `and_or_logic`: AND / OR Boolean Logic

### Deskripsi Fungsional
Menggabungkan beberapa kondisi keluaran dari node logika lain menjadi satu keputusan terpadu:
- **Operasi AND**: Seluruh kondisi harus bernilai `TRUE` (misal: "Ada orang" AND "Zona aktif" AND "Di luar jam kerja").
- **Operasi OR**: Cukup salah satu kondisi bernilai `TRUE` untuk memicu alarm.

---

## 4.4.12 `rate_limiter`: Rate Limiter (Pembatas Frekuensi)

### Deskripsi Fungsional
Membatasi laju aliran paket data maksimum per detik atau per menit. Berguna saat menghubungkan alur kerja ke API pihak ketiga yang memiliki kuota pembatasan panggilan (*Rate Limit Quota*).

---

## 4.4.13 `roi_filter`: ROI Filter (Region of Interest)

### Deskripsi Fungsional
Menyaring objek deteksi berdasarkan koordinat spasial kotak pembatasnya. Hanya objek yang titik pusatnya (*bounding box centroid*) berada di dalam kotak area ROI yang diizinkan lewat; objek di luar kotak akan dibuang dari daftar deteksi.

---

## 4.4.14 `timer_delay`: Timer / Delay

### Deskripsi Fungsional
Menunda transmisi paket frame atau kejadian selama durasi waktu tertentu (misal tunda 2.0 detik) untuk sinkronisasi waktu dengan sistem eksternal atau kamera sudut lain.

---

## 4.4.15 `trigger_once`: Trigger Once (Pemicu Tunggal)

### Deskripsi Fungsional
Hanya memicu kejadian tepat satu kali saat kondisi pertama kali terpenuhi, lalu mengunci diri (*latched*). Pemicu tidak akan aktif kembali sampai menerima sinyal `RESET` dari node lain atau alur kerja di-restart.

---

*Lanjutkan ke **Bagian 4.5: Ensiklopedia Node - Visualisasi & Anotasi** untuk mempelajari teknik rendering overlay grafis dan visualisasi data langsung di atas video.*
