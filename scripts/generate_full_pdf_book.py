import os
import re
import base64
import markdown
from playwright.sync_api import sync_playwright

WORKSPACE_DIR = r"D:\[01] PROJECT\REA\webapp"
DOCS_DIR = os.path.join(WORKSPACE_DIR, "docs")
MANUAL_DIR = os.path.join(DOCS_DIR, "manual")
SCREENSHOTS_DIR = os.path.join(DOCS_DIR, "screenshots")
OUTPUT_PDF = os.path.join(DOCS_DIR, "Buku_Panduan_Lengkap_Afi_Vision_Builder_dan_OpenNVR.pdf")

chapter_order = [
    ("docs/manual/BAB_01_PENGENALAN_DAN_ARSITEKTUR.md", "BAB I", "Pengenalan dan Arsitektur Sistem"),
    ("docs/manual/BAB_02_PANDUAN_INSTALASI_DAN_DEPLOYMENT.md", "BAB II", "Panduan Instalasi dan Deployment"),
    ("docs/manual/BAB_03_WORKSPACE_STUDIO_DAN_NAVIGASI_UI.md", "BAB III", "Workspace Studio dan Navigasi UI"),
    ("docs/manual/BAB_04_ENSIKLOPEDIA_NODE_PART1_SOURCES_PREPROCESSING.md", "BAB IV - BAGIAN 1", "Sources & Image Preprocessing"),
    ("docs/manual/BAB_04_ENSIKLOPEDIA_NODE_PART2_AI_MODELS.md", "BAB IV - BAGIAN 2", "AI Vision Models"),
    ("docs/manual/BAB_04_ENSIKLOPEDIA_NODE_PART3_TRACKING_ANALYSIS.md", "BAB IV - BAGIAN 3", "Tracking & Kinematic Analysis"),
    ("docs/manual/BAB_04_ENSIKLOPEDIA_NODE_PART4_LOGIC_FLOW_CONTROL.md", "BAB IV - BAGIAN 4", "Logic & Flow Control"),
    ("docs/manual/BAB_04_ENSIKLOPEDIA_NODE_PART5_ANNOTATIONS_DRAWING.md", "BAB IV - BAGIAN 5", "Annotations & Visualisasi"),
    ("docs/manual/BAB_04_ENSIKLOPEDIA_NODE_PART6_OUTPUTS_EXPORT.md", "BAB IV - BAGIAN 6", "Outputs, Sinks & Code Export"),
    ("docs/manual/BAB_05_EKOSISTEM_OPEN_NVR_DAN_CCTV_HUB.md", "BAB V", "Ekosistem Open-NVR & CCTV Hub"),
    ("docs/manual/BAB_06_DASHBOARD_BUILDER_DAN_TELEMETRI.md", "BAB VI", "Dashboard Builder & Telemetri Enterprise"),
    ("docs/manual/BAB_07_MODEL_ZOO_DAN_QUANTIZATION.md", "BAB VII", "Model Zoo, Quantization & Custom AI"),
    ("docs/manual/BAB_08_INTEGRASI_API_MQTT_DAN_ERP.md", "BAB VIII", "Integrasi Sistem Eksternal, MQTT & ERP"),
    ("docs/manual/BAB_09_EXPORT_CODE_DAN_EDGE_DEPLOYMENT.md", "BAB IX", "Export Code & Edge Deployment"),
    ("docs/manual/BAB_10_STUDI_KASUS_DAN_TUTORIAL_STEP_BY_STEP.md", "BAB X", "Panduan Langkah demi Langkah: 5 Studi Kasus"),
    ("docs/manual/BAB_11_TROUBLESHOOTING_MAINTENANCE_FAQ.md", "BAB XI", "Troubleshooting, Pemeliharaan & FAQ")
]

def image_to_base64(match):
    alt_text = match.group(1)
    img_rel_path = match.group(2)
    filename = os.path.basename(img_rel_path)
    full_path = os.path.join(SCREENSHOTS_DIR, filename)
    if os.path.exists(full_path):
        ext = os.path.splitext(filename)[1].lower().replace(".", "")
        if ext == "jpg": ext = "jpeg"
        with open(full_path, "rb") as img_f:
            b64_data = base64.b64encode(img_f.read()).decode("utf-8")
        return f'<div class="figure-container"><img class="screenshot-img" src="data:image/{ext};base64,{b64_data}" alt="{alt_text}" /><div class="figure-caption"><strong>Gambar:</strong> {alt_text}</div></div>'
    return f'<div class="missing-img">[{alt_text}]</div>'

def process_alerts(html_content):
    # Process [!NOTE], [!IMPORTANT], [!WARNING], [!CAUTION]
    html_content = re.sub(
        r'<blockquote>\s*<p>\s*\[!NOTE\]\s*(.*?)</p>\s*</blockquote>',
        r'<div class="alert alert-note"><div class="alert-icon">💡 CATATAN</div><div class="alert-body">\1</div></div>',
        html_content, flags=re.DOTALL
    )
    html_content = re.sub(
        r'<blockquote>\s*<p>\s*\[!IMPORTANT\]\s*(.*?)</p>\s*</blockquote>',
        r'<div class="alert alert-important"><div class="alert-icon">⭐ PENTING</div><div class="alert-body">\1</div></div>',
        html_content, flags=re.DOTALL
    )
    html_content = re.sub(
        r'<blockquote>\s*<p>\s*\[!WARNING\]\s*(.*?)</p>\s*</blockquote>',
        r'<div class="alert alert-warning"><div class="alert-icon">⚠️ PERINGATAN</div><div class="alert-body">\1</div></div>',
        html_content, flags=re.DOTALL
    )
    html_content = re.sub(
        r'<blockquote>\s*<p>\s*\[!CAUTION\]\s*(.*?)</p>\s*</blockquote>',
        r'<div class="alert alert-caution"><div class="alert-icon">🛑 PERHATIAN KHUSUS</div><div class="alert-body">\1</div></div>',
        html_content, flags=re.DOTALL
    )
    return html_content

def build_html_book():
    print("[1/4] Mengompilasi naskah markdown dan menyematkan aset visual...")
    body_html_parts = []
    
    for filepath, ch_num, ch_title in chapter_order:
        full_filepath = os.path.join(WORKSPACE_DIR, filepath)
        if not os.path.exists(full_filepath):
            print(f"Warning: File {full_filepath} tidak ditemukan!")
            continue
            
        with open(full_filepath, "r", encoding="utf-8") as f:
            md_text = f.read()
            
        # Ganti pola gambar markdown ![alt](path) dengan base64 container
        md_text = re.sub(r'!\[(.*?)\]\((.*?)\)', image_to_base64, md_text)
        
        # Konversi markdown ke HTML
        html_part = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'nl2br'])
        html_part = process_alerts(html_part)
        
        # Bungkus chapter
        chapter_wrapper = f"""
        <div class="chapter-page">
            <div class="chapter-header-badge">{ch_num}</div>
            <div class="chapter-body">
                {html_part}
            </div>
        </div>
        """
        body_html_parts.append(chapter_wrapper)

    print(f"[2/4] Total {len(body_html_parts)} bab berhasil dirangkai ke dalam format HTML.")
    
    full_html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<title>Buku Panduan Lengkap Afi Vision Builder & Integrated Open-NVR</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

  @page {{
    size: A4;
    margin: 20mm 15mm 20mm 15mm;
  }}

  @page :left {{
    @bottom-left {{
      content: "Afi Vision Builder & Integrated Open-NVR";
      font-size: 8pt;
      color: #64748b;
      font-family: 'Plus Jakarta Sans', sans-serif;
    }}
  }}

  * {{
    box-sizing: border-box;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}

  body {{
    font-family: 'Plus Jakarta Sans', 'Segoe UI', system-ui, -apple-system, sans-serif;
    font-size: 10pt;
    line-height: 1.65;
    color: #1e293b;
    background-color: #ffffff;
    margin: 0;
    padding: 0;
  }}

  /* ================= COVER PAGE ================= */
  .cover-page {{
    page-break-after: always;
    height: 100vh;
    min-height: 250mm;
    background: radial-gradient(circle at 80% 20%, #064e3b 0%, #022c22 40%, #090e17 100%);
    color: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 25mm 20mm 20mm 20mm;
    border-radius: 4px;
    position: relative;
    overflow: hidden;
  }}

  .cover-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(16, 185, 129, 0.3);
    padding-bottom: 15px;
  }}

  .cover-badge {{
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(52, 211, 153, 0.4);
    color: #34d399;
    font-size: 8.5pt;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding: 6px 14px;
    border-radius: 9999px;
  }}

  .cover-version {{
    color: #94a3b8;
    font-size: 8.5pt;
    font-family: 'JetBrains Mono', monospace;
  }}

  .cover-center {{
    margin: auto 0;
  }}

  .cover-title {{
    font-size: 32pt;
    font-weight: 800;
    line-height: 1.15;
    margin: 0 0 16px 0;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #ffffff 30%, #a7f3d0 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}

  .cover-subtitle {{
    font-size: 13pt;
    font-weight: 400;
    line-height: 1.5;
    color: #cbd5e1;
    margin: 0 0 24px 0;
    max-width: 90%;
  }}

  .cover-tagline {{
    display: inline-block;
    color: #10b981;
    font-weight: 600;
    font-size: 10pt;
    border-left: 3px solid #10b981;
    padding-left: 12px;
  }}

  .cover-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(10px);
    padding: 16px;
    border-radius: 12px;
    margin-top: 30px;
  }}

  .cover-stat-label {{
    font-size: 7.5pt;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #94a3b8;
    margin-bottom: 4px;
  }}

  .cover-stat-val {{
    font-size: 12pt;
    font-weight: 700;
    color: #38bdf8;
  }}

  .cover-bottom {{
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 15px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    font-size: 8.5pt;
    color: #94a3b8;
  }}

  /* ================= TABLE OF CONTENTS & PREFACE ================= */
  .toc-page {{
    page-break-after: always;
    page-break-before: always;
    padding: 10mm 5mm;
  }}

  .toc-title {{
    font-size: 20pt;
    font-weight: 800;
    color: #0f172a;
    border-bottom: 2px solid #10b981;
    padding-bottom: 8px;
    margin-bottom: 24px;
  }}

  .toc-item {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 10px;
    font-size: 9.5pt;
  }}

  .toc-ch {{
    font-weight: 700;
    color: #059669;
    min-width: 140px;
  }}

  .toc-name {{
    color: #1e293b;
    font-weight: 600;
    flex-grow: 1;
    border-bottom: 1px dotted #cbd5e1;
    margin: 0 10px;
  }}

  /* ================= CHAPTER STYLING ================= */
  .chapter-page {{
    page-break-before: always;
    margin-top: 10px;
  }}

  .chapter-header-badge {{
    display: inline-block;
    background: #ecfdf5;
    border: 1px solid #10b981;
    color: #047857;
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 4px;
    margin-bottom: 8px;
  }}

  h1 {{
    font-size: 18pt;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.25;
    margin-top: 4px;
    margin-bottom: 16px;
    border-bottom: 1.5px solid #e2e8f0;
    padding-bottom: 8px;
  }}

  h2 {{
    font-size: 13pt;
    font-weight: 700;
    color: #0f172a;
    margin-top: 24px;
    margin-bottom: 12px;
    padding-left: 10px;
    border-left: 3.5px solid #10b981;
  }}

  h3 {{
    font-size: 11pt;
    font-weight: 700;
    color: #1e293b;
    margin-top: 18px;
    margin-bottom: 8px;
  }}

  p {{
    margin: 0 0 12px 0;
    text-align: justify;
  }}

  /* ================= TABLES ================= */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0 20px 0;
    font-size: 8.5pt;
    page-break-inside: avoid;
  }}

  th {{
    background-color: #0f172a;
    color: #ffffff;
    font-weight: 600;
    text-align: left;
    padding: 8px 10px;
    border: 1px solid #0f172a;
  }}

  td {{
    padding: 7px 10px;
    border: 1px solid #e2e8f0;
    vertical-align: top;
  }}

  tr:nth-child(even) td {{
    background-color: #f8fafc;
  }}

  /* ================= CODE BLOCKS ================= */
  pre {{
    background-color: #0f172a;
    color: #e2e8f0;
    padding: 12px 14px;
    border-radius: 6px;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 8pt;
    line-height: 1.45;
    overflow-x: auto;
    margin: 14px 0;
    page-break-inside: avoid;
    border: 1px solid #1e293b;
  }}

  code {{
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 8.5pt;
    background-color: #f1f5f9;
    color: #0f172a;
    padding: 1px 4px;
    border-radius: 3px;
    border: 1px solid #e2e8f0;
  }}

  pre code {{
    background-color: transparent;
    color: inherit;
    padding: 0;
    border: none;
  }}

  /* ================= ALERTS & CALLOUTS ================= */
  .alert {{
    border-radius: 8px;
    padding: 12px 14px;
    margin: 16px 0;
    page-break-inside: avoid;
    border-left: 4px solid;
    font-size: 9pt;
  }}

  .alert-icon {{
    font-weight: 700;
    font-size: 8.5pt;
    margin-bottom: 4px;
    letter-spacing: 0.05em;
  }}

  .alert-note {{
    background-color: #f0fdf4;
    border-color: #10b981;
    color: #065f46;
  }}

  .alert-important {{
    background-color: #eff6ff;
    border-color: #3b82f6;
    color: #1e40af;
  }}

  .alert-warning {{
    background-color: #fffbeb;
    border-color: #f59e0b;
    color: #92400e;
  }}

  .alert-caution {{
    background-color: #fef2f2;
    border-color: #ef4444;
    color: #991b1b;
  }}

  /* ================= FIGURES & SCREENSHOTS ================= */
  .figure-container {{
    margin: 18px 0;
    text-align: center;
    page-break-inside: avoid;
  }}

  .screenshot-img {{
    max-width: 95%;
    max-height: 110mm;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
  }}

  .figure-caption {{
    font-size: 8pt;
    color: #64748b;
    margin-top: 6px;
    font-style: italic;
  }}

  /* Footer & header in print */
  .footer-bar {{
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    display: flex;
    justify-content: space-between;
    font-size: 7.5pt;
    color: #94a3b8;
    border-top: 1px solid #e2e8f0;
    padding-top: 4px;
  }}
</style>
</head>
<body>

  <!-- ================= COVER PAGE ================= -->
  <div class="cover-page">
    <div class="cover-top">
      <div class="cover-badge">BUKU PANDUAN RESMI SISTEM OPERASIONAL</div>
      <div class="cover-version">AFI-VISION-OS v3.8 • EDISI ENTERPRISE</div>
    </div>
    
    <div class="cover-center">
      <div class="cover-tagline">DOKUMENTASI TEKNIS & PANDUAN PENGEMBANGAN SISTEM</div>
      <h1 class="cover-title">AFI VISION BUILDER & INTEGRATED OPEN-NVR</h1>
      <p class="cover-subtitle">
        Buku Panduan Komprehensif Arsitektur Perangkat Lunak, Ensiklopedia Lengkap Seluruh 98 Node, Integrasi Enterprise ERP, dan Video Management System (VMS) Skala Industri.
      </p>

      <div class="cover-grid">
        <div>
          <div class="cover-stat-label">TOTAL LINGKUP BUKU</div>
          <div class="cover-stat-val">~150 HALAMAN</div>
        </div>
        <div>
          <div class="cover-stat-label">KATALOG NODE LENGKAP</div>
          <div class="cover-stat-val">98 NODE RESMI</div>
        </div>
        <div>
          <div class="cover-stat-label">VERIFIKASI INTEGRASI</div>
          <div class="cover-stat-val">OPEN-NVR + ERP</div>
        </div>
      </div>
    </div>

    <div class="cover-bottom">
      <div>
        <strong>Penyusun:</strong> Tim Rekayasa AI & Vision Architecture<br>
        <strong>Organisasi:</strong> PT Chitra Paratama • Heavy Equipment & AI Operations
      </div>
      <div style="text-align: right;">
        <strong>Klasifikasi:</strong> Confidential / Operational Guide<br>
        <strong>Tahun Rilis:</strong> November 2026
      </div>
    </div>
  </div>

  <!-- ================= DAFTAR ISI ================= -->
  <div class="toc-page">
    <div class="toc-title">DAFTAR ISI BUKU PANDUAN</div>
    <div class="toc-item">
      <span class="toc-ch">BAB I</span>
      <span class="toc-name">Pengenalan dan Arsitektur Sistem Afi Vision</span>
      <span>Halaman 1</span>
    </div>
    <div class="toc-item">
      <span class="toc-ch">BAB II</span>
      <span class="toc-name">Panduan Instalasi Lengkap (Bare-Metal & Docker)</span>
      <span>Halaman 9</span>
    </div>
    <div class="toc-item">
      <span class="toc-ch">BAB III</span>
      <span class="toc-name">Workspace Studio, Navigasi UI & CAD Studio</span>
      <span>Halaman 18</span>
    </div>
    <div class="toc-item">
      <span class="toc-ch">BAB IV - BAG. 1</span>
      <span class="toc-name">Ensiklopedia Node: Sources & Image Preprocessing</span>
      <span>Halaman 26</span>
    </div>
    <div class="toc-item">
      <span class="toc-ch">BAB IV - BAG. 2</span>
      <span class="toc-name">Ensiklopedia Node: AI Vision Models (YOLO & LLM)</span>
      <span>Halaman 37</span>
    </div>
    <div class="toc-item">
      <span class="toc-ch">BAB IV - BAG. 3</span>
      <span class="toc-name">Ensiklopedia Node: Tracking & Kinematic Analysis</span>
      <span>Halaman 47</span>
    </div>
    <div class="toc-item">
      <span class="toc-ch">BAB IV - BAG. 4</span>
      <span class="toc-name">Ensiklopedia Node: Logic & Flow Control Nodes</span>
      <span>Halaman 61</span>
    </div>
    <div class="toc-item">
      <span class="toc-ch">BAB IV - BAG. 5</span>
      <span class="toc-name">Ensiklopedia Node: Annotations, Drawing & Visualisasi</span>
      <span>Halaman 70</span>
    </div>
    <div class="toc-item">
      <span class="toc-ch">BAB IV - BAG. 6</span>
      <span class="toc-name">Ensiklopedia Node: Outputs, Sinks & Code Export</span>
      <span>Halaman 77</span>
    </div>
    <div class="toc-item">
      <span class="toc-ch">BAB V</span>
      <span class="toc-name">Ekosistem Open-NVR & CCTV Hub Terintegrasi</span>
      <span>Halaman 88</span>
    </div>
    <div class="toc-item">
      <span class="toc-ch">BAB VI</span>
      <span class="toc-name">Dashboard Builder Visual & Telemetri Enterprise</span>
      <span>Halaman 99</span>
    </div>
    <div class="toc-item">
      <span class="toc-ch">BAB VII</span>
      <span class="toc-name">Model Zoo, Quantization & Custom AI Runtime</span>
      <span>Halaman 109</span>
    </div>
    <div class="toc-item">
      <span class="toc-ch">BAB VIII</span>
      <span class="toc-name">Integrasi Sistem Eksternal, MQTT & Enterprise ERP</span>
      <span>Halaman 117</span>
    </div>
    <div class="toc-item">
      <span class="toc-ch">BAB IX</span>
      <span class="toc-name">Export Code Mandiri & Deployment Edge Headless</span>
      <span>Halaman 126</span>
    </div>
    <div class="toc-item">
      <span class="toc-ch">BAB X</span>
      <span class="toc-name">Panduan Langkah Demi Langkah: 5 Studi Kasus Nyata</span>
      <span>Halaman 133</span>
    </div>
    <div class="toc-item">
      <span class="toc-ch">BAB XI</span>
      <span class="toc-name">Troubleshooting, Pemeliharaan Rutin & FAQ</span>
      <span>Halaman 144</span>
    </div>
  </div>

  <!-- ================= ISI KESELURUHAN BAB ================= -->
  {"".join(body_html_parts)}

</body>
</html>
"""

    temp_html_path = os.path.join(DOCS_DIR, "buku_panduan_temp.html")
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"[3/4] File HTML komposit siap di {temp_html_path}")

    # Render PDF dengan Playwright
    print("[4/4] Merender PDF profesional menggunakan Chromium Headless Engine...")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge_path):
        edge_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=edge_path)
        page = browser.new_page()
        # Muat file HTML lokal
        page.goto(f"file:///{temp_html_path.replace(os.sep, '/')}", wait_until="networkidle")
        
        # Header and footer templates
        header_template = """
        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:7pt;color:#94a3b8;width:100%;padding:0 15mm;display:flex;justify-content:space-between;border-bottom:0.5px solid #e2e8f0;padding-bottom:3px;">
          <span>AFI VISION BUILDER & INTEGRATED OPEN-NVR</span>
          <span>BUKU PANDUAN OPERASIONAL RESMI</span>
        </div>
        """
        
        footer_template = """
        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:7pt;color:#94a3b8;width:100%;padding:0 15mm;display:flex;justify-content:space-between;border-top:0.5px solid #e2e8f0;padding-top:3px;">
          <span>PT Chitra Paratama • Dokumen Resmi Enterprise</span>
          <span>Halaman <span class="pageNumber"></span> dari <span class="totalPages"></span></span>
        </div>
        """

        page.pdf(
            path=OUTPUT_PDF,
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template=header_template,
            footer_template=footer_template,
            margin={"top": "18mm", "bottom": "18mm", "left": "14mm", "right": "14mm"}
        )
        browser.close()

    if os.path.exists(temp_html_path):
        os.remove(temp_html_path)

    print(f"\n==========================================================================")
    print(f"🎉 SUKSES BESAR! Buku Panduan PDF Berhasil Diterbitkan:")
    print(f"📁 Lokasi File: {OUTPUT_PDF}")
    print(f"📊 Ukuran File: {os.path.getsize(OUTPUT_PDF) / (1024 * 1024):.2f} MB")
    print(f"==========================================================================")

if __name__ == "__main__":
    build_html_book()
