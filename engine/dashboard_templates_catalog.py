"""
Afivision Dashboard Templates Catalog & Layout Generator.
Provides comprehensive paired dashboard layouts for all 43 workflow templates.
Each template has a completely distinct, domain-crafted layout architecture,
specialized widgets, tailored coordinates, and realistic initial telemetry.
"""
from __future__ import annotations
import time
from typing import Any, Optional

WORKFLOW_TO_DASHBOARD_MAP: dict[str, str] = {
    # 5 Ultralytics Solutions
    "smart_parking_management": "tpl_smart_parking",
    "retail_queue_management": "tpl_retail_queue_ultralytics",
    "ai_gym_ergonomic": "tpl_ai_gym_ergonomic",
    "driver_blindspot_vision": "tpl_driver_blindspot",
    "live_analytics_hud": "tpl_live_analytics_hud",
    # Flagship & Domain Templates
    "traffic_flow_counter": "tpl_traffic_flow",
    "restaurant_table_occupancy": "tpl_restaurant_dwell",
    "assembly_workshop_cycle_timer": "tpl_assembly_cycle",
    "warehouse_forklift_safety_guard": "tpl_warehouse_safety",
    "retail_checkout_queue_monitor": "tpl_retail_queue",
    "workshop_bay_activity": "tpl_workshop_bay",
    "warehouse_gate_exit": "tpl_warehouse_gate",
    "bottle_visual_inspection": "tpl_bottle_inspection",
    "preprocessing": "tpl_preprocessing",
    "rfdetr_detection": "tpl_rfdetr_detection",
    "filter_counter": "tpl_filter_counter",
    "motion_detection": "tpl_motion_detection",
    "image_enhancement": "tpl_image_enhancement",
    "branching_if_else": "tpl_branching_if_else",
    "workflow-01-detection": "tpl_wf01_detection",
    "workflow-02-filter-count": "tpl_wf02_filter_count",
    "workflow-03-tracking-line": "tpl_wf03_tracking_line",
    "workflow-04-dwell-privacy": "tpl_wf04_dwell_privacy",
    "workflow-05-segmentation": "tpl_wf05_segmentation",
    "workflow-06-crop-classify": "tpl_wf06_crop_classify",
    "workflow-07-if-else": "tpl_wf07_if_else",
    "workflow-08-roi": "tpl_wf08_roi",
    "workflow-09-conditions": "tpl_wf09_conditions",
    "workflow-10-transform": "tpl_wf10_transform",
    "workflow-11-enhance": "tpl_wf11_enhance",
    "workflow-12-calibration": "tpl_wf12_calibration",
    "workflow-13-motion": "tpl_wf13_motion",
    "workflow-14-sampling-slicer": "tpl_wf14_sampling_slicer",
    "workflow-15-barcode": "tpl_wf15_barcode",
    "workflow-16-event-controls": "tpl_wf16_event_controls",
    "workflow-17-python-script": "tpl_wf17_python_script",
    "workflow-18-output": "tpl_wf18_output",
    "workflow-19-ip-camera": "tpl_wf19_ip_camera",
    "workflow-20-inspection": "tpl_wf20_inspection",
    "custom-workshop-zone": "tpl_custom_workshop_zone",
    "custom-warehouse-exit": "tpl_custom_warehouse_exit",
    "ai-agent-safety-auditor": "tpl_ai_cctv_pro",
    "web_cv_studio": "tpl_web_cv_studio"
}

DASHBOARD_TO_WORKFLOW_MAP: dict[str, str] = {v: k for k, v in WORKFLOW_TO_DASHBOARD_MAP.items()}


def get_all_dashboard_template_meta() -> list[dict[str, Any]]:
    """Return comprehensive metadata for all 43 paired dashboard templates."""
    return [
        {
            "id": "tpl_smart_parking",
            "name": "Smart Parking Lot & Multi-Slot Occupancy Hub",
            "workflow_id": "smart_parking_management",
            "category": "Smart City & Parkir",
            "badge": "🚗 ULTRALYTICS PARKING",
            "icon": "navigation",
            "description": "Monitoring multi-slot parkir real-time (P1..Pn) dengan grid slot interaktif, rasio okupansi, waktu parkir, dan peringatan slot penuh."
        },
        {
            "id": "tpl_retail_queue_ultralytics",
            "name": "Ultralytics Queue & Customer Wait-Time Manager",
            "workflow_id": "retail_queue_management",
            "category": "Ritel & Supermarket",
            "badge": "🚶 ULTRALYTICS QUEUE",
            "icon": "users",
            "description": "Analisis panjang antrean kasir, taksiran waktu tunggu pembeli, status kepadatan (LOW/MEDIUM/OVERLOADED), dan alert antrean membludak."
        },
        {
            "id": "tpl_ai_gym_ergonomic",
            "name": "AI Gym Repetition & Ergonomic Safety Auditor",
            "workflow_id": "ai_gym_ergonomic",
            "category": "K3 & Olahraga",
            "badge": "🏋️ ULTRALYTICS GYM",
            "icon": "activity",
            "description": "Pelacak repetisi latihan fisik, pengukur busur sudut sendi real-time, indikator gerakan UP/DOWN, dan audit postur ergonomi K3."
        },
        {
            "id": "tpl_driver_blindspot_vision",
            "name": "Vision Eye 360° Sightline & Driver Blind-Spot Radar",
            "workflow_id": "driver_blindspot_vision",
            "category": "Logistik & Transportasi",
            "badge": "🎯 ULTRALYTICS VISION EYE",
            "icon": "eye",
            "description": "Radar 360 derajat garis pandang pengamat, deteksi objek berbahaya di titik buta kendaraan berat, dan alarm perimeter tabrakan."
        },
        {
            "id": "tpl_live_analytics_hud",
            "name": "Live Video Analytics HUD & Telemetry Speedometer",
            "workflow_id": "live_analytics_hud",
            "category": "Visualisasi & Anotasi",
            "badge": "📈 ULTRALYTICS HUD",
            "icon": "gauge",
            "description": "Dial gauge speedometer, grafik telemetri live, tren laju produksi, dan statistik inferensi vision langsung pada dashboard."
        },
        {
            "id": "tpl_web_cv_studio",
            "name": "Web Computer Vision Studio (Streamlit Style)",
            "workflow_id": "web_cv_studio",
            "category": "Web Computer Vision & Analisis Interaktif",
            "badge": "⚡ WEB CV & STREAMLIT",
            "icon": "layout-template",
            "description": "Aplikasi Web Computer Vision interaktif: Media Input Controller (upload gambar/video), Vision Result Viewer beranotasi, Tabel Hasil Konfiden, dan Tabel Kustom Analitik."
        },
        {
            "id": "tpl_ai_cctv_pro",
            "name": "AI CCTV PRO — Security Command Center",
            "workflow_id": "ai-agent-safety-auditor",
            "category": "Keamanan Siber & Pengawasan Kritis",
            "badge": "⭐ FLAGSHIP PRO",
            "icon": "shield-check",
            "description": "Pusat kendali pengawasan AI tingkat tinggi: Video Wall 2x2 dengan deteksi intrusi, audit K3, donat okupansi, dan telemetri sistem."
        },
        {
            "id": "tpl_traffic_flow",
            "name": "Smart Traffic Flow & Highway Telemetry",
            "workflow_id": "traffic_flow_counter",
            "category": "Transportasi & Jalan Raya",
            "badge": "🚦 Lalu Lintas",
            "icon": "truck",
            "description": "Pemantauan lalu lintas jalan raya, deteksi kendaraan, estimasi kecepatan, volume per lajur, dan log kepadatan simpang kota."
        },
        {
            "id": "tpl_restaurant_dwell",
            "name": "Restaurant Table Occupancy & Dining Dwell Hub",
            "workflow_id": "restaurant_table_occupancy",
            "category": "F&B & Hospitality",
            "badge": "🍽️ Restoran",
            "icon": "coffee",
            "description": "Pelacakan okupansi meja, durasi makan pengunjung (dwell time), pergantian meja, dan antrean kasir."
        },
        {
            "id": "tpl_assembly_cycle",
            "name": "Industrial Assembly Line & Workshop Cycle Timer",
            "workflow_id": "assembly_workshop_cycle_timer",
            "category": "Manufaktur & Pabrik",
            "badge": "🏭 Manufaktur",
            "icon": "cpu",
            "description": "Pengendali waktu siklus stasiun perakitan, estimasi efisiensi OEE, pencegahan bottleneck, dan rekap unit QC."
        },
        {
            "id": "tpl_warehouse_safety",
            "name": "Warehouse Logistics Dock & Forklift Safety Guard",
            "workflow_id": "warehouse_forklift_safety_guard",
            "category": "Logistik & Pergudangan",
            "badge": "🛡️ K3 Gudang",
            "icon": "shield",
            "description": "Audit keselamatan kerja K3, pemantauan jarak aman forklift, kepatuhan helm & rompi, dan batas tinggi tumpukan."
        },
        {
            "id": "tpl_retail_queue",
            "name": "Retail Store Queue Length & Customer Hotspot Hub",
            "workflow_id": "retail_checkout_queue_monitor",
            "category": "Ritel & Supermarket",
            "badge": "🛒 Ritel",
            "icon": "shopping-cart",
            "description": "Deteksi panjang antrean kasir, taksiran waktu tunggu pembeli, kepadatan lorong etalase, dan peringatan buka kasir."
        },
        {
            "id": "tpl_workshop_bay",
            "name": "Workshop Bay Activity & Active Station Monitor",
            "workflow_id": "workshop_bay_activity",
            "category": "Operasional Bengkel",
            "badge": "🔧 Bengkel",
            "icon": "tool",
            "description": "Pengawasan aktivitas bay workshop mekanik, durasi pengerjaan aktif vs menganggur, dan utilisasi bay bengkel."
        },
        {
            "id": "tpl_warehouse_gate",
            "name": "Warehouse Gate Exit & Loading Dispatch Tracker",
            "workflow_id": "warehouse_gate_exit",
            "category": "Logistik & Pergudangan",
            "badge": "🚪 Pintu Keluar",
            "icon": "log-out",
            "description": "Verifikasi pelepasan barang di pintu gerbang gudang, deteksi palet keluar, dan pencocokan dispatch log."
        },
        {
            "id": "tpl_bottle_inspection",
            "name": "Automated Bottle QC Visual Inspection Station",
            "workflow_id": "bottle_visual_inspection",
            "category": "Kontrol Kualitas (QC)",
            "badge": "🍾 QC Botol",
            "icon": "check-circle",
            "description": "Inspeksi visual botol produksi: tutup botol miring, volume cairan kurang, label cacat, dan rasio reject."
        },
        {
            "id": "tpl_preprocessing",
            "name": "Video Preprocessing & Dynamic Frame Optimizer",
            "workflow_id": "preprocessing",
            "category": "Prapemrosesan Video",
            "badge": "⚙️ Preprocess",
            "icon": "sliders",
            "description": "Optimasi resolusi, normalisasi warna, dan pengurangan noise frame untuk pipeline inferensi edge AI."
        },
        {
            "id": "tpl_rfdetr_detection",
            "name": "RF-DETR Transformer Detection Command Station",
            "workflow_id": "rfdetr_detection",
            "category": "Deteksi Objek AI",
            "badge": "🤖 Transformer",
            "icon": "target",
            "description": "Dashboard deteksi real-time menggunakan transformer RF-DETR dengan skor konfiden tinggi dan bounding box akurat."
        },
        {
            "id": "tpl_filter_counter",
            "name": "Multi-Class Filter Counter & Crossing Telemetry",
            "workflow_id": "filter_counter",
            "category": "Penghitungan Objek",
            "badge": "🔢 Counter",
            "icon": "hash",
            "description": "Pemisahan kelas kendaraan/orang, garis hitung dwiarah (masuk/keluar), dan akumulasi volume kumulatif."
        },
        {
            "id": "tpl_motion_detection",
            "name": "Motion Detection & Perimeter Intrusion Guard",
            "workflow_id": "motion_detection",
            "category": "Keamanan Siber & Fisik",
            "badge": "🚨 Gerakan",
            "icon": "bell",
            "description": "Deteksi pergerakan perimeter sensitif, filter angin/bayangan, alarm intrusi, dan riwayat perekaman kejadian."
        },
        {
            "id": "tpl_image_enhancement",
            "name": "Low-Light Image Enhancement & De-Noise Studio",
            "workflow_id": "image_enhancement",
            "category": "Prapemrosesan Video",
            "badge": "✨ Peningkatan",
            "icon": "sun",
            "description": "Peningkatan pencahayaan malam/gelap CLAHE, de-noise adaptif, dan ketajaman kontras video CCTV."
        },
        {
            "id": "tpl_branching_if_else",
            "name": "Conditional Logic & Multi-Branch Router Hub",
            "workflow_id": "branching_if_else",
            "category": "Logika & Alur",
            "badge": "🔀 Percabangan",
            "icon": "git-branch",
            "description": "Pemilahan alur berdasarkan kondisi deteksi (True/False routing), filter kelas, dan dispatch event spesifik."
        },
        {
            "id": "tpl_wf01_detection",
            "name": "Workflow 01 — Basic Object Detection Hub",
            "workflow_id": "workflow-01-detection",
            "category": "Deteksi Dasar",
            "badge": "🎯 Deteksi",
            "icon": "target",
            "description": "Dasbor inspeksi deteksi objek umum dengan metrik akurasi kelas dan pratinjau kamera utama."
        },
        {
            "id": "tpl_wf02_filter_count",
            "name": "Workflow 02 — Class Filter & Area Counter",
            "workflow_id": "workflow-02-filter-count",
            "category": "Filter & Counter",
            "badge": "🔍 Filter",
            "icon": "filter",
            "description": "Penyaringan kelas objek terpilih dan penghitungan volume area dengan batas ambang aman."
        },
        {
            "id": "tpl_wf03_tracking_line",
            "name": "Workflow 03 — Multi-Object Tracking & Line Counter",
            "workflow_id": "workflow-03-tracking-line",
            "category": "Tracking & Jalur",
            "badge": "📈 Tracking",
            "icon": "activity",
            "description": "Pelacakan objek persisten dengan garis lintasan In/Out dan grafik volume per jam."
        },
        {
            "id": "tpl_wf04_dwell_privacy",
            "name": "Workflow 04 — Zone Dwell Time & Privacy Blur",
            "workflow_id": "workflow-04-dwell-privacy",
            "category": "Privasi & Zona",
            "badge": "🛡️ Privasi",
            "icon": "eye-off",
            "description": "Pemantauan durasi menetap (dwell time) dengan sensor penyamaran privasi wajah/badan otomatis."
        },
        {
            "id": "tpl_wf05_segmentation",
            "name": "Workflow 05 — Polygon Instance Segmentation",
            "workflow_id": "workflow-05-segmentation",
            "category": "Segmentasi AI",
            "badge": "🧩 Poligon",
            "icon": "pie-chart",
            "description": "Segmentasi instan berbasis poligon piksel dengan kalkulasi cakupan area permukaan."
        },
        {
            "id": "tpl_wf06_crop_classify",
            "name": "Workflow 06 — Object Crop & Secondary Classification",
            "workflow_id": "workflow-06-crop-classify",
            "category": "Klasifikasi Ganda",
            "badge": "✂️ Crop AI",
            "icon": "crop",
            "description": "Pemotongan objek otomatis dan inferensi klasifikasi sekunder dengan galeri thumbnail langsung."
        },
        {
            "id": "tpl_wf07_if_else",
            "name": "Workflow 07 — Conditional If/Else Logic Decision",
            "workflow_id": "workflow-07-if-else",
            "category": "Logika Kondisi",
            "badge": "⚡ Gerbang Logika",
            "icon": "git-commit",
            "description": "Keputusan logika biner PASS/FAIL berdasarkan kondisi deteksi dengan status indikator visual."
        },
        {
            "id": "tpl_wf08_roi",
            "name": "Workflow 08 — Multi-ROI Region of Interest Filter",
            "workflow_id": "workflow-08-roi",
            "category": "Multi-Zona ROI",
            "badge": "📐 Multi-ROI",
            "icon": "grid",
            "description": "Pemantauan tiga area ROI berbeda secara simultan dengan perbandingan densitas objek."
        },
        {
            "id": "tpl_wf09_conditions",
            "name": "Workflow 09 — Multi-Criteria Complex Logic Evaluator",
            "workflow_id": "workflow-09-conditions",
            "category": "Evaluator Logika",
            "badge": "🔬 Komposit",
            "icon": "cpu",
            "description": "Evaluasi kondisi multi-kriteria kompleks dengan status aturan dan log kepatuhan SOP."
        },
        {
            "id": "tpl_wf10_transform",
            "name": "Workflow 10 — Spatial Transform & Perspective Projector",
            "workflow_id": "workflow-10-transform",
            "category": "Transformasi Spasial",
            "badge": "🗺️ BEV Warp",
            "icon": "compass",
            "description": "Proyeksi bidang datar bird-eye-view (BEV) dan pemetaan koordinat posisi tanah aktual."
        },
        {
            "id": "tpl_wf11_enhance",
            "name": "Workflow 11 — Advanced Image Enhancement & Equalizer",
            "workflow_id": "workflow-11-enhance",
            "category": "Prapemrosesan Video",
            "badge": "🎛️ Equalizer",
            "icon": "sliders",
            "description": "Studio ekualisasi frekuensi citra, penajaman tepi, dan optimasi kontras dinamis."
        },
        {
            "id": "tpl_wf12_calibration",
            "name": "Workflow 12 — Camera Lens Calibration & Undistortion",
            "workflow_id": "workflow-12-calibration",
            "category": "Kalibrasi Kamera",
            "badge": "📏 Kalibrasi",
            "icon": "maximize",
            "description": "Koreksi distorsi lensa sudut lebar (fisheye) dan kalkulasi parameter intrinsik kamera."
        },
        {
            "id": "tpl_wf13_motion",
            "name": "Workflow 13 — Optical Flow & Dynamic Motion Sentry",
            "workflow_id": "workflow-13-motion",
            "category": "Vektor Gerak",
            "badge": "🌊 Optical Flow",
            "icon": "wind",
            "description": "Analisis intensitas dan arah vektor pergerakan partikel dengan pengukur sudut kompas."
        },
        {
            "id": "tpl_wf14_sampling_slicer",
            "name": "Workflow 14 — Frame Rate Slicer & Smart Sampler",
            "workflow_id": "workflow-14-sampling-slicer",
            "category": "SAHI Slicing",
            "badge": "🍱 SAHI Tiling",
            "icon": "layers",
            "description": "Inferensi berpetak SAHI untuk deteksi objek mikro dan pemangkasan frame komputasi."
        },
        {
            "id": "tpl_wf15_barcode",
            "name": "Workflow 15 — Barcode & QR Code High-Speed Scanner",
            "workflow_id": "workflow-15-barcode",
            "category": "Pemindai Barcode",
            "badge": "🏷️ Barcode/QR",
            "icon": "maximize-2",
            "description": "Pemindaian barcode dan QR code jalur konveyor berkecepatan tinggi dengan riwayat SKU."
        },
        {
            "id": "tpl_wf16_event_controls",
            "name": "Workflow 16 — Event Dispatcher & Webhook Trigger",
            "workflow_id": "workflow-16-event-controls",
            "category": "Integrasi & Event",
            "badge": "📡 Webhook",
            "icon": "radio",
            "description": "Pusat pengendali pengiriman event webhook, notifikasi alarm, dan log HTTP payload."
        },
        {
            "id": "tpl_wf17_python_script",
            "name": "Workflow 17 — Custom Python Scripting Node Hub",
            "workflow_id": "workflow-17-python-script",
            "category": "Skrip Kustom",
            "badge": "🐍 Python Hub",
            "icon": "code",
            "description": "Konsol telemetri eksekusi skrip Python kustom, pemantauan latensi, dan konsol output."
        },
        {
            "id": "tpl_wf18_output",
            "name": "Workflow 18 — Multi-Channel Video & Stream Output",
            "workflow_id": "workflow-18-output",
            "category": "Distribusi Video",
            "badge": "📺 Multi-Output",
            "icon": "cast",
            "description": "Distribusi multi-saluran penyiaran video (RTSP/WebRTC) dengan telemetri kesehatan bitrate."
        },
        {
            "id": "tpl_wf19_ip_camera",
            "name": "Workflow 19 — Enterprise RTSP IP Camera Manager",
            "workflow_id": "workflow-19-ip-camera",
            "category": "Manajemen Kamera",
            "badge": "📹 IP Camera",
            "icon": "video",
            "description": "Pengawasan kondisi jaringan RTSP, latency ping, rekoneksi otomatis, dan kesehatan buffer."
        },
        {
            "id": "tpl_wf20_inspection",
            "name": "Workflow 20 — Industrial Surface & Part QC Inspector",
            "workflow_id": "workflow-20-inspection",
            "category": "Inspeksi Permukaan",
            "badge": "🔍 Surface QC",
            "icon": "check-square",
            "description": "Inspeksi cacat permukaan logam/komponen industri dengan skor keparahan dan tabel konfiden."
        },
        {
            "id": "tpl_custom_workshop_zone",
            "name": "Custom Workshop Zone Activity Timer Hub",
            "workflow_id": "custom-workshop-zone",
            "category": "Zona Workshop",
            "badge": "⏱️ Zona Bengkel",
            "icon": "clock",
            "description": "Pencatat durasi kerja aktif multi-zona poligon pada area servis mekanik workshop."
        },
        {
            "id": "tpl_custom_warehouse_exit",
            "name": "Custom Warehouse Exit Event Dispatcher",
            "workflow_id": "custom-warehouse-exit",
            "category": "Gerbang Gudang",
            "badge": "🚪 Gerbang Keluar",
            "icon": "external-link",
            "description": "Deteksi transisi keluar gerbang gudang dan pencatatan riwayat dispatch barang ke ERP."
        }
    ]


def build_template_layout(template_id: str, project_id: str) -> dict[str, Any]:
    """Build a completely distinct, domain-crafted dashboard layout for each template."""
    clean_id = "".join(c for c in project_id if c.isalnum() or c in ("-", "_")).strip() or "default"

    # =========================================================================
    # 1. SMART PARKING MANAGEMENT
    # =========================================================================
    if template_id == "tpl_smart_parking":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Smart Parking Lot & Multi-Slot Occupancy Hub",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080D19"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "SMART PARKING MANAGEMENT", "subtitle": "Real-time Multi-Slot Occupancy & ANPR Monitoring", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_parking_grid", "type": "parking_lot_grid", "x": 20, "y": 70, "w": 480, "h": 360, "z": 2,
                    "config": {
                        "title": "Ketersediaan Slot Parkir (Area Barat)",
                        "slots": [
                            {"id": "P1", "label": "Slot 1 (VIP)", "status": "occupied", "vehicle": "B 1234 CD"},
                            {"id": "P2", "label": "Slot 2", "status": "free", "vehicle": ""},
                            {"id": "P3", "label": "Slot 3", "status": "occupied", "vehicle": "D 5678 EF"},
                            {"id": "P4", "label": "Slot 4", "status": "free", "vehicle": ""},
                            {"id": "P5", "label": "Slot 5", "status": "free", "vehicle": ""},
                            {"id": "P6", "label": "Slot 6", "status": "occupied", "vehicle": "B 9999 Z"}
                        ],
                        "metricOccupancyKey": "parking_occupancy_pct"
                    }
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 520, "y": 70, "w": 900, "h": 500, "z": 2,
                    "config": {"cameraLabel": "CCTV Utama Lapangan Parkir & Gerbang", "streamId": "cam_parking_main", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_kpi_occ", "type": "stat_kpi_card", "x": 20, "y": 445, "w": 230, "h": 125, "z": 2,
                    "config": {"title": "TINGKAT OKUPANSI", "value": "50%", "icon": "percent", "sublabel": "3 dari 6 Slot Terisi", "accent": "#00E5FF", "metricKey": "parking_occupancy_pct"}
                },
                {
                    "id": "w_kpi_free", "type": "stat_kpi_card", "x": 270, "y": 445, "w": 230, "h": 125, "z": 2,
                    "config": {"title": "SLOT KOSONG", "value": 3, "icon": "check-circle", "sublabel": "Tersedia Masuk", "accent": "#10B981", "metricKey": "parking_free_count"}
                },
                {
                    "id": "w_trend", "type": "trend_chart", "x": 20, "y": 590, "w": 680, "h": 340, "z": 2,
                    "config": {"title": "Grafik Fluktuasi Parkir per Jam", "metricKey": "parking_occupancy_pct", "chartType": "line", "rangeHours": 24}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 720, "y": 590, "w": 480, "h": 340, "z": 2,
                    "config": {"title": "Log Kendaraan Masuk & Keluar", "maxRows": 20, "autoScroll": True, "showFilter": True}
                },
                {
                    "id": "w_excel", "type": "excel_export_btn", "x": 1220, "y": 590, "w": 200, "h": 50, "z": 2,
                    "config": {"label": "Unduh Rekap (.xlsx)", "includeEvents": True, "includeMetrics": True}
                }
            ]
        }

    # =========================================================================
    # 2. RETAIL QUEUE MANAGEMENT (ULTRALYTICS)
    # =========================================================================
    if template_id == "tpl_retail_queue_ultralytics":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Ultralytics Queue & Customer Wait-Time Manager",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080D19"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "RETAIL QUEUE & WAIT-TIME ANALYZER", "subtitle": "Customer Wait-Time & Counter Optimization", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_queue_status", "type": "queue_status_widget", "x": 20, "y": 70, "w": 480, "h": 320, "z": 2,
                    "config": {
                        "title": "Status Antrean Kasir Utama",
                        "queueMetricKey": "queue_count",
                        "avgWaitMetricKey": "queue_avg_wait_sec",
                        "maxWaitMetricKey": "queue_max_wait_sec",
                        "maxCapacity": 10
                    }
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 520, "y": 70, "w": 900, "h": 500, "z": 2,
                    "config": {"cameraLabel": "Kamera Pengawas Jalur Antrean Kasir", "streamId": "cam_queue", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_kpi_wait", "type": "stat_kpi_card", "x": 20, "y": 410, "w": 230, "h": 160, "z": 2,
                    "config": {"title": "RATA-RATA TUNGGU", "value": "1m 35s", "icon": "clock", "sublabel": "Sesuai Standar Layanan", "accent": "#00E5FF", "metricKey": "queue_avg_wait_sec"}
                },
                {
                    "id": "w_kpi_bottleneck", "type": "stat_kpi_card", "x": 270, "y": 410, "w": 230, "h": 160, "z": 2,
                    "config": {"title": "STATUS BOTTLENECK", "value": "NORMAL", "icon": "check-circle", "sublabel": "Kasir Beroperasi Cepat", "accent": "#10B981", "metricKey": "queue_bottleneck_status"}
                },
                {
                    "id": "w_trend", "type": "trend_chart", "x": 20, "y": 590, "w": 680, "h": 340, "z": 2,
                    "config": {"title": "Grafik Fluktuasi Panjang Antrean", "metricKey": "queue_count", "chartType": "line", "rangeHours": 12}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 720, "y": 590, "w": 700, "h": 340, "z": 2,
                    "config": {"title": "Log Peringatan Antrean Membludak", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 3. AI GYM & ERGONOMIC POSTURE AUDITOR
    # =========================================================================
    if template_id == "tpl_ai_gym_ergonomic":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "AI Gym Repetition & Ergonomic Safety Auditor",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080D19"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "AI GYM & ERGONOMIC POSTURE AUDITOR", "subtitle": "Real-time Joint Angle & Repetition Counter", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_gym", "type": "ai_gym_rep_widget", "x": 20, "y": 70, "w": 460, "h": 340, "z": 2,
                    "config": {
                        "title": "Pelacak Repetisi & Sudut Sendi",
                        "exerciseType": "squat",
                        "repMetricKey": "gym_rep_count",
                        "stageMetricKey": "gym_current_stage",
                        "angleMetricKey": "gym_current_angle",
                        "targetReps": 25
                    }
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 500, "y": 70, "w": 920, "h": 510, "z": 2,
                    "config": {"cameraLabel": "Kamera Pose & Analisis Ergonomi K3", "streamId": "cam_gym", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_kpi_reps", "type": "stat_kpi_card", "x": 20, "y": 430, "w": 220, "h": 150, "z": 2,
                    "config": {"title": "TOTAL REPETISI", "value": 18, "icon": "activity", "sublabel": "Target: 25 Reps", "accent": "#22C55E", "metricKey": "gym_rep_count"}
                },
                {
                    "id": "w_kpi_angle", "type": "stat_kpi_card", "x": 260, "y": 430, "w": 220, "h": 150, "z": 2,
                    "config": {"title": "SUDUT SENDI", "value": "145°", "icon": "compass", "sublabel": "Rentang Aman SOP", "accent": "#00E5FF", "metricKey": "gym_current_angle"}
                },
                {
                    "id": "w_trend", "type": "trend_chart", "x": 20, "y": 600, "w": 680, "h": 330, "z": 2,
                    "config": {"title": "Grafik Ritme & Sudut Sendi Latihan", "metricKey": "gym_current_angle", "chartType": "line", "rangeHours": 1}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 720, "y": 600, "w": 700, "h": 330, "z": 2,
                    "config": {"title": "Log Audit Siklus & Peringatan Postur", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 4. VISION EYE 360° SIGHTLINE & BLIND-SPOT RADAR
    # =========================================================================
    if template_id in ("tpl_driver_blindspot", "tpl_driver_blindspot_vision"):
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Vision Eye 360° Sightline & Driver Blind-Spot Radar",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080D19"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "VISION EYE 360° SIGHTLINE & BLIND-SPOT RADAR", "subtitle": "Driver Assistance & Heavy Equipment Proximity Alert", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_radar", "type": "vision_eye_radar_widget", "x": 20, "y": 70, "w": 460, "h": 380, "z": 2,
                    "config": {
                        "title": "Radar 360° & Sektor Titik Buta",
                        "observerLabel": "Forklift / Truk Tambang",
                        "dangerMetricKey": "ve_danger_count",
                        "blindSpotMetricKey": "ve_blindspot_count"
                    }
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 500, "y": 70, "w": 920, "h": 500, "z": 2,
                    "config": {"cameraLabel": "Kamera Pandang Luas Operator & Titik Buta", "streamId": "cam_vision_eye", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_kpi_danger", "type": "stat_kpi_card", "x": 20, "y": 470, "w": 220, "h": 100, "z": 2,
                    "config": {"title": "OBJEK BAHAYA", "value": 1, "icon": "alert-triangle", "sublabel": "Perimeter Kritis <2m", "accent": "#EF4444", "metricKey": "ve_danger_count"}
                },
                {
                    "id": "w_kpi_blind", "type": "stat_kpi_card", "x": 260, "y": 470, "w": 220, "h": 100, "z": 2,
                    "config": {"title": "DALAM TITIK BUTA", "value": 1, "icon": "eye-off", "sublabel": "Sudut 120°-240°", "accent": "#F59E0B", "metricKey": "ve_blindspot_count"}
                },
                {
                    "id": "w_alerts", "type": "active_alerts_list", "x": 20, "y": 590, "w": 460, "h": 340, "z": 2,
                    "config": {
                        "title": "ALARM PERINGATAN KEDEKATAN",
                        "alerts": [
                            {"level": "CRITICAL", "title": "Personil mendekati area blind-spot belakang", "loc": "Zona Belakang Kiri"},
                            {"level": "WARNING", "title": "Palet kayu di batas perimeter bahaya 1.8m", "loc": "Zona Samping Kanan"}
                        ]
                    }
                },
                {
                    "id": "w_table", "type": "event_table", "x": 500, "y": 590, "w": 920, "h": 340, "z": 2,
                    "config": {"title": "Log Kejadian & Alarm Titik Buta Kendaraan", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 5. LIVE VIDEO ANALYTICS HUD & TELEMETRY SPEEDOMETER
    # =========================================================================
    if template_id == "tpl_live_analytics_hud":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Live Video Analytics HUD & Telemetry Speedometer",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080D19"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "REAL-TIME VIDEO ANALYTICS & TELEMETRY HUD", "subtitle": "Live Performance Speedometer & Trend Line Visualizer", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_gauge", "type": "live_gauge_meter", "x": 20, "y": 70, "w": 440, "h": 280, "z": 2,
                    "config": {
                        "title": "Speedometer Laju Produksi / OEE",
                        "metricKey": "analytics_speed_rate",
                        "unit": "Unit/Mnt",
                        "minVal": 0,
                        "maxVal": 120,
                        "warningVal": 65,
                        "dangerVal": 95,
                        "defaultValue": 78
                    }
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 480, "y": 70, "w": 940, "h": 500, "z": 2,
                    "config": {"cameraLabel": "CCTV Utama dengan Live Telemetry HUD Overlay", "streamId": "cam_hud", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_kpi_fps", "type": "stat_kpi_card", "x": 20, "y": 370, "w": 210, "h": 110, "z": 2,
                    "config": {"title": "INFERENCE FPS", "value": "28.4", "icon": "zap", "sublabel": "Ultralytics Engine", "accent": "#00E5FF", "metricKey": "system_fps"}
                },
                {
                    "id": "w_kpi_throughput", "type": "stat_kpi_card", "x": 250, "y": 370, "w": 210, "h": 110, "z": 2,
                    "config": {"title": "TOTAL PROSES", "value": 1420, "icon": "check-circle", "sublabel": "Objek Hari Ini", "accent": "#10B981", "metricKey": "total_processed"}
                },
                {
                    "id": "w_trend", "type": "trend_chart", "x": 20, "y": 590, "w": 700, "h": 340, "z": 2,
                    "config": {"title": "Grafik Telemetri Tren Produksi Real-time", "metricKey": "analytics_speed_rate", "chartType": "line", "rangeHours": 12}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 740, "y": 590, "w": 680, "h": 340, "z": 2,
                    "config": {"title": "Log Telemetri Kejadian & Fluktuasi", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 6. WEB COMPUTER VISION STUDIO
    # =========================================================================
    if template_id == "tpl_web_cv_studio":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Interactive Web Computer Vision Studio",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 980, "background": "#080D19"},
            "widgets": [
                {
                    "id": "w_cv_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "WEB COMPUTER VISION STUDIO", "subtitle": "Interactive Inference & Analytics Platform", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cv_input", "type": "media_input_controller", "x": 20, "y": 70, "w": 440, "h": 460, "z": 2,
                    "config": {"title": "Media Input & Inference Controller", "defaultMode": "single_analysis", "confidence": 0.25, "iouThreshold": 0.45, "autoRunOnDrop": True}
                },
                {
                    "id": "w_cv_kpi", "type": "stat_kpi_card", "x": 20, "y": 545, "w": 440, "h": 105, "z": 2,
                    "config": {"title": "Total Objek Terdeteksi", "metricKey": "total_detected", "accent": "#0284c7", "icon": "users"}
                },
                {
                    "id": "w_cv_viewer", "type": "vision_result_viewer", "x": 480, "y": 70, "w": 940, "h": 580, "z": 2,
                    "config": {"title": "Hasil Visual Analisis AI (Annotated Result)", "showBeforeAfterSlider": True, "showZoomControls": True, "showDownloadBtn": True}
                },
                {
                    "id": "w_cv_table_conf", "type": "confidence_table", "x": 20, "y": 665, "w": 720, "h": 295, "z": 2,
                    "config": {"title": "Tabel Hasil Konfiden Deteksi (Detections)", "showCrops": True, "showScoreBar": True, "showBboxCoords": True, "showExportBtn": True}
                },
                {
                    "id": "w_cv_table_analytics", "type": "custom_analytics_table", "x": 760, "y": 665, "w": 660, "h": 295, "z": 2,
                    "config": {"title": "Tabel Kustom Analitik Alur Kerja", "showZoneSummary": True, "showClassCounter": True, "showExportBtn": True}
                }
            ]
        }

    # =========================================================================
    # 7. AI CCTV PRO (FLAGSHIP COMMAND CENTER)
    # =========================================================================
    if template_id in ("tpl_ai_cctv_pro", "default"):
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "AI CCTV PRO — Security Command Center",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 980, "background": "#080D19"},
            "widgets": [
                {
                    "id": "w_head_brand", "type": "custom_text", "x": 20, "y": 14, "w": 460, "h": 50, "z": 1,
                    "config": {"text": "🛡️ AI CCTV PRO — Command Center", "tag": "h1", "fontSize": 19, "color": "#00E5FF", "subtitle": "AI-Powered Intelligent Surveillance Platform"}
                },
                {
                    "id": "w_head_sys_status", "type": "status_badge", "x": 730, "y": 14, "w": 290, "h": 48, "z": 1,
                    "config": {"label": "SYSTEM STATUS: All operational", "status": "online", "shift": "● Live Pipeline Active"}
                },
                {
                    "id": "w_head_alert_status", "type": "status_badge", "x": 1035, "y": 14, "w": 190, "h": 48, "z": 1,
                    "config": {"label": "3 CRITICAL ALERTS", "status": "danger", "shift": "Tindakan Diperlukan"}
                },
                {
                    "id": "w_head_export_excel", "type": "excel_export_btn", "x": 1240, "y": 14, "w": 180, "h": 48, "z": 1,
                    "config": {"label": "Unduh Rekap Excel", "includeEvents": True, "includeMetrics": True}
                },
                {
                    "id": "w_stat_cameras", "type": "stat_kpi_card", "x": 20, "y": 74, "w": 268, "h": 86, "z": 2,
                    "config": {"title": "CAMERAS", "value": 24, "icon": "camera", "sublabel": "22 Online / 2 Offline", "accent": "#00E5FF", "metricKey": "cameras_online"}
                },
                {
                    "id": "w_stat_people", "type": "stat_kpi_card", "x": 303, "y": 74, "w": 268, "h": 86, "z": 2,
                    "config": {"title": "PEOPLE", "value": 128, "icon": "users", "sublabel": "Currently Detected", "accent": "#A855F7", "metricKey": "total_person"}
                },
                {
                    "id": "w_stat_entries", "type": "stat_kpi_card", "x": 586, "y": 74, "w": 268, "h": 86, "z": 2,
                    "config": {"title": "ENTRIES", "value": 74, "icon": "arrow-down-right", "sublabel": "Today's Entries", "accent": "#14B8A6", "metricKey": "today_entries"}
                },
                {
                    "id": "w_stat_exits", "type": "stat_kpi_card", "x": 869, "y": 74, "w": 268, "h": 86, "z": 2,
                    "config": {"title": "EXITS", "value": 31, "icon": "arrow-up-right", "sublabel": "Today's Exits", "accent": "#00E5FF", "metricKey": "today_exits"}
                },
                {
                    "id": "w_stat_active_alerts", "type": "stat_kpi_card", "x": 1152, "y": 74, "w": 268, "h": 86, "z": 2,
                    "config": {"title": "ACTIVE ALERTS", "value": 3, "icon": "alert-triangle", "sublabel": "Immediate Attention", "accent": "#EF4444", "metricKey": "active_alerts"}
                },
                {
                    "id": "w_matrix_cctv", "type": "cctv_player", "x": 20, "y": 174, "w": 1050, "h": 500, "z": 3,
                    "config": {"cameraLabel": "CCTV Command Video Feed", "streamId": "cam_main", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_active_alerts_panel", "type": "active_alerts_list", "x": 1085, "y": 174, "w": 335, "h": 500, "z": 3,
                    "config": {
                        "title": "ACTIVE CRITICAL ALERTS",
                        "alerts": [
                            {"level": "CRITICAL", "title": "Pelanggaran Helm Area Forklift", "loc": "Zona Loading Bay 02"},
                            {"level": "CRITICAL", "title": "Objek Tak Dikenal di Jalur Darurat", "loc": "Gerbang Barat"},
                            {"level": "WARNING", "title": "Kepadatan melebihi ambang batas", "loc": "Lobby Utama"}
                        ]
                    }
                },
                {
                    "id": "w_trend", "type": "trend_chart", "x": 20, "y": 690, "w": 700, "h": 270, "z": 4,
                    "config": {"title": "Grafik Tren Deteksi & Lalu Lintas Kejadian", "metricKey": "total_person", "chartType": "line", "rangeHours": 24}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 740, "y": 690, "w": 680, "h": 270, "z": 4,
                    "config": {"title": "Log Kejadian Terkini Real-time", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 8. SMART TRAFFIC FLOW
    # =========================================================================
    elif template_id == "tpl_traffic_flow":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Smart Traffic Flow & Highway Telemetry Center",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#070B14"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "SMART TRAFFIC FLOW & HIGHWAY TELEMETRY", "subtitle": "Klasifikasi Kendaraan Real-time, Gerbang Tol ANPR, dan Analitik Laju Aliran", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_gauge", "type": "live_gauge_meter", "x": 20, "y": 70, "w": 340, "h": 280, "z": 2,
                    "config": {"title": "Kecepatan Rata-rata Ruas Tol", "metricKey": "avg_speed", "min": 0, "max": 140, "unit": "km/h", "zones": [{"min": 0, "max": 60, "color": "#EF4444", "label": "Macet"}, {"min": 60, "max": 100, "color": "#10B981", "label": "Lancar"}, {"min": 100, "max": 140, "color": "#F59E0B", "label": "Ngebut"}]}
                },
                {
                    "id": "w_sc1", "type": "stat_kpi_card", "x": 20, "y": 365, "w": 340, "h": 110, "z": 2,
                    "config": {"title": "VOLUME KENDARAAN (24 JAM)", "value": 1248, "icon": "truck", "sublabel": "Unit Terhitung ANPR", "accent": "#38BDF8", "metricKey": "vehicle_count"}
                },
                {
                    "id": "w_sc2", "type": "stat_kpi_card", "x": 20, "y": 490, "w": 340, "h": 110, "z": 2,
                    "config": {"title": "PELANGGARAN BAHU JALAN", "value": 3, "icon": "alert-triangle", "sublabel": "Kasus Tertangkap Sensor", "accent": "#EF4444", "metricKey": "violation_shoulder"}
                },
                {
                    "id": "w_sc3", "type": "stat_kpi_card", "x": 20, "y": 615, "w": 340, "h": 110, "z": 2,
                    "config": {"title": "LAJU ALIRAN TRAFIK", "value": "18.2", "icon": "activity", "sublabel": "Mobil / Menit", "accent": "#F59E0B", "metricKey": "flow_rate"}
                },
                {
                    "id": "w_excel", "type": "excel_export_btn", "x": 20, "y": 740, "w": 340, "h": 45, "z": 2,
                    "config": {"label": "Unduh Rekap Lalu Lintas (.xlsx)", "includeEvents": True, "includeMetrics": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 380, "y": 70, "w": 700, "h": 430, "z": 3,
                    "config": {"cameraLabel": "Kamera Gerbang Masuk Tol ANPR & Bahu Jalan", "streamId": "cam_toll_in", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_chart", "type": "trend_chart", "x": 380, "y": 520, "w": 700, "h": 265, "z": 4,
                    "config": {"title": "Grafik Fluktuasi Volume Kendaraan (24 Jam)", "metricKey": "vehicle_count", "chartType": "line", "rangeHours": 24}
                },
                {
                    "id": "w_alerts", "type": "active_alerts_strip", "x": 1100, "y": 70, "w": 320, "h": 200, "z": 2,
                    "config": {"title": "Peringatan Lalu Lintas", "maxAlerts": 4, "autoDismiss": False}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 1100, "y": 285, "w": 320, "h": 500, "z": 4,
                    "config": {"title": "Tabel Plat Nomor & Klasifikasi", "maxRows": 30, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 9. RESTAURANT TABLE OCCUPANCY
    # =========================================================================
    elif template_id == "tpl_restaurant_dwell":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Restaurant Dining Analytics & Guest Dwell Hub",
            "theme": "dark",
            "canvas": {"width": 1400, "height": 940, "background": "#0F172A"},
            "widgets": [
                {
                    "id": "w_head", "type": "custom_text", "x": 20, "y": 15, "w": 680, "h": 55, "z": 1,
                    "config": {"text": "Restaurant Dining Analytics & Guest Dwell Monitor", "tag": "h1", "fontSize": 24, "color": "#F59E0B", "subtitle": "Pelacakan Meja Tamu, Durasi Makan, dan Efisiensi Pelayanan"}
                },
                {
                    "id": "w_badge", "type": "status_badge", "x": 1100, "y": 20, "w": 280, "h": 45, "z": 1,
                    "config": {"label": "Restoran Utama — Jam Makan Siang", "status": "online", "shift": "Layanan Penuh"}
                },
                {
                    "id": "w_sc1", "type": "stat_kpi_card", "x": 20, "y": 85, "w": 320, "h": 110, "z": 2,
                    "config": {"title": "OKUPANSI MEJA MAKAN", "value": "74.2%", "icon": "pie-chart", "sublabel": "Tingkat Keterisian Meja", "accent": "#F59E0B", "metricKey": "table_occupancy_pct"}
                },
                {
                    "id": "w_sc2", "type": "stat_kpi_card", "x": 360, "y": 85, "w": 320, "h": 110, "z": 2,
                    "config": {"title": "RATA-RATA DURASI MAKAN", "value": "42.5 m", "icon": "clock", "sublabel": "Waktu Singgah per Meja", "accent": "#10B981", "metricKey": "avg_dining_minutes"}
                },
                {
                    "id": "w_sc3", "type": "stat_kpi_card", "x": 700, "y": 85, "w": 320, "h": 110, "z": 2,
                    "config": {"title": "MEJA SIAP PAKAI", "value": 6, "icon": "check-circle", "sublabel": "Tersedia Langsung", "accent": "#38BDF8", "metricKey": "tables_ready"}
                },
                {
                    "id": "w_sc4", "type": "stat_kpi_card", "x": 1040, "y": 85, "w": 340, "h": 110, "z": 2,
                    "config": {"title": "WAITLIST TAMU", "value": 4, "icon": "users", "sublabel": "Menunggu Meja Kosong", "accent": "#EF4444", "metricKey": "waitlist_count"}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 215, "w": 780, "h": 440, "z": 3,
                    "config": {"cameraLabel": "Kamera Ruang Makan Tengah (Meja 1-12)", "streamId": "cam_dining_hall", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_donut", "type": "donut_occupancy", "x": 820, "y": 215, "w": 560, "h": 260, "z": 2,
                    "config": {"title": "Distribusi Okupansi Meja Restoran", "metricKey": "table_occupancy_pct", "occupiedLabel": "Terisi Makan", "freeLabel": "Kosong/Reserved"}
                },
                {
                    "id": "w_chart", "type": "trend_chart", "x": 820, "y": 490, "w": 560, "h": 260, "z": 4,
                    "config": {"title": "Grafik Perputaran Meja per Jam", "metricKey": "table_occupancy_pct", "chartType": "line", "rangeHours": 12}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 675, "w": 780, "h": 245, "z": 4,
                    "config": {"title": "Log Pergantian Meja & Tamu Selesai", "maxRows": 25, "autoScroll": True, "showFilter": True}
                },
                {
                    "id": "w_excel", "type": "excel_export_btn", "x": 820, "y": 765, "w": 560, "h": 45, "z": 2,
                    "config": {"label": "Unduh Laporan Resto (.xlsx)", "includeEvents": True, "includeMetrics": True}
                }
            ]
        }

    # =========================================================================
    # 10. ASSEMBLY WORKSHOP CYCLE TIMER
    # =========================================================================
    elif template_id == "tpl_assembly_cycle":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Industrial Assembly Line & Cycle Time Monitor",
            "theme": "dark",
            "canvas": {"width": 1480, "height": 960, "background": "#090D1A"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1480, "h": 56, "z": 1,
                    "config": {"title": "INDUSTRIAL ASSEMBLY LINE CYCLE TIMER", "subtitle": "Monitoring Takt Time & Ergonomi Pekerja Manufaktur", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 20, "y": 70, "w": 460, "h": 110, "z": 2,
                    "config": {"metricKey": "cycle_time_sec", "title": "Cycle Time Rata-rata", "unit": "Detik", "warningThreshold": 35, "dangerThreshold": 45, "defaultValue": 28.4}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 500, "y": 70, "w": 460, "h": 110, "z": 2,
                    "config": {"metricKey": "target_cycle_sec", "title": "Target Takt Time", "unit": "Detik", "warningThreshold": 30, "dangerThreshold": 40, "defaultValue": 30.0}
                },
                {
                    "id": "w_sc3", "type": "scorecard", "x": 980, "y": 70, "w": 480, "h": 110, "z": 2,
                    "config": {"metricKey": "units_completed", "title": "Total Unit Selesai Shift Ini", "unit": "Unit", "warningThreshold": 400, "dangerThreshold": 300, "defaultValue": 482}
                },
                {
                    "id": "w_cctv1", "type": "cctv_player", "x": 20, "y": 200, "w": 460, "h": 340, "z": 3,
                    "config": {"cameraLabel": "Kamera Stasiun Perakitan A", "streamId": "cam_line_a", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_cctv2", "type": "cctv_player", "x": 500, "y": 200, "w": 460, "h": 340, "z": 3,
                    "config": {"cameraLabel": "Kamera Stasiun Perakitan B", "streamId": "cam_line_b", "nodeId": "detector", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_gauge", "type": "live_gauge_meter", "x": 980, "y": 200, "w": 480, "h": 340, "z": 2,
                    "config": {"title": "Takt Time Compliance Speedometer", "metricKey": "cycle_time_sec", "min": 0, "max": 60, "unit": "detik", "zones": [{"min": 0, "max": 30, "color": "#10B981", "label": "Efisien"}, {"min": 30, "max": 45, "color": "#F59E0B", "label": "Warning"}, {"min": 45, "max": 60, "color": "#EF4444", "label": "Over Takt"}]}
                },
                {
                    "id": "w_chart", "type": "trend_chart", "x": 20, "y": 560, "w": 720, "h": 380, "z": 4,
                    "config": {"title": "Grafik Variasi Cycle Time per Siklus Kerja", "metricKey": "cycle_time_sec", "chartType": "line", "rangeHours": 8}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 760, "y": 560, "w": 700, "h": 380, "z": 4,
                    "config": {"title": "Log Siklus Selesai & Pelanggaran Takt Time", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 11. WAREHOUSE FORKLIFT SAFETY GUARD
    # =========================================================================
    elif template_id == "tpl_warehouse_safety":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Warehouse Safety Perimeter & Forklift Guard",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#0B0F19"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "WAREHOUSE SAFETY PERIMETER & FORKLIFT GUARD", "subtitle": "Deteksi Jarak Dekat Pejalan Kaki & Forklift di Persimpangan Blind-Spot", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_radar", "type": "vision_eye_radar_widget", "x": 20, "y": 70, "w": 440, "h": 460, "z": 2,
                    "config": {
                        "title": "360° Safety Proximity Radar",
                        "sweepSpeed": "medium",
                        "dangerThresholdMeters": 2.5,
                        "metricProximityKey": "forklift_min_distance",
                        "warningSector": {"startDeg": 45, "endDeg": 135}
                    }
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 480, "y": 70, "w": 640, "h": 460, "z": 3,
                    "config": {"cameraLabel": "Kamera Persimpangan Gudang & Jalur Forklift", "streamId": "cam_forklift_zone", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 1140, "y": 70, "w": 280, "h": 100, "z": 2,
                    "config": {"metricKey": "safety_breaches", "title": "Pelanggaran Jarak Aman", "unit": "Insiden", "warningThreshold": 3, "dangerThreshold": 6, "defaultValue": 1}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 1140, "y": 185, "w": 280, "h": 100, "z": 2,
                    "config": {"metricKey": "forklift_speed", "title": "Kecepatan Forklift", "unit": "km/h", "warningThreshold": 15, "dangerThreshold": 20, "defaultValue": 11.8}
                },
                {
                    "id": "w_sc3", "type": "scorecard", "x": 1140, "y": 300, "w": 280, "h": 100, "z": 2,
                    "config": {"metricKey": "pedestrians_in_zone", "title": "Pejalan Kaki di Jalur", "unit": "Orang", "warningThreshold": 1, "dangerThreshold": 3, "defaultValue": 0}
                },
                {
                    "id": "w_alerts", "type": "active_alerts_strip", "x": 1140, "y": 415, "w": 280, "h": 115, "z": 2,
                    "config": {"title": "Alarm Keamanan", "maxAlerts": 3, "autoDismiss": False}
                },
                {
                    "id": "w_chart", "type": "trend_chart", "x": 20, "y": 550, "w": 620, "h": 390, "z": 4,
                    "config": {"title": "Grafik Insiden Dekat (Near-Miss) per Jam", "metricKey": "safety_breaches", "chartType": "bar", "rangeHours": 24}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 660, "y": 550, "w": 760, "h": 390, "z": 4,
                    "config": {"title": "Log Peringatan Pelanggaran Proximity & Alarm", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 12. RETAIL QUEUE & CHECKOUT HOTSPOT
    # =========================================================================
    elif template_id == "tpl_retail_queue":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Retail Queue Checkout & Cashier Balancing Hub",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080F1E"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "RETAIL QUEUE CHECKOUT & CASHIER BALANCING", "subtitle": "Estimasi Waktu Tunggu, Distribusi Antrean Kasir, dan Rekomendasi Buka Jalur", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_queue", "type": "queue_status_widget", "x": 20, "y": 70, "w": 460, "h": 460, "z": 2,
                    "config": {
                        "title": "Status Antrean Kasir 1 - 4",
                        "maxThreshold": 5,
                        "metricQueueCountKey": "queue_length",
                        "metricWaitTimeKey": "avg_wait_minutes"
                    }
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 500, "y": 70, "w": 920, "h": 460, "z": 3,
                    "config": {"cameraLabel": "Kamera Antrean & Meja Kasir Supermarket", "streamId": "cam_checkout_area", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_sc1", "type": "stat_kpi_card", "x": 20, "y": 550, "w": 330, "h": 105, "z": 2,
                    "config": {"title": "TOTAL ANTREAN", "value": 7, "icon": "users", "sublabel": "Pelanggan Mengantre", "accent": "#00E5FF", "metricKey": "queue_length"}
                },
                {
                    "id": "w_sc2", "type": "stat_kpi_card", "x": 370, "y": 550, "w": 330, "h": 105, "z": 2,
                    "config": {"title": "ESTIMASI WAKTU TUNGGU", "value": "4.2 m", "icon": "clock", "sublabel": "Rata-rata Menunggu", "accent": "#10B981", "metricKey": "avg_wait_minutes"}
                },
                {
                    "id": "w_sc3", "type": "stat_kpi_card", "x": 720, "y": 550, "w": 330, "h": 105, "z": 2,
                    "config": {"title": "KASIR AKTIF DIBUKA", "value": 3, "icon": "check-circle", "sublabel": "Dari 4 Kasir Tersedia", "accent": "#38BDF8", "metricKey": "cashiers_active"}
                },
                {
                    "id": "w_sc4", "type": "stat_kpi_card", "x": 1070, "y": 550, "w": 350, "h": 105, "z": 2,
                    "config": {"title": "REKOMENDASI BUKA", "value": "Siaga Kasir 4", "icon": "alert-circle", "sublabel": "Tingkat Antrean Moderat", "accent": "#F59E0B", "metricKey": "queue_recommendation"}
                },
                {
                    "id": "w_chart", "type": "trend_chart", "x": 20, "y": 675, "w": 780, "h": 265, "z": 4,
                    "config": {"title": "Fluktuasi Panjang Antrean Sepanjang Hari", "metricKey": "queue_length", "chartType": "line", "rangeHours": 12}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 820, "y": 675, "w": 600, "h": 265, "z": 4,
                    "config": {"title": "Log Waktu Pelayanan Transaksi Kasir", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 13. WORKSHOP BAY ACTIVITY
    # =========================================================================
    elif template_id == "tpl_workshop_bay":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workshop Bay Activity & Active Station Monitor",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#070E1A"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "WORKSHOP BAY ACTIVITY MONITOR", "subtitle": "Stasiun Servis Kendaraan 1-5 & Durasi Mekanik Aktif", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv_bay1", "type": "cctv_player", "x": 20, "y": 70, "w": 680, "h": 400, "z": 2,
                    "config": {"cameraLabel": "Kamera Bay Servis 1 & 2 (Overhaul)", "streamId": "cam_bay_1_2", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_cctv_bay2", "type": "cctv_player", "x": 720, "y": 70, "w": 700, "h": 400, "z": 2,
                    "config": {"cameraLabel": "Kamera Bay Servis 3-5 (Quick Service)", "streamId": "cam_bay_3_5", "nodeId": "detector", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 20, "y": 485, "w": 260, "h": 115, "z": 2,
                    "config": {"metricKey": "bay_utilization_pct", "title": "Utilisasi Bay Aktif", "unit": "%", "warningThreshold": 70, "dangerThreshold": 50, "defaultValue": 84.0}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 300, "y": 485, "w": 260, "h": 115, "z": 2,
                    "config": {"metricKey": "avg_service_time_mins", "title": "Rata-rata Waktu Servis", "unit": "Menit", "warningThreshold": 60, "dangerThreshold": 90, "defaultValue": 38.5}
                },
                {
                    "id": "w_sc3", "type": "scorecard", "x": 580, "y": 485, "w": 260, "h": 115, "z": 2,
                    "config": {"metricKey": "mechanics_active", "title": "Mekanik Sedang Bekerja", "unit": "Orang", "warningThreshold": 3, "dangerThreshold": 1, "defaultValue": 7}
                },
                {
                    "id": "w_sc4", "type": "scorecard", "x": 860, "y": 485, "w": 260, "h": 115, "z": 2,
                    "config": {"metricKey": "vehicles_in_progress", "title": "Mobil Sedang Dikerjakan", "unit": "Unit", "warningThreshold": 2, "dangerThreshold": 1, "defaultValue": 4}
                },
                {
                    "id": "w_excel", "type": "excel_export_btn", "x": 1140, "y": 485, "w": 280, "h": 50, "z": 2,
                    "config": {"label": "Unduh Rekap Bengkel (.xlsx)", "includeEvents": True, "includeMetrics": True}
                },
                {
                    "id": "w_trend", "type": "trend_chart", "x": 20, "y": 620, "w": 700, "h": 320, "z": 3,
                    "config": {"title": "Grafik Jam Kerja Aktif per Bay (Jam)", "metricKey": "bay_utilization_pct", "chartType": "line", "rangeHours": 12}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 740, "y": 620, "w": 680, "h": 320, "z": 3,
                    "config": {"title": "Log Selesai Servis & Pergantian Mobil", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 14. WAREHOUSE GATE EXIT
    # =========================================================================
    elif template_id == "tpl_warehouse_gate":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Warehouse Gate Exit & Loading Dispatch Tracker",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#0A0D15"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "WAREHOUSE GATE EXIT & DISPATCH DISPATCHER", "subtitle": "Inside-to-Outside Transition & Barcode Matcher", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 880, "h": 490, "z": 2,
                    "config": {"cameraLabel": "CCTV Gerbang Keluar Truk Ekspedisi", "streamId": "cam_gate_exit", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_gauge", "type": "live_gauge_meter", "x": 920, "y": 70, "w": 500, "h": 240, "z": 2,
                    "config": {
                        "title": "Laju Dispatch Truk per Jam",
                        "metricKey": "gate_dispatch_rate",
                        "unit": "Truk/Jam",
                        "minVal": 0,
                        "maxVal": 30,
                        "warningVal": 15,
                        "dangerVal": 25,
                        "defaultValue": 12
                    }
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 920, "y": 325, "w": 240, "h": 110, "z": 2,
                    "config": {"metricKey": "pallets_dispatched_today", "title": "Palet Keluar Hari Ini", "unit": "Palet", "warningThreshold": 100, "dangerThreshold": 200, "defaultValue": 146}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 1180, "y": 325, "w": 240, "h": 110, "z": 2,
                    "config": {"metricKey": "erp_sync_success_pct", "title": "Sinkronisasi ERP SAP", "unit": "%", "warningThreshold": 95, "dangerThreshold": 90, "defaultValue": 100}
                },
                {
                    "id": "w_alerts", "type": "active_alerts_list", "x": 920, "y": 450, "w": 500, "h": 110, "z": 2,
                    "config": {
                        "title": "STATUS DISPATCH GERBANG",
                        "alerts": [
                            {"level": "INFO", "title": "Truk B 9120 WX lolos verifikasi gerbang keluar", "loc": "Gerbang Selatan 02"}
                        ]
                    }
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 580, "w": 1400, "h": 350, "z": 3,
                    "config": {"title": "Tabel Verifikasi Pelepasan Barang Gerbang & Pencocokan PO", "maxRows": 35, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 15. AUTOMATED BOTTLE QC INSPECTION
    # =========================================================================
    elif template_id == "tpl_bottle_inspection":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Automated Bottle QC Visual Inspection Station",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080C14"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "BOTTLE PACKAGING QC INSPECTOR", "subtitle": "High-Speed Cap, Label, and Fill-Level Automated Defect Inspection", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 20, "y": 70, "w": 260, "h": 110, "z": 2,
                    "config": {"metricKey": "qc_passed_count", "title": "Botol Lolos (Pass)", "unit": "Unit", "warningThreshold": 500, "dangerThreshold": 100, "defaultValue": 8420}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 300, "y": 70, "w": 260, "h": 110, "z": 2,
                    "config": {"metricKey": "qc_rejected_count", "title": "Botol Cacat (Reject)", "unit": "Unit", "warningThreshold": 20, "dangerThreshold": 50, "defaultValue": 14}
                },
                {
                    "id": "w_sc3", "type": "scorecard", "x": 580, "y": 70, "w": 260, "h": 110, "z": 2,
                    "config": {"metricKey": "qc_accuracy_pct", "title": "Tingkat Akurasi QC", "unit": "%", "warningThreshold": 99.0, "dangerThreshold": 98.0, "defaultValue": 99.83}
                },
                {
                    "id": "w_sc4", "type": "scorecard", "x": 860, "y": 70, "w": 260, "h": 110, "z": 2,
                    "config": {"metricKey": "conveyor_speed_bpm", "title": "Kecepatan Konveyor", "unit": "BPM", "warningThreshold": 120, "dangerThreshold": 80, "defaultValue": 150}
                },
                {
                    "id": "w_excel", "type": "excel_export_btn", "x": 1140, "y": 70, "w": 280, "h": 50, "z": 2,
                    "config": {"label": "Unduh Sertifikat QC (.xlsx)", "includeEvents": True, "includeMetrics": True}
                },
                {
                    "id": "w_cctv_cap", "type": "cctv_player", "x": 20, "y": 195, "w": 690, "h": 410, "z": 3,
                    "config": {"cameraLabel": "Kamera Inspeksi Tutup Botol & Segel", "streamId": "cam_bottle_cap", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_cctv_fill", "type": "cctv_player", "x": 730, "y": 195, "w": 690, "h": 410, "z": 3,
                    "config": {"cameraLabel": "Kamera Level Isi Cairan & Posisi Label", "streamId": "cam_bottle_fill", "nodeId": "detector", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_donut", "type": "donut_chart", "x": 20, "y": 620, "w": 450, "h": 320, "z": 3,
                    "config": {
                        "title": "SEBARAN CACAT BOTOL",
                        "segments": [
                            {"label": "Tutup Miring", "pct": 52, "color": "#EF4444"},
                            {"label": "Volume Kurang", "pct": 31, "color": "#F59E0B"},
                            {"label": "Label Cacat", "pct": 17, "color": "#3B82F6"}
                        ]
                    }
                },
                {
                    "id": "w_table", "type": "event_table", "x": 490, "y": 620, "w": 930, "h": 320, "z": 3,
                    "config": {"title": "Log Reject Pneupneumatic Ejector & Snapshot Cacat", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 16. PREPROCESSING & FRAME OPTIMIZER
    # =========================================================================
    elif template_id == "tpl_preprocessing":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Video Preprocessing & Dynamic Frame Optimizer",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#070B12"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "FRAME PREPROCESSING OPTIMIZER", "subtitle": "Noise Reduction, CLAHE Equalization & Dynamic Resizing", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_raw_feed", "type": "cctv_player", "x": 20, "y": 70, "w": 690, "h": 460, "z": 2,
                    "config": {"cameraLabel": "Input Stream Mentah (Raw 1080p)", "streamId": "cam_raw", "nodeId": "input", "showAnnotatedToggle": False, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_opt_feed", "type": "cctv_player", "x": 730, "y": 70, "w": 690, "h": 460, "z": 2,
                    "config": {"cameraLabel": "Frame Teroptimasi (Normalized & Denoised)", "streamId": "cam_opt", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 20, "y": 545, "w": 330, "h": 110, "z": 2,
                    "config": {"metricKey": "compression_ratio", "title": "Reduksi Ukuran Frame", "unit": "%", "warningThreshold": 30, "dangerThreshold": 10, "defaultValue": 58.2}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 370, "y": 545, "w": 330, "h": 110, "z": 2,
                    "config": {"metricKey": "preprocess_latency_ms", "title": "Latensi Preprocess", "unit": "ms", "warningThreshold": 8, "dangerThreshold": 15, "defaultValue": 3.4}
                },
                {
                    "id": "w_sc3", "type": "scorecard", "x": 720, "y": 545, "w": 330, "h": 110, "z": 2,
                    "config": {"metricKey": "snr_improvement_db", "title": "Peningkatan SNR", "unit": "dB", "warningThreshold": 5, "dangerThreshold": 2, "defaultValue": 8.7}
                },
                {
                    "id": "w_sc4", "type": "scorecard", "x": 1070, "y": 545, "w": 350, "h": 110, "z": 2,
                    "config": {"metricKey": "ai_inference_fps", "title": "FPS Inferensi AI", "unit": "FPS", "warningThreshold": 24, "dangerThreshold": 15, "defaultValue": 42.1}
                },
                {
                    "id": "w_trend", "type": "trend_chart", "x": 20, "y": 670, "w": 1400, "h": 270, "z": 3,
                    "config": {"title": "Grafik Efisiensi Throughput Frame & Kecepatan Komputasi (FPS)", "metricKey": "ai_inference_fps", "chartType": "line", "rangeHours": 12}
                }
            ]
        }

    # =========================================================================
    # 17. RF-DETR TRANSFORMER DETECTION
    # =========================================================================
    elif template_id == "tpl_rfdetr_detection":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "RF-DETR Transformer Detection Command Station",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080D1A"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "RF-DETR TRANSFORMER VISION COMMAND", "subtitle": "Real-time Multi-Query Transformer Detection Station", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 960, "h": 540, "z": 2,
                    "config": {"cameraLabel": "RF-DETR High-Accuracy Video Feed", "streamId": "cam_rfdetr", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 1000, "y": 70, "w": 420, "h": 115, "z": 2,
                    "config": {"metricKey": "rfdetr_mean_conf", "title": "Skor Konfiden Rata-rata", "unit": "%", "warningThreshold": 80, "dangerThreshold": 60, "defaultValue": 93.4}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 1000, "y": 200, "w": 420, "h": 115, "z": 2,
                    "config": {"metricKey": "rfdetr_queries_active", "title": "Query Objek Aktif", "unit": "Objek", "warningThreshold": 50, "dangerThreshold": 80, "defaultValue": 28}
                },
                {
                    "id": "w_sc3", "type": "scorecard", "x": 1000, "y": 330, "w": 420, "h": 115, "z": 2,
                    "config": {"metricKey": "rfdetr_latency_ms", "title": "Latensi Inferensi NPU", "unit": "ms", "warningThreshold": 25, "dangerThreshold": 45, "defaultValue": 18.2}
                },
                {
                    "id": "w_excel", "type": "excel_export_btn", "x": 1000, "y": 460, "w": 420, "h": 50, "z": 2,
                    "config": {"label": "Unduh Log Deteksi (.xlsx)", "includeEvents": True, "includeMetrics": True}
                },
                {
                    "id": "w_conf_table", "type": "confidence_table", "x": 20, "y": 625, "w": 1400, "h": 315, "z": 3,
                    "config": {"title": "Tabel Hasil Konfiden Deteksi RF-DETR dengan Bounding Box", "minConfidence": 0.25, "showCropThumbnail": True, "showBboxCoords": True, "exportCsv": True, "exportExcel": True}
                }
            ]
        }

    # =========================================================================
    # 18. FILTER COUNTER & CROSSING TELEMETRY
    # =========================================================================
    elif template_id == "tpl_filter_counter":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Multi-Class Filter Counter & Crossing Telemetry",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080E18"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "MULTI-CLASS FILTER & CROSSING TELEMETRY", "subtitle": "Bi-directional In/Out Counting with Class Segregation", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 860, "h": 500, "z": 2,
                    "config": {"cameraLabel": "CCTV Garis Hitung Dwiarah", "streamId": "cam_counter", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_gauge", "type": "live_gauge_meter", "x": 900, "y": 70, "w": 520, "h": 240, "z": 2,
                    "config": {
                        "title": "Okupansi Netto Ruangan / Area",
                        "metricKey": "net_occupancy_count",
                        "unit": "Orang",
                        "minVal": 0,
                        "maxVal": 100,
                        "warningVal": 70,
                        "dangerVal": 90,
                        "defaultValue": 46
                    }
                },
                {
                    "id": "w_sc_in", "type": "stat_kpi_card", "x": 900, "y": 325, "w": 250, "h": 120, "z": 2,
                    "config": {"title": "TOTAL MASUK (IN)", "value": 418, "icon": "arrow-down-right", "sublabel": "Kumulatif Hari Ini", "accent": "#10B981", "metricKey": "in_count"}
                },
                {
                    "id": "w_sc_out", "type": "stat_kpi_card", "x": 1170, "y": 325, "w": 250, "h": 120, "z": 2,
                    "config": {"title": "TOTAL KELUAR (OUT)", "value": 372, "icon": "arrow-up-right", "sublabel": "Kumulatif Hari Ini", "accent": "#38BDF8", "metricKey": "out_count"}
                },
                {
                    "id": "w_trend", "type": "trend_chart", "x": 20, "y": 590, "w": 700, "h": 340, "z": 3,
                    "config": {"title": "Grafik Arus Masuk vs Keluar per Jam", "metricKey": "in_count", "chartType": "line", "rangeHours": 12}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 740, "y": 590, "w": 680, "h": 340, "z": 3,
                    "config": {"title": "Log Objek Melintasi Garis Hitung", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 19. MOTION DETECTION & PERIMETER SENTRY
    # =========================================================================
    elif template_id == "tpl_motion_detection":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Motion Detection & Perimeter Intrusion Guard",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#0B0B14"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "PERIMETER SENTRY & MOTION INTRUSION GUARD", "subtitle": "Thermal & Optical-Flow Sensitive Intrusion Watcher", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 920, "h": 520, "z": 2,
                    "config": {"cameraLabel": "CCTV Sentry Perimeter Pagar Pembatas", "streamId": "cam_perimeter", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_alerts", "type": "active_alerts_list", "x": 960, "y": 70, "w": 460, "h": 300, "z": 2,
                    "config": {
                        "title": "ALARM PERIMETER SENSITIF",
                        "alerts": [
                            {"level": "CRITICAL", "title": "Pergerakan terdeteksi di Zona Terlarang Timur", "loc": "Pagar Sektor 04"}
                        ]
                    }
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 960, "y": 385, "w": 220, "h": 100, "z": 2,
                    "config": {"metricKey": "motion_energy_pct", "title": "Energi Gerakan", "unit": "%", "warningThreshold": 40, "dangerThreshold": 75, "defaultValue": 12.4}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 1200, "y": 385, "w": 220, "h": 100, "z": 2,
                    "config": {"metricKey": "intrusion_alerts_today", "title": "Total Alarm Hari Ini", "unit": "Kali", "warningThreshold": 2, "dangerThreshold": 5, "defaultValue": 1}
                },
                {
                    "id": "w_excel", "type": "excel_export_btn", "x": 960, "y": 500, "w": 460, "h": 50, "z": 2,
                    "config": {"label": "Unduh Log Insiden Kemanan (.xlsx)", "includeEvents": True, "includeMetrics": True}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 610, "w": 1400, "h": 330, "z": 3,
                    "config": {"title": "Log Kronologis Deteksi Gerakan & Snapshot Rekaman Insiden", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 20. LOW-LIGHT IMAGE ENHANCEMENT STUDIO
    # =========================================================================
    elif template_id == "tpl_image_enhancement":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Low-Light Image Enhancement & De-Noise Studio",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#070D16"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "LOW-LIGHT & NIGHT-VISION ENHANCEMENT STUDIO", "subtitle": "Adaptive CLAHE Contrast & Temporal De-Noising", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 20, "y": 70, "w": 260, "h": 110, "z": 2,
                    "config": {"metricKey": "lumens_index", "title": "Indeks Luminansi", "unit": "Lux", "warningThreshold": 20, "dangerThreshold": 5, "defaultValue": 18.5}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 300, "y": 70, "w": 260, "h": 110, "z": 2,
                    "config": {"metricKey": "contrast_boost_ratio", "title": "Peningkatan Kontras", "unit": "x", "warningThreshold": 1.5, "dangerThreshold": 1.2, "defaultValue": 2.4}
                },
                {
                    "id": "w_sc3", "type": "scorecard", "x": 580, "y": 70, "w": 260, "h": 110, "z": 2,
                    "config": {"metricKey": "noise_reduction_pct", "title": "Noise Tereliminasi", "unit": "%", "warningThreshold": 50, "dangerThreshold": 30, "defaultValue": 74.5}
                },
                {
                    "id": "w_sc4", "type": "scorecard", "x": 860, "y": 70, "w": 260, "h": 110, "z": 2,
                    "config": {"metricKey": "enhancer_fps", "title": "Kecepatan Render", "unit": "FPS", "warningThreshold": 20, "dangerThreshold": 12, "defaultValue": 30.0}
                },
                {
                    "id": "w_badge", "type": "status_badge", "x": 1140, "y": 70, "w": 280, "h": 48, "z": 2,
                    "config": {"label": "NIGHT VISION: ACTIVE (CLAHE Boost)", "status": "online", "shift": "Auto Day/Night Mode"}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 200, "w": 1400, "h": 500, "z": 3,
                    "config": {"cameraLabel": "CCTV Malam Hari dengan Peningkatan Citra Real-time", "streamId": "cam_enhanced", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_trend", "type": "trend_chart", "x": 20, "y": 720, "w": 1400, "h": 220, "z": 4,
                    "config": {"title": "Grafik Distribusi Kecerahan & Kontras Temporal", "metricKey": "lumens_index", "chartType": "line", "rangeHours": 12}
                }
            ]
        }

    # =========================================================================
    # 21. CONDITIONAL LOGIC & BRANCHING ROUTER
    # =========================================================================
    elif template_id == "tpl_branching_if_else":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Conditional Logic & Multi-Branch Router Hub",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080C16"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "DYNAMIC LOGIC & BRANCHING ROUTER HUB", "subtitle": "Conditional Rule Evaluation & Multi-Stream Splitting", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 880, "h": 480, "z": 2,
                    "config": {"cameraLabel": "Stream Evaluasi Alur Logika Percabangan", "streamId": "cam_branch", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_donut", "type": "donut_chart", "x": 920, "y": 70, "w": 500, "h": 250, "z": 2,
                    "config": {
                        "title": "RASIO PERCABANGAN ALUR",
                        "segments": [
                            {"label": "Jalur True (Lolos)", "pct": 78, "color": "#10B981"},
                            {"label": "Jalur False (Alihkan)", "pct": 22, "color": "#F59E0B"}
                        ]
                    }
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 920, "y": 335, "w": 240, "h": 100, "z": 2,
                    "config": {"metricKey": "true_branch_count", "title": "Eksekusi Jalur A", "unit": "Objek", "warningThreshold": 100, "dangerThreshold": 200, "defaultValue": 128}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 1180, "y": 335, "w": 240, "h": 100, "z": 2,
                    "config": {"metricKey": "false_branch_count", "title": "Eksekusi Jalur B", "unit": "Objek", "warningThreshold": 30, "dangerThreshold": 60, "defaultValue": 36}
                },
                {
                    "id": "w_badge", "type": "status_badge", "x": 920, "y": 450, "w": 500, "h": 48, "z": 2,
                    "config": {"label": "STATUS LOGIKA: Evaluasi Otomatis Aktif", "status": "online", "shift": "Rule: class == person && conf > 0.5"}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 570, "w": 1400, "h": 360, "z": 3,
                    "config": {"title": "Log Riwayat Keputusan Percabangan & Pengalihan Alur", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 22. WORKFLOW 01 — OBJECT DETECTION
    # =========================================================================
    elif template_id == "tpl_wf01_detection":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 01 — Basic Object Detection Hub",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080E18"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "WORKFLOW 01: BASIC OBJECT DETECTION", "subtitle": "Standard YOLOv8 Object Classification & Bounding Box Visualizer", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 860, "h": 520, "z": 2,
                    "config": {"cameraLabel": "Kamera Deteksi Objek", "streamId": "cam_wf01", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_summary", "type": "detection_summary", "x": 900, "y": 70, "w": 520, "h": 260, "z": 2,
                    "config": {"title": "RINGKASAN DETEKSI KELAS", "metricKey": "detection_summary"}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 900, "y": 345, "w": 250, "h": 115, "z": 2,
                    "config": {"metricKey": "wf01_total_count", "title": "Total Objek Terdeteksi", "unit": "Objek", "warningThreshold": 30, "dangerThreshold": 60, "defaultValue": 18}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 1170, "y": 345, "w": 250, "h": 115, "z": 2,
                    "config": {"metricKey": "wf01_avg_conf", "title": "Keyakinan Rata-rata", "unit": "%", "warningThreshold": 75, "dangerThreshold": 50, "defaultValue": 89.2}
                },
                {
                    "id": "w_table", "type": "confidence_table", "x": 20, "y": 610, "w": 1400, "h": 330, "z": 3,
                    "config": {"title": "Daftar Objek Terdeteksi & Skor Keyakinan", "minConfidence": 0.25, "showCropThumbnail": True, "showBboxCoords": True, "exportCsv": True, "exportExcel": True}
                }
            ]
        }

    # =========================================================================
    # 23. WORKFLOW 02 — FILTER COUNT
    # =========================================================================
    elif template_id == "tpl_wf02_filter_count":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 02 — Class Filter & Area Counter",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#090E17"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "WORKFLOW 02: CLASS FILTER & AREA COUNTER", "subtitle": "Selective Target Filtering & Area Population Sentry", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 900, "h": 510, "z": 2,
                    "config": {"cameraLabel": "CCTV Area Filter Terfokus", "streamId": "cam_wf02", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 940, "y": 70, "w": 480, "h": 130, "z": 2,
                    "config": {"metricKey": "target_class_count", "title": "Kelas Target (Lolos Filter)", "unit": "Unit", "warningThreshold": 20, "dangerThreshold": 40, "defaultValue": 12}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 940, "y": 215, "w": 480, "h": 130, "z": 2,
                    "config": {"metricKey": "filtered_out_count", "title": "Non-Target (Dieliminasi)", "unit": "Unit", "warningThreshold": 50, "dangerThreshold": 100, "defaultValue": 34}
                },
                {
                    "id": "w_excel", "type": "excel_export_btn", "x": 940, "y": 360, "w": 480, "h": 50, "z": 2,
                    "config": {"label": "Unduh Rekap Filter (.xlsx)", "includeEvents": True, "includeMetrics": True}
                },
                {
                    "id": "w_trend", "type": "trend_chart", "x": 20, "y": 600, "w": 700, "h": 340, "z": 3,
                    "config": {"title": "Grafik Akumulasi Objek Target per Jam", "metricKey": "target_class_count", "chartType": "line", "rangeHours": 12}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 740, "y": 600, "w": 680, "h": 340, "z": 3,
                    "config": {"title": "Log Deteksi Kelas Terpilih", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 24. WORKFLOW 03 — TRACKING LINE
    # =========================================================================
    elif template_id == "tpl_wf03_tracking_line":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 03 — Multi-Object Tracking & Line Counter",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080F1D"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "WORKFLOW 03: TRACKING & LINE CROSSING", "subtitle": "Persistent Track ID, Trajectory History & Velocity Calculation", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 20, "y": 70, "w": 260, "h": 110, "z": 2,
                    "config": {"metricKey": "line_in", "title": "Garis Masuk (In)", "unit": "Objek", "warningThreshold": 50, "dangerThreshold": 100, "defaultValue": 64}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 300, "y": 70, "w": 260, "h": 110, "z": 2,
                    "config": {"metricKey": "line_out", "title": "Garis Keluar (Out)", "unit": "Objek", "warningThreshold": 50, "dangerThreshold": 100, "defaultValue": 58}
                },
                {
                    "id": "w_sc3", "type": "scorecard", "x": 580, "y": 70, "w": 260, "h": 110, "z": 2,
                    "config": {"metricKey": "avg_track_len", "title": "Panjang Trajektori Rata-rata", "unit": "Titik", "warningThreshold": 20, "dangerThreshold": 10, "defaultValue": 42}
                },
                {
                    "id": "w_sc4", "type": "scorecard", "x": 860, "y": 70, "w": 260, "h": 110, "z": 2,
                    "config": {"metricKey": "active_tracklets", "title": "Tracklet Aktif di Layar", "unit": "ID", "warningThreshold": 15, "dangerThreshold": 30, "defaultValue": 8}
                },
                {
                    "id": "w_excel", "type": "excel_export_btn", "x": 1140, "y": 70, "w": 280, "h": 50, "z": 2,
                    "config": {"label": "Unduh Log Tracking (.xlsx)", "includeEvents": True, "includeMetrics": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 195, "w": 900, "h": 460, "z": 3,
                    "config": {"cameraLabel": "CCTV dengan Garis Hitung & Jejak Trajektori", "streamId": "cam_tracking", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_trend", "type": "trend_chart", "x": 940, "y": 195, "w": 480, "h": 460, "z": 3,
                    "config": {"title": "Grafik Kecepatan Lintas per Jam", "metricKey": "line_in", "chartType": "line", "rangeHours": 12}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 670, "w": 1400, "h": 270, "z": 4,
                    "config": {"title": "Tabel Kronologis Penyeberangan Garis & Kecepatan Tracking", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 25. WORKFLOW 04 — DWELL PRIVACY
    # =========================================================================
    elif template_id == "tpl_wf04_dwell_privacy":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 04 — Zone Dwell Time & Privacy Blur",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#0B0E17"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "WORKFLOW 04: DWELL TIME & PRIVACY BLUR", "subtitle": "Zone Dwelling Duration Watcher with GDPR-Compliant Face/Body Blur", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 920, "h": 500, "z": 2,
                    "config": {"cameraLabel": "CCTV Zona Dwell dengan Penyamaran Privasi", "streamId": "cam_privacy", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 960, "y": 70, "w": 460, "h": 120, "z": 2,
                    "config": {"metricKey": "dwell_violators_count", "title": "Pelanggaran Dwell Time (>5 Mnt)", "unit": "Orang", "warningThreshold": 3, "dangerThreshold": 6, "defaultValue": 2}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 960, "y": 205, "w": 460, "h": 120, "z": 2,
                    "config": {"metricKey": "avg_dwell_sec", "title": "Rata-rata Waktu Menetap", "unit": "Detik", "warningThreshold": 180, "dangerThreshold": 300, "defaultValue": 142}
                },
                {
                    "id": "w_sc3", "type": "scorecard", "x": 960, "y": 340, "w": 460, "h": 120, "z": 2,
                    "config": {"metricKey": "faces_blurred_count", "title": "Wajah Berhasil Disamarkan", "unit": "Wajah", "warningThreshold": 100, "dangerThreshold": 200, "defaultValue": 84}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 590, "w": 1400, "h": 350, "z": 3,
                    "config": {"title": "Log Peringatan Batas Dwell Time Zona Terlarang", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 26. WORKFLOW 05 — POLYGON SEGMENTATION
    # =========================================================================
    elif template_id == "tpl_wf05_segmentation":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 05 — Polygon Instance Segmentation Hub",
            "theme": "dark",
            "canvas": {"width": 1520, "height": 960, "background": "#080C18"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1520, "h": 56, "z": 1,
                    "config": {"title": "WORKFLOW 05: POLYGON INSTANCE SEGMENTATION", "subtitle": "Pixel-Level Masking & Surface Area Quantification", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 860, "h": 530, "z": 2,
                    "config": {"cameraLabel": "CCTV Segmentasi Poligon Mask", "streamId": "cam_seg", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_conf_table", "type": "confidence_table", "x": 900, "y": 70, "w": 600, "h": 280, "z": 2,
                    "config": {"title": "Tabel Confidence & Mask IoU", "metricKey": "mask_detections"}
                },
                {
                    "id": "w_sc1", "type": "stat_kpi_card", "x": 900, "y": 365, "w": 290, "h": 110, "z": 2,
                    "config": {"title": "CAKUPAN MASK", "value": "24.5%", "icon": "pie-chart", "sublabel": "Luas Area Piksel", "accent": "#00E5FF", "metricKey": "mask_coverage_pct"}
                },
                {
                    "id": "w_sc2", "type": "stat_kpi_card", "x": 1210, "y": 365, "w": 290, "h": 110, "z": 2,
                    "config": {"title": "POLIGON TERDETEKSI", "value": 7, "icon": "check-square", "sublabel": "Objek Tersegmentasi", "accent": "#10B981", "metricKey": "masks_detected"}
                },
                {
                    "id": "w_chart", "type": "trend_chart", "x": 900, "y": 490, "w": 600, "h": 230, "z": 2,
                    "config": {"title": "Grafik Luas Area Mask per Frame", "metricKey": "mask_coverage_pct", "chartType": "line", "rangeHours": 4}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 620, "w": 860, "h": 320, "z": 3,
                    "config": {"title": "Tabel Geometri Poligon & Luas Area Piksel", "maxRows": 25, "autoScroll": True, "showFilter": True}
                },
                {
                    "id": "w_excel", "type": "excel_export_btn", "x": 900, "y": 735, "w": 600, "h": 45, "z": 2,
                    "config": {"label": "Export Data Segmentasi (.xlsx)", "includeEvents": True, "includeMetrics": True}
                }
            ]
        }

    # =========================================================================
    # 27. WORKFLOW 06 — CROP & SECONDARY CLASSIFICATION
    # =========================================================================
    elif template_id == "tpl_wf06_crop_classify":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 06 — Object Crop & Secondary Classification",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080E1C"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "WORKFLOW 06: DUAL-STAGE CROP & CLASSIFY", "subtitle": "Primary Detection & Deep Secondary Neural Classification", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 880, "h": 490, "z": 2,
                    "config": {"cameraLabel": "Kamera Utama Deteksi Primer", "streamId": "cam_crop_primary", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 920, "y": 70, "w": 240, "h": 115, "z": 2,
                    "config": {"metricKey": "crops_processed", "title": "Total Crop Diproses", "unit": "Crop", "warningThreshold": 100, "dangerThreshold": 200, "defaultValue": 184}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 1180, "y": 70, "w": 240, "h": 115, "z": 2,
                    "config": {"metricKey": "secondary_conf", "title": "Keyakinan Klasifikasi", "unit": "%", "warningThreshold": 80, "dangerThreshold": 60, "defaultValue": 96.1}
                },
                {
                    "id": "w_donut", "type": "donut_chart", "x": 920, "y": 200, "w": 500, "h": 260, "z": 2,
                    "config": {
                        "title": "DISTRIBUSI SUB-KELAS HASIL CROP",
                        "segments": [
                            {"label": "Tipe A (Sedan)", "pct": 45, "color": "#00E5FF"},
                            {"label": "Tipe B (SUV)", "pct": 35, "color": "#A855F7"},
                            {"label": "Tipe C (Truk)", "pct": 20, "color": "#F59E0B"}
                        ]
                    }
                },
                {
                    "id": "w_conf_table", "type": "confidence_table", "x": 20, "y": 580, "w": 1400, "h": 360, "z": 3,
                    "config": {"title": "Galeri Crop Objek & Hasil Klasifikasi Sekunder", "minConfidence": 0.25, "showCropThumbnail": True, "showBboxCoords": True, "exportCsv": True, "exportExcel": True}
                }
            ]
        }

    # =========================================================================
    # 28. WORKFLOW 07 — IF/ELSE LOGIC
    # =========================================================================
    elif template_id == "tpl_wf07_if_else":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 07 — Conditional If/Else Logic Decision",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#070E1A"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "WORKFLOW 07: IF/ELSE DECISION GATE", "subtitle": "Deterministic Logic Gatekeeper & Automated Alert Dispatch", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 860, "h": 480, "z": 2,
                    "config": {"cameraLabel": "CCTV Evaluasi Gerbang Logika", "streamId": "cam_logic", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_badge1", "type": "status_badge", "x": 900, "y": 70, "w": 520, "h": 60, "z": 2,
                    "config": {"label": "KONDISI GERBANG: PASS (Lolos SOP)", "status": "online", "shift": "Aturan: Helm Aktif & Jarak Aman > 1.5m"}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 900, "y": 145, "w": 250, "h": 120, "z": 2,
                    "config": {"metricKey": "pass_count", "title": "Total Kondisi PASS", "unit": "Kali", "warningThreshold": 100, "dangerThreshold": 50, "defaultValue": 240}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 1170, "y": 145, "w": 250, "h": 120, "z": 2,
                    "config": {"metricKey": "fail_count", "title": "Total Kondisi FAIL", "unit": "Kali", "warningThreshold": 5, "dangerThreshold": 10, "defaultValue": 3}
                },
                {
                    "id": "w_trend", "type": "trend_chart", "x": 900, "y": 280, "w": 520, "h": 270, "z": 2,
                    "config": {"title": "Grafik Kepatuhan PASS vs FAIL", "metricKey": "pass_count", "chartType": "line", "rangeHours": 12}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 570, "w": 1400, "h": 360, "z": 3,
                    "config": {"title": "Log Keputusan Aturan Gerbang Logika Real-time", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 29. WORKFLOW 08 — MULTI-ROI
    # =========================================================================
    elif template_id == "tpl_wf08_roi":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 08 — Multi-ROI Region of Interest Filter",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080C14"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "WORKFLOW 08: MULTI-ROI MATRIX", "subtitle": "Concurrent 3-Zone Spatial Occupancy & Boundary Watch", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 900, "h": 520, "z": 2,
                    "config": {"cameraLabel": "CCTV dengan 3 ROI Poligon Aktif", "streamId": "cam_roi", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 940, "y": 70, "w": 480, "h": 120, "z": 2,
                    "config": {"metricKey": "roi_1_count", "title": "ROI 1: Zona Pemuatan (Loading)", "unit": "Unit", "warningThreshold": 5, "dangerThreshold": 10, "defaultValue": 4}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 940, "y": 205, "w": 480, "h": 120, "z": 2,
                    "config": {"metricKey": "roi_2_count", "title": "ROI 2: Jalur Forklift (Hazard)", "unit": "Unit", "warningThreshold": 3, "dangerThreshold": 5, "defaultValue": 1}
                },
                {
                    "id": "w_sc3", "type": "scorecard", "x": 940, "y": 340, "w": 480, "h": 120, "z": 2,
                    "config": {"metricKey": "roi_3_count", "title": "ROI 3: Koridor Pejalan Kaki", "unit": "Orang", "warningThreshold": 8, "dangerThreshold": 15, "defaultValue": 6}
                },
                {
                    "id": "w_trend", "type": "trend_chart", "x": 20, "y": 610, "w": 700, "h": 330, "z": 3,
                    "config": {"title": "Grafik Kepadatan per ROI (24 Jam)", "metricKey": "roi_1_count", "chartType": "line", "rangeHours": 24}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 740, "y": 610, "w": 680, "h": 330, "z": 3,
                    "config": {"title": "Log Perpindahan Objek Antar-ROI", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 30. WORKFLOW 09 — CONDITIONS
    # =========================================================================
    elif template_id == "tpl_wf09_conditions":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 09 — Multi-Criteria Complex Logic Evaluator",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#0A0D18"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "WORKFLOW 09: MULTI-CRITERIA EVALUATOR", "subtitle": "Composite Rules, Cooldown Timers & Automated Dispatch", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 960, "h": 500, "z": 2,
                    "config": {"cameraLabel": "CCTV Evaluasi Multi-Kriteria", "streamId": "cam_cond", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_alerts", "type": "active_alerts_list", "x": 1000, "y": 70, "w": 420, "h": 360, "z": 2,
                    "config": {
                        "title": "STATUS EVALUASI 4 ATURAN",
                        "alerts": [
                            {"level": "CRITICAL", "title": "Aturan 1 (Kepadatan > 10): TERPENUHI", "loc": "Area A"},
                            {"level": "WARNING", "title": "Aturan 2 (Waktu Dwell > 3m): AKTIF", "loc": "Area B"}
                        ]
                    }
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 1000, "y": 445, "w": 420, "h": 125, "z": 2,
                    "config": {"metricKey": "rules_triggered_today", "title": "Total Pemicu Aturan Hari Ini", "unit": "Kali", "warningThreshold": 10, "dangerThreshold": 25, "defaultValue": 8}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 590, "w": 1400, "h": 350, "z": 3,
                    "config": {"title": "Log Kejadian Terverifikasi Aturan Multi-Kriteria", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 31. WORKFLOW 10 — TRANSFORM
    # =========================================================================
    elif template_id == "tpl_wf10_transform":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 10 — Spatial Transform & Perspective Projector",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#070C15"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "WORKFLOW 10: PERSPECTIVE TRANSFORM & BEV", "subtitle": "4-Point Ground Calibration & Spatial Coordinate Mapping", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv_persp", "type": "cctv_player", "x": 20, "y": 70, "w": 690, "h": 460, "z": 2,
                    "config": {"cameraLabel": "Kamera Perspektif Asli (4-Point Ground)", "streamId": "cam_persp", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_cctv_bev", "type": "cctv_player", "x": 730, "y": 70, "w": 690, "h": 460, "z": 2,
                    "config": {"cameraLabel": "Tampak Atas Proyeksi Tanah (Birds-Eye-View Grid)", "streamId": "cam_bev", "nodeId": "bev_visualizer", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 20, "y": 545, "w": 330, "h": 110, "z": 2,
                    "config": {"metricKey": "calibrated_scale_m", "title": "Skala Kalibrasi Tanah", "unit": "m/px", "warningThreshold": 0.05, "dangerThreshold": 0.02, "defaultValue": 0.035}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 370, "y": 545, "w": 330, "h": 110, "z": 2,
                    "config": {"metricKey": "ground_objects_mapped", "title": "Objek Terpetakan ke Tanah", "unit": "Objek", "warningThreshold": 20, "dangerThreshold": 40, "defaultValue": 14}
                },
                {
                    "id": "w_sc3", "type": "scorecard", "x": 720, "y": 545, "w": 330, "h": 110, "z": 2,
                    "config": {"metricKey": "homography_error", "title": "Error Homografi", "unit": "px", "warningThreshold": 3, "dangerThreshold": 8, "defaultValue": 1.2}
                },
                {
                    "id": "w_sc4", "type": "scorecard", "x": 1070, "y": 545, "w": 350, "h": 110, "z": 2,
                    "config": {"metricKey": "transform_fps", "title": "Kecepatan Warp", "unit": "FPS", "warningThreshold": 25, "dangerThreshold": 15, "defaultValue": 30.0}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 670, "w": 1400, "h": 270, "z": 3,
                    "config": {"title": "Tabel Koordinat Spasial Dunia Nyata (X, Y dalam meter)", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 32. WORKFLOW 11 — ENHANCE
    # =========================================================================
    elif template_id == "tpl_wf11_enhance":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 11 — Advanced Image Enhancement & Equalizer",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080B15"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "WORKFLOW 11: SPECTRAL EQUALIZER & ENHANCE", "subtitle": "Adaptive Tone Mapping, Gamma Correction & Edge Sharpening", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 960, "h": 520, "z": 2,
                    "config": {"cameraLabel": "CCTV dengan Peningkatan Spektral", "streamId": "cam_spectral", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_gauge", "type": "live_gauge_meter", "x": 1000, "y": 70, "w": 420, "h": 240, "z": 2,
                    "config": {
                        "title": "Indeks Ketajaman Laplacian",
                        "metricKey": "laplacian_sharpness_score",
                        "unit": "Score",
                        "minVal": 0,
                        "maxVal": 500,
                        "warningVal": 150,
                        "dangerVal": 80,
                        "defaultValue": 320
                    }
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 1000, "y": 325, "w": 200, "h": 120, "z": 2,
                    "config": {"metricKey": "gamma_applied", "title": "Gamma Koreksi", "unit": "γ", "warningThreshold": 1.5, "dangerThreshold": 2.0, "defaultValue": 1.2}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 1220, "y": 325, "w": 200, "h": 120, "z": 2,
                    "config": {"metricKey": "color_vibrance_pct", "title": "Vibransi Warna", "unit": "%", "warningThreshold": 50, "dangerThreshold": 30, "defaultValue": 68}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 610, "w": 1400, "h": 330, "z": 3,
                    "config": {"title": "Log Penyesuaian Kualitas & Filter Citra", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 33. WORKFLOW 12 — CALIBRATION
    # =========================================================================
    elif template_id == "tpl_wf12_calibration":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 12 — Camera Calibration & Perspective Desk",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 920, "background": "#070E1A"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "WORKFLOW 12: CAMERA CALIBRATION & PERSPECTIVE WARP", "subtitle": "Koreksi Distorsi Lensa & Transformasi Bird's Eye View", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv1", "type": "cctv_player", "x": 20, "y": 70, "w": 520, "h": 380, "z": 2,
                    "config": {"cameraLabel": "Kamera Raw Asli (Distorted)", "streamId": "cam_raw_calib", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_cctv2", "type": "cctv_player", "x": 560, "y": 70, "w": 520, "h": 380, "z": 2,
                    "config": {"cameraLabel": "Kamera Kalibrasi Bird's Eye View", "streamId": "cam_warped", "nodeId": "detector", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_sc1", "type": "stat_kpi_card", "x": 1100, "y": 70, "w": 320, "h": 105, "z": 2,
                    "config": {"title": "REPROJECTION ERROR", "value": "0.14 px", "icon": "target", "sublabel": "Toleransi Sangat Presisi", "accent": "#10B981", "metricKey": "calib_error"}
                },
                {
                    "id": "w_sc2", "type": "stat_kpi_card", "x": 1100, "y": 190, "w": 320, "h": 105, "z": 2,
                    "config": {"title": "RASIO SKALA DUNIA", "value": "24.8 px/cm", "icon": "maximize-2", "sublabel": "Faktor Kalibrasi Geometrik", "accent": "#38BDF8", "metricKey": "calib_scale_ratio"}
                },
                {
                    "id": "w_sc3", "type": "scorecard", "x": 1100, "y": 310, "w": 320, "h": 105, "z": 2,
                    "config": {"metricKey": "calib_status", "title": "Status Matriks Homografi", "unit": "", "warningThreshold": 0, "dangerThreshold": 0, "defaultValue": 1}
                },
                {
                    "id": "w_excel", "type": "excel_export_btn", "x": 1100, "y": 430, "w": 320, "h": 45, "z": 2,
                    "config": {"label": "Export Titik Kalibrasi (.xlsx)", "includeEvents": True, "includeMetrics": True}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 470, "w": 680, "h": 430, "z": 3,
                    "config": {"title": "Tabel Titik Referensi Kalibrasi 4-Point", "maxRows": 25, "autoScroll": True, "showFilter": True}
                },
                {
                    "id": "w_chart", "type": "trend_chart", "x": 720, "y": 470, "w": 700, "h": 430, "z": 3,
                    "config": {"title": "Stabilitas Matriks Homografi Antar Frame", "metricKey": "calib_error", "chartType": "line", "rangeHours": 12}
                }
            ]
        }

    # =========================================================================
    # 34. WORKFLOW 13 — MOTION & OPTICAL FLOW
    # =========================================================================
    elif template_id == "tpl_wf13_motion":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 13 — Optical Flow & Dynamic Motion Sentry",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#070D18"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "WORKFLOW 13: OPTICAL FLOW VECTOR SENTRY", "subtitle": "Lucas-Kanade Dense Motion Vector Field & Turbulence Analyzer", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 900, "h": 500, "z": 2,
                    "config": {"cameraLabel": "CCTV dengan Lapisan Vektor Optical Flow", "streamId": "cam_optflow", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_gauge", "type": "live_gauge_meter", "x": 940, "y": 70, "w": 480, "h": 240, "z": 2,
                    "config": {
                        "title": "Intensitas Turbulensi Gerak",
                        "metricKey": "motion_turbulence_intensity",
                        "unit": "Magnitude",
                        "minVal": 0,
                        "maxVal": 100,
                        "warningVal": 50,
                        "dangerVal": 80,
                        "defaultValue": 34
                    }
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 940, "y": 325, "w": 230, "h": 115, "z": 2,
                    "config": {"metricKey": "dominant_direction_deg", "title": "Arah Dominan", "unit": "°", "warningThreshold": 180, "dangerThreshold": 270, "defaultValue": 84}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 1190, "y": 325, "w": 230, "h": 115, "z": 2,
                    "config": {"metricKey": "motion_vectors_count", "title": "Vektor Terdeteksi", "unit": "Titik", "warningThreshold": 500, "dangerThreshold": 1000, "defaultValue": 420}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 590, "w": 1400, "h": 350, "z": 3,
                    "config": {"title": "Log Kejadian Lonjakan Gerakan & Deteksi Anomali", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 35. WORKFLOW 14 — SAMPLING & SAHI SLICER
    # =========================================================================
    elif template_id == "tpl_wf14_sampling_slicer":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 14 — Video Frame Slicer & Smart Sampling",
            "theme": "dark",
            "canvas": {"width": 1400, "height": 940, "background": "#080F1D"},
            "widgets": [
                {
                    "id": "w_head", "type": "custom_text", "x": 20, "y": 15, "w": 700, "h": 50, "z": 1,
                    "config": {"text": "Workflow 14: Video Frame Slicer & Smart Sampling", "tag": "h1", "fontSize": 24, "color": "#06B6D4", "subtitle": "Optimasi Throughput Komputasi dengan Intelligent Frame Skipping"}
                },
                {
                    "id": "w_badge", "type": "status_badge", "x": 1120, "y": 20, "w": 260, "h": 45, "z": 1,
                    "config": {"label": "Slicer Pipeline Aktif", "status": "online", "shift": "Mode Dinamis"}
                },
                {
                    "id": "w_sc1", "type": "stat_kpi_card", "x": 20, "y": 80, "w": 440, "h": 105, "z": 2,
                    "config": {"title": "TOTAL FRAME MASUK", "value": 14200, "icon": "film", "sublabel": "Raw Ingestion 30 FPS", "accent": "#38BDF8", "metricKey": "total_frames_in"}
                },
                {
                    "id": "w_sc2", "type": "stat_kpi_card", "x": 480, "y": 80, "w": 440, "h": 105, "z": 2,
                    "config": {"title": "FRAME LOLOS SAMPLING", "value": 2840, "icon": "filter", "sublabel": "Diteruskan ke Model AI (1:5)", "accent": "#10B981", "metricKey": "frames_passed"}
                },
                {
                    "id": "w_sc3", "type": "stat_kpi_card", "x": 940, "y": 80, "w": 440, "h": 105, "z": 2,
                    "config": {"title": "PENGHEMATAN KOMPUTASI", "value": "80%", "icon": "cpu", "sublabel": "Beban GPU Direduksi", "accent": "#F59E0B", "metricKey": "compute_saved_pct"}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 205, "w": 780, "h": 450, "z": 3,
                    "config": {"cameraLabel": "Stream Video Sampling Real-time", "streamId": "cam_slicer_stream", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_alerts", "type": "active_alerts_strip", "x": 820, "y": 205, "w": 560, "h": 160, "z": 2,
                    "config": {"title": "Status Buffer Slicer & Peringatan Frame Drop", "maxAlerts": 3, "autoDismiss": False}
                },
                {
                    "id": "w_chart", "type": "trend_chart", "x": 820, "y": 385, "w": 560, "h": 270, "z": 4,
                    "config": {"title": "Laju Sampling Frame per Detik (FPS)", "metricKey": "sampling_fps", "chartType": "line", "rangeHours": 4}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 675, "w": 1360, "h": 245, "z": 4,
                    "config": {"title": "Log Cuplikan Frame Terpilih & Keyframe SSIM", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 36. WORKFLOW 15 — HIGH-SPEED BARCODE & QR SCANNER
    # =========================================================================
    elif template_id == "tpl_wf15_barcode":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 15 — Barcode & QR Code High-Speed Scanner",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080D17"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "CONVEYOR BARCODE & QR CODE SCANNER HUB", "subtitle": "High-Speed Logistics Sorter & Automated SKU Validation", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 860, "h": 460, "z": 2,
                    "config": {"cameraLabel": "Kamera Konveyor Pemindai Barcode", "streamId": "cam_barcode", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_kpi_last", "type": "stat_kpi_card", "x": 900, "y": 70, "w": 520, "h": 140, "z": 2,
                    "config": {"title": "KODE TERAKHIR DIPINDAI", "value": "SKU-882910-B", "icon": "maximize-2", "sublabel": "EAN-13 · Lolos Validasi", "accent": "#00E5FF", "metricKey": "last_scanned_barcode"}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 900, "y": 225, "w": 250, "h": 115, "z": 2,
                    "config": {"metricKey": "scan_read_rate_pct", "title": "Tingkat Bacaan Sukses", "unit": "%", "warningThreshold": 98.0, "dangerThreshold": 95.0, "defaultValue": 99.8}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 1170, "y": 225, "w": 250, "h": 115, "z": 2,
                    "config": {"metricKey": "scans_per_minute", "title": "Kecepatan Pemindaian", "unit": "Scans/M", "warningThreshold": 60, "dangerThreshold": 40, "defaultValue": 94}
                },
                {
                    "id": "w_excel", "type": "excel_export_btn", "x": 900, "y": 355, "w": 520, "h": 50, "z": 2,
                    "config": {"label": "Unduh Rekap Barcode (.xlsx)", "includeEvents": True, "includeMetrics": True}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 550, "w": 1400, "h": 390, "z": 3,
                    "config": {"title": "Tabel Riwayat Barcode & QR Code Terpindai Lengkap dengan Timestamp", "maxRows": 35, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 37. WORKFLOW 16 — EVENT CONTROLS
    # =========================================================================
    elif template_id == "tpl_wf16_event_controls":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 16 — Event Dispatcher & Webhook Trigger",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#070E1A"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "EVENT DISPATCHER & WEBHOOK TRIGGER HUB", "subtitle": "Real-time HTTP Push, MQTT Notification & Enterprise Integration", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 900, "h": 480, "z": 2,
                    "config": {"cameraLabel": "CCTV Pemicu Event Otomatis", "streamId": "cam_event", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_badge", "type": "status_badge", "x": 940, "y": 70, "w": 480, "h": 50, "z": 2,
                    "config": {"label": "WEBHOOK STATUS: ONLINE (HTTP 200)", "status": "online", "shift": "Endpoint: https://api.enterprise.corp/events"}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 940, "y": 135, "w": 230, "h": 120, "z": 2,
                    "config": {"metricKey": "webhooks_sent", "title": "Event Terkirim", "unit": "Payload", "warningThreshold": 500, "dangerThreshold": 1000, "defaultValue": 242}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 1190, "y": 135, "w": 230, "h": 120, "z": 2,
                    "config": {"metricKey": "webhook_latency_ms", "title": "Latensi Respon HTTP", "unit": "ms", "warningThreshold": 200, "dangerThreshold": 500, "defaultValue": 48}
                },
                {
                    "id": "w_trend", "type": "trend_chart", "x": 940, "y": 270, "w": 480, "h": 280, "z": 2,
                    "config": {"title": "Grafik Frekuensi Pengiriman Webhook", "metricKey": "webhooks_sent", "chartType": "line", "rangeHours": 12}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 570, "w": 1400, "h": 360, "z": 3,
                    "config": {"title": "Log Payload Webhook & Respon Server Penerima", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 38. WORKFLOW 17 — PYTHON SCRIPT
    # =========================================================================
    elif template_id == "tpl_wf17_python_script":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 17 — Custom Python Script Execution Runner",
            "theme": "dark",
            "canvas": {"width": 1600, "height": 980, "background": "#070D1A"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1600, "h": 56, "z": 1,
                    "config": {"title": "WORKFLOW 17: CUSTOM PYTHON SCRIPT EXECUTION", "subtitle": "Runtime Sandbox, Eksekusi Variabel Mandiri & Latensi Pemrosesan", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 800, "h": 480, "z": 2,
                    "config": {"cameraLabel": "Pipeline Frame Input / Processed Stream", "streamId": "cam_python_run", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_analytics", "type": "analytics_table", "x": 840, "y": 70, "w": 740, "h": 480, "z": 2,
                    "config": {"title": "Tabel Variabel Output Eksekusi Python", "sourceNode": "python_script", "refreshSec": 2}
                },
                {
                    "id": "w_sc1", "type": "stat_kpi_card", "x": 20, "y": 565, "w": 380, "h": 100, "z": 2,
                    "config": {"title": "LATENSI EKSEKUSI SCRIPT", "value": "12.4 ms", "icon": "zap", "sublabel": "Waktu Runtime per Frame", "accent": "#10B981", "metricKey": "script_runtime_ms"}
                },
                {
                    "id": "w_sc2", "type": "stat_kpi_card", "x": 420, "y": 565, "w": 380, "h": 100, "z": 2,
                    "config": {"title": "MEMORI PYTHON SANDBOX", "value": "48.2 MB", "icon": "cpu", "sublabel": "Penggunaan RAM Script", "accent": "#38BDF8", "metricKey": "script_memory_mb"}
                },
                {
                    "id": "w_sc3", "type": "stat_kpi_card", "x": 820, "y": 565, "w": 380, "h": 100, "z": 2,
                    "config": {"title": "OUTPUT ARRAY SIZE", "value": "1920x1080", "icon": "maximize-2", "sublabel": "Dimensi Tensor Matriks", "accent": "#F59E0B", "metricKey": "tensor_shape"}
                },
                {
                    "id": "w_sc4", "type": "stat_kpi_card", "x": 1220, "y": 565, "w": 360, "h": 100, "z": 2,
                    "config": {"title": "STATUS EKSEKUSI", "value": "PASS (0 Errors)", "icon": "check-circle", "sublabel": "Sandbox Stabil", "accent": "#00E5FF", "metricKey": "script_status"}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 680, "w": 980, "h": 280, "z": 3,
                    "config": {"title": "Console stdout / stderr & Output Log", "maxRows": 25, "autoScroll": True, "showFilter": True}
                },
                {
                    "id": "w_chart", "type": "trend_chart", "x": 1020, "y": 680, "w": 560, "h": 280, "z": 3,
                    "config": {"title": "Grafik Latensi Eksekusi per Frame (ms)", "metricKey": "script_runtime_ms", "chartType": "line", "rangeHours": 4}
                }
            ]
        }

    # =========================================================================
    # 39. WORKFLOW 18 — OUTPUT
    # =========================================================================
    elif template_id == "tpl_wf18_output":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 18 — Multi-Channel Video & Stream Output",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080F1E"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "MULTI-SINK BROADCAST & STREAM DISTRIBUTION", "subtitle": "Simultaneous RTSP Out, Local Storage Recording & WebRTC Multiplex", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv1", "type": "cctv_player", "x": 20, "y": 70, "w": 690, "h": 460, "z": 2,
                    "config": {"cameraLabel": "Output Siaran 1 (RTSP Relay 1080p)", "streamId": "cam_out_rtsp", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_cctv2", "type": "cctv_player", "x": 730, "y": 70, "w": 690, "h": 460, "z": 2,
                    "config": {"cameraLabel": "Output Siaran 2 (Perekam Disk Lokal MP4)", "streamId": "cam_out_disk", "nodeId": "detector", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_gauge", "type": "live_gauge_meter", "x": 20, "y": 545, "w": 450, "h": 220, "z": 3,
                    "config": {
                        "title": "Bitrate Encoding Video",
                        "metricKey": "broadcast_bitrate_mbps",
                        "unit": "Mbps",
                        "minVal": 0,
                        "maxVal": 20,
                        "warningVal": 12,
                        "dangerVal": 18,
                        "defaultValue": 6.4
                    }
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 490, "y": 545, "w": 300, "h": 110, "z": 3,
                    "config": {"metricKey": "dropped_frames_count", "title": "Frame Drop Sink", "unit": "Frame", "warningThreshold": 10, "dangerThreshold": 30, "defaultValue": 0}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 810, "y": 545, "w": 300, "h": 110, "z": 3,
                    "config": {"metricKey": "client_viewers_connected", "title": "Klien Terhubung", "unit": "User", "warningThreshold": 15, "dangerThreshold": 30, "defaultValue": 5}
                },
                {
                    "id": "w_sc3", "type": "scorecard", "x": 1130, "y": 545, "w": 290, "h": 110, "z": 3,
                    "config": {"metricKey": "disk_storage_free_gb", "title": "Sisa Penyimpanan Disk", "unit": "GB", "warningThreshold": 50, "dangerThreshold": 20, "defaultValue": 412}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 490, "y": 670, "w": 930, "h": 270, "z": 3,
                    "config": {"title": "Log Telemetri Distribusi Siaran & Status Multi-Sink", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 40. WORKFLOW 19 — IP CAMERA
    # =========================================================================
    elif template_id == "tpl_wf19_ip_camera":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 19 — Enterprise RTSP IP Camera Manager",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080C14"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "ENTERPRISE RTSP IP CAMERA MANAGER", "subtitle": "Network Bandwidth Health, Buffer Overflow & Auto-Reconnect Sentry", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 960, "h": 520, "z": 2,
                    "config": {"cameraLabel": "Stream Kamera IP Utama (Hikvision/Dahua)", "streamId": "cam_ip_main", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_vitals", "type": "system_health_vitals", "x": 1000, "y": 70, "w": 420, "h": 260, "z": 2,
                    "config": {"title": "KESEHATAN JARINGAN & SERVER"}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 1000, "y": 345, "w": 200, "h": 120, "z": 2,
                    "config": {"metricKey": "rtsp_ping_ms", "title": "Latensi Ping CCTV", "unit": "ms", "warningThreshold": 80, "dangerThreshold": 150, "defaultValue": 24}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 1220, "y": 345, "w": 200, "h": 120, "z": 2,
                    "config": {"metricKey": "packet_loss_pct", "title": "Packet Loss", "unit": "%", "warningThreshold": 2, "dangerThreshold": 5, "defaultValue": 0.0}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 610, "w": 1400, "h": 330, "z": 3,
                    "config": {"title": "Log Status Jaringan RTSP & Rekoneksi Otomatis", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 41. WORKFLOW 20 — INDUSTRIAL SURFACE & PART INSPECTION
    # =========================================================================
    elif template_id == "tpl_wf20_inspection":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Workflow 20 — Industrial Surface & Part QC Inspector",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#070E1A"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "INDUSTRIAL SURFACE & PART QC INSPECTOR", "subtitle": "Micro-Crack, Scratch & Anodizing Flaw Automated Inspection", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 920, "h": 500, "z": 2,
                    "config": {"cameraLabel": "Kamera Pembesar Inspeksi Cacat Permukaan", "streamId": "cam_surface_qc", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_gauge", "type": "live_gauge_meter", "x": 960, "y": 70, "w": 460, "h": 240, "z": 2,
                    "config": {
                        "title": "Skor Keparahan Cacat (Severity)",
                        "metricKey": "flaw_severity_score",
                        "unit": "Severity",
                        "minVal": 0,
                        "maxVal": 100,
                        "warningVal": 40,
                        "dangerVal": 70,
                        "defaultValue": 18
                    }
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 960, "y": 325, "w": 220, "h": 115, "z": 2,
                    "config": {"metricKey": "parts_inspected_today", "title": "Komponen Terinspeksi", "unit": "Part", "warningThreshold": 200, "dangerThreshold": 100, "defaultValue": 1240}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 1200, "y": 325, "w": 220, "h": 115, "z": 2,
                    "config": {"metricKey": "part_defect_rate_pct", "title": "Rasio Cacat (Defect)", "unit": "%", "warningThreshold": 2.0, "dangerThreshold": 5.0, "defaultValue": 0.48}
                },
                {
                    "id": "w_table", "type": "confidence_table", "x": 20, "y": 590, "w": 1400, "h": 350, "z": 3,
                    "config": {"title": "Tabel Cacat Permukaan Terdeteksi dengan Foto Bukti & Koordinat", "minConfidence": 0.25, "showCropThumbnail": True, "showBboxCoords": True, "exportCsv": True, "exportExcel": True}
                }
            ]
        }

    # =========================================================================
    # 42. CUSTOM WORKSHOP ZONE
    # =========================================================================
    elif template_id == "tpl_custom_workshop_zone":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Custom Workshop Zone Activity Timer Hub",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080F1B"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "CUSTOM WORKSHOP POLYGON ZONE TIMER", "subtitle": "Multi-Zone Work Elapsed Time & Non-Overlapping Presence Monitor", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 900, "h": 510, "z": 2,
                    "config": {"cameraLabel": "CCTV Area Poligon Servis Bengkel", "streamId": "cam_workshop_custom", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 940, "y": 70, "w": 480, "h": 120, "z": 2,
                    "config": {"metricKey": "zone_a_active_hours", "title": "Durasi Zona Las (Welding)", "unit": "Jam", "warningThreshold": 6, "dangerThreshold": 8, "defaultValue": 5.4}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 940, "y": 205, "w": 480, "h": 120, "z": 2,
                    "config": {"metricKey": "zone_b_active_hours", "title": "Durasi Zona Mesin (Engine)", "unit": "Jam", "warningThreshold": 6, "dangerThreshold": 8, "defaultValue": 4.8}
                },
                {
                    "id": "w_sc3", "type": "scorecard", "x": 940, "y": 340, "w": 480, "h": 120, "z": 2,
                    "config": {"metricKey": "zone_c_active_hours", "title": "Durasi Zona Detailing", "unit": "Jam", "warningThreshold": 6, "dangerThreshold": 8, "defaultValue": 3.6}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 600, "w": 1400, "h": 340, "z": 3,
                    "config": {"title": "Tabel Rekapitulasi Durasi Sesi Kerja per Zona Poligon", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # 43. CUSTOM WAREHOUSE EXIT
    # =========================================================================
    elif template_id == "tpl_custom_warehouse_exit":
        return {
            "version": "1.0.0",
            "project_id": clean_id,
            "title": "Custom Warehouse Exit Event Dispatcher",
            "theme": "dark",
            "canvas": {"width": 1440, "height": 960, "background": "#080E1A"},
            "widgets": [
                {
                    "id": "w_navbar", "type": "dashboard_navbar", "x": 0, "y": 0, "w": 1440, "h": 56, "z": 1,
                    "config": {"title": "CUSTOM WAREHOUSE EXIT EVENT SENTRY", "subtitle": "Inside-to-Outside Transition Verifier & Permanent ERP Delivery Log", "showClock": True, "showShift": True}
                },
                {
                    "id": "w_cctv", "type": "cctv_player", "x": 20, "y": 70, "w": 920, "h": 500, "z": 2,
                    "config": {"cameraLabel": "CCTV Perimeter Pintu Keluar Gudang", "streamId": "cam_wh_exit_custom", "nodeId": "preview", "showAnnotatedToggle": True, "showSnapshotBtn": True, "showFullscreenBtn": True}
                },
                {
                    "id": "w_alerts", "type": "active_alerts_list", "x": 960, "y": 70, "w": 460, "h": 260, "z": 2,
                    "config": {
                        "title": "STATUS PELEPASAN GERBANG KELUAR",
                        "alerts": [
                            {"level": "CRITICAL", "title": "Palet 1082 telah melintasi batas luar gudang", "loc": "Pintu Keluar Sektor Barat"}
                        ]
                    }
                },
                {
                    "id": "w_sc1", "type": "scorecard", "x": 960, "y": 345, "w": 220, "h": 120, "z": 2,
                    "config": {"metricKey": "confirmed_exits_today", "title": "Pelepasan Terkonfirmasi", "unit": "Barang", "warningThreshold": 50, "dangerThreshold": 100, "defaultValue": 42}
                },
                {
                    "id": "w_sc2", "type": "scorecard", "x": 1200, "y": 345, "w": 220, "h": 120, "z": 2,
                    "config": {"metricKey": "erp_push_status_pct", "title": "Keberhasilan Push ERP", "unit": "%", "warningThreshold": 95, "dangerThreshold": 90, "defaultValue": 100}
                },
                {
                    "id": "w_table", "type": "event_table", "x": 20, "y": 590, "w": 1400, "h": 350, "z": 3,
                    "config": {"title": "Log Kejadian Transisi Keluar Gerbang Lengkap dengan ID Event", "maxRows": 25, "autoScroll": True, "showFilter": True}
                }
            ]
        }

    # =========================================================================
    # FALLBACK / UNKNOWN
    # =========================================================================
    return build_template_layout("tpl_ai_cctv_pro", project_id)
