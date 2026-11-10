import os
import re
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

WORKSPACE_DIR = r"D:\[01] PROJECT\REA\webapp"
DOCS_DIR = os.path.join(WORKSPACE_DIR, "docs")
SCREENSHOTS_DIR = os.path.join(DOCS_DIR, "screenshots")
OUTPUT_DOCX = os.path.join(DOCS_DIR, "Buku_Panduan_Lengkap_Afi_Vision_Builder_dan_OpenNVR.docx")

chapter_order = [
    ("docs/manual/BAB_01_PENGENALAN_DAN_ARSITEKTUR.md", "BAB I: PENGENALAN DAN ARSITEKTUR SISTEM"),
    ("docs/manual/BAB_02_PANDUAN_INSTALASI_DAN_DEPLOYMENT.md", "BAB II: PANDUAN INSTALASI DAN DEPLOYMENT"),
    ("docs/manual/BAB_03_WORKSPACE_STUDIO_DAN_NAVIGASI_UI.md", "BAB III: WORKSPACE STUDIO DAN NAVIGASI UI"),
    ("docs/manual/BAB_04_ENSIKLOPEDIA_NODE_PART1_SOURCES_PREPROCESSING.md", "BAB IV (BAGIAN 1): SOURCES & PREPROCESSING"),
    ("docs/manual/BAB_04_ENSIKLOPEDIA_NODE_PART2_AI_MODELS.md", "BAB IV (BAGIAN 2): AI VISION MODELS"),
    ("docs/manual/BAB_04_ENSIKLOPEDIA_NODE_PART3_TRACKING_ANALYSIS.md", "BAB IV (BAGIAN 3): TRACKING & ANALYSIS"),
    ("docs/manual/BAB_04_ENSIKLOPEDIA_NODE_PART4_LOGIC_FLOW_CONTROL.md", "BAB IV (BAGIAN 4): LOGIC & FLOW CONTROL"),
    ("docs/manual/BAB_04_ENSIKLOPEDIA_NODE_PART5_ANNOTATIONS_DRAWING.md", "BAB IV (BAGIAN 5): ANNOTATIONS & DRAWING"),
    ("docs/manual/BAB_04_ENSIKLOPEDIA_NODE_PART6_OUTPUTS_EXPORT.md", "BAB IV (BAGIAN 6): OUTPUTS, SINKS & CODE EXPORT"),
    ("docs/manual/BAB_05_EKOSISTEM_OPEN_NVR_DAN_CCTV_HUB.md", "BAB V: EKOSISTEM OPEN-NVR & CCTV HUB"),
    ("docs/manual/BAB_06_DASHBOARD_BUILDER_DAN_TELEMETRI.md", "BAB VI: DASHBOARD BUILDER & TELEMETRI"),
    ("docs/manual/BAB_07_MODEL_ZOO_DAN_QUANTIZATION.md", "BAB VII: MODEL ZOO, QUANTIZATION & CUSTOM AI"),
    ("docs/manual/BAB_08_INTEGRASI_API_MQTT_DAN_ERP.md", "BAB VIII: INTEGRASI SISTEM EKSTERNAL, MQTT & ERP"),
    ("docs/manual/BAB_09_EXPORT_CODE_DAN_EDGE_DEPLOYMENT.md", "BAB IX: EXPORT CODE & EDGE DEPLOYMENT"),
    ("docs/manual/BAB_10_STUDI_KASUS_DAN_TUTORIAL_STEP_BY_STEP.md", "BAB X: 5 STUDI KASUS END-TO-END STEP-BY-STEP"),
    ("docs/manual/BAB_11_TROUBLESHOOTING_MAINTENANCE_FAQ.md", "BAB XI: TROUBLESHOOTING, PEMELIHARAAN & FAQ")
]

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def create_styled_document():
    doc = docx.Document()
    
    # Page setup: A4, Margins 2cm
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
        # Add footer
        footer = section.footer
        f_p = footer.paragraphs[0]
        f_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        f_run = f_p.add_run("Afi Vision Builder & Integrated Open-NVR — Buku Panduan Resmi Enterprise")
        f_run.font.name = "Calibri"
        f_run.font.size = Pt(8.5)
        f_run.font.color.rgb = RGBColor(148, 163, 184)

    # ================= COVER PAGE =================
    cover_table = doc.add_table(rows=1, cols=1)
    cover_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_cell = cover_table.cell(0, 0)
    set_cell_background(c_cell, "090E17")
    set_cell_margins(c_cell, top=700, bottom=700, left=400, right=400)
    
    cp = c_cell.paragraphs[0]
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c_badge = cp.add_run("BUKU PANDUAN RESMI OPERASIONAL & PENGEMBANGAN\n")
    c_badge.font.name = "Calibri"
    c_badge.font.size = Pt(10)
    c_badge.font.bold = True
    c_badge.font.color.rgb = RGBColor(52, 211, 153)
    
    c_sp = c_cell.add_paragraph()
    c_sp.paragraph_format.space_before = Pt(20)
    c_sp.paragraph_format.space_after = Pt(10)
    c_sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c_title = c_sp.add_run("AFI VISION BUILDER &\nINTEGRATED OPEN-NVR")
    c_title.font.name = "Calibri"
    c_title.font.size = Pt(28)
    c_title.font.bold = True
    c_title.font.color.rgb = RGBColor(255, 255, 255)
    
    c_sub = c_cell.add_paragraph()
    c_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c_sub_run = c_sub.add_run("Buku Panduan Komprehensif Arsitektur, Ensiklopedia 98 Node,\nIntegrasi Enterprise ERP, dan Video Management System")
    c_sub_run.font.name = "Calibri"
    c_sub_run.font.size = Pt(12)
    c_sub_run.font.color.rgb = RGBColor(203, 213, 225)
    
    c_meta = c_cell.add_paragraph()
    c_meta.paragraph_format.space_before = Pt(40)
    c_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c_m1 = c_meta.add_run("Edisi Enterprise v3.8  •  Klasifikasi: Dokumen Operasional Resmi\n")
    c_m1.font.size = Pt(9.5)
    c_m1.font.color.rgb = RGBColor(148, 163, 184)
    c_m2 = c_meta.add_run("PT Chitra Paratama  •  Heavy Equipment & Vision AI Operations")
    c_m2.font.size = Pt(10)
    c_m2.font.bold = True
    c_m2.font.color.rgb = RGBColor(16, 185, 129)
    
    doc.add_page_break()

    # ================= DAFTAR ISI =================
    toc_h = doc.add_heading("DAFTAR ISI LENGKAP", level=1)
    toc_h.runs[0].font.color.rgb = RGBColor(15, 23, 42)
    
    for _, ch_num, ch_title in [
        ("", "BAB I", "Pengenalan dan Arsitektur Sistem Afi Vision"),
        ("", "BAB II", "Panduan Instalasi Lengkap (Bare-Metal & Docker)"),
        ("", "BAB III", "Workspace Studio, Navigasi UI & CAD Studio"),
        ("", "BAB IV (Bagian 1)", "Ensiklopedia Node: Sources & Preprocessing (19 Nodes)"),
        ("", "BAB IV (Bagian 2)", "Ensiklopedia Node: AI Vision Models (15 Nodes)"),
        ("", "BAB IV (Bagian 3)", "Ensiklopedia Node: Tracking & Kinematic Analysis (25 Nodes)"),
        ("", "BAB IV (Bagian 4)", "Ensiklopedia Node: Logic & Flow Control (15 Nodes)"),
        ("", "BAB IV (Bagian 5)", "Ensiklopedia Node: Annotations, Drawing & Visualisasi (7 Nodes)"),
        ("", "BAB IV (Bagian 6)", "Ensiklopedia Node: Outputs, Sinks & Code Export (17 Nodes)"),
        ("", "BAB V", "Ekosistem Open-NVR & CCTV Hub Terintegrasi"),
        ("", "BAB VI", "Dashboard Builder Visual & Telemetri Enterprise"),
        ("", "BAB VII", "Model Zoo, Quantization & Custom AI Runtime"),
        ("", "BAB VIII", "Integrasi Sistem Eksternal, MQTT & Enterprise ERP"),
        ("", "BAB IX", "Export Code Mandiri & Deployment Edge Headless"),
        ("", "BAB X", "Panduan Langkah Demi Langkah: 5 Studi Kasus Nyata"),
        ("", "BAB XI", "Troubleshooting, Pemeliharaan Rutin & FAQ"),
    ]:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r_ch = p.add_run(f"{ch_num:20} ")
        r_ch.font.bold = True
        r_ch.font.color.rgb = RGBColor(5, 150, 105)
        r_title = p.add_run(ch_title)
        r_title.font.color.rgb = RGBColor(30, 41, 59)
        
    doc.add_page_break()

    # ================= CHAPTERS CONTENT =================
    for filepath, ch_header in chapter_order:
        full_filepath = os.path.join(WORKSPACE_DIR, filepath)
        if not os.path.exists(full_filepath):
            continue
            
        print(f"Memproses {ch_header}...")
        
        # Add chapter heading
        ch_h = doc.add_heading(ch_header, level=1)
        ch_h.runs[0].font.color.rgb = RGBColor(15, 23, 42)
        ch_h.runs[0].font.name = "Calibri"
        ch_h.runs[0].font.bold = True
        ch_h.paragraph_format.space_before = Pt(12)
        ch_h.paragraph_format.space_after = Pt(12)
        
        with open(full_filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        in_code_block = False
        code_lines = []
        in_table = False
        table_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            sline = line.strip()
            
            # Code block toggle
            if sline.startswith("```"):
                if in_code_block:
                    # Flush code block
                    code_text = "".join(code_lines)
                    c_tbl = doc.add_table(rows=1, cols=1)
                    c_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                    cell = c_tbl.cell(0, 0)
                    set_cell_background(cell, "0F172A")
                    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
                    cp = cell.paragraphs[0]
                    cp.paragraph_format.space_before = Pt(2)
                    cp.paragraph_format.space_after = Pt(2)
                    crun = cp.add_run(code_text)
                    crun.font.name = "Consolas"
                    crun.font.size = Pt(8.5)
                    crun.font.color.rgb = RGBColor(226, 232, 240)
                    code_lines = []
                    in_code_block = False
                else:
                    in_code_block = True
                    code_lines = []
                i += 1
                continue
                
            if in_code_block:
                code_lines.append(line)
                i += 1
                continue
                
            # Table handling
            if sline.startswith("|") and sline.endswith("|"):
                table_lines.append(sline)
                i += 1
                # Check if next line is also table
                if i < len(lines) and lines[i].strip().startswith("|"):
                    continue
                else:
                    # Flush table
                    if len(table_lines) >= 2:
                        header_cols = [c.strip() for c in table_lines[0].split("|")[1:-1]]
                        # Skip delimiter line
                        data_rows = []
                        for tr in table_lines[2:]:
                            cols = [c.strip() for c in tr.split("|")[1:-1]]
                            data_rows.append(cols)
                            
                        tbl = doc.add_table(rows=len(data_rows)+1, cols=len(header_cols))
                        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                        # Header
                        for c_idx, h_text in enumerate(header_cols):
                            cell = tbl.cell(0, c_idx)
                            set_cell_background(cell, "0F172A")
                            p = cell.paragraphs[0]
                            p.paragraph_format.space_before = Pt(4)
                            p.paragraph_format.space_after = Pt(4)
                            r = p.add_run(h_text)
                            r.font.bold = True
                            r.font.color.rgb = RGBColor(255, 255, 255)
                            r.font.size = Pt(8.5)
                        # Data rows
                        for r_idx, d_row in enumerate(data_rows):
                            row_bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
                            for c_idx, val in enumerate(d_row):
                                if c_idx < len(header_cols):
                                    cell = tbl.cell(r_idx+1, c_idx)
                                    set_cell_background(cell, row_bg)
                                    p = cell.paragraphs[0]
                                    p.paragraph_format.space_before = Pt(2)
                                    p.paragraph_format.space_after = Pt(2)
                                    r = p.add_run(val)
                                    r.font.size = Pt(8.5)
                        doc.add_paragraph().paragraph_format.space_before = Pt(4)
                    table_lines = []
                    continue

            # Image handling ![alt](url)
            img_match = re.search(r'!\[(.*?)\]\((.*?)\)', sline)
            if img_match:
                alt_text = img_match.group(1)
                img_path = img_match.group(2)
                fname = os.path.basename(img_path)
                full_img_path = os.path.join(SCREENSHOTS_DIR, fname)
                if os.path.exists(full_img_path):
                    try:
                        p = doc.add_paragraph()
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p.paragraph_format.space_before = Pt(8)
                        p.paragraph_format.space_after = Pt(2)
                        p.add_run().add_picture(full_img_path, width=Inches(5.5))
                        cap_p = doc.add_paragraph()
                        cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        cap_p.paragraph_format.space_after = Pt(10)
                        cap_run = cap_p.add_run(f"Gambar: {alt_text}")
                        cap_run.font.italic = True
                        cap_run.font.size = Pt(8.5)
                        cap_run.font.color.rgb = RGBColor(100, 116, 139)
                    except Exception as e:
                        print(f"Gagal menyematkan gambar {fname}: {e}")
                i += 1
                continue

            # Alert blocks > [!NOTE], > [!IMPORTANT], > [!WARNING], > [!CAUTION]
            if sline.startswith(">"):
                alert_text = sline.lstrip("> ").strip()
                tbl = doc.add_table(rows=1, cols=1)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                cell = tbl.cell(0, 0)
                set_cell_background(cell, "F0FDF4")
                set_cell_margins(cell, top=80, bottom=80, left=150, right=150)
                ap = cell.paragraphs[0]
                ap.paragraph_format.space_before = Pt(2)
                ap.paragraph_format.space_after = Pt(2)
                arun = ap.add_run(alert_text)
                arun.font.size = Pt(9)
                arun.font.bold = True
                arun.font.color.rgb = RGBColor(6, 95, 70)
                i += 1
                continue

            # Headings
            if sline.startswith("## "):
                h2 = doc.add_heading(sline[3:], level=2)
                h2.runs[0].font.color.rgb = RGBColor(5, 150, 105)
                h2.paragraph_format.space_before = Pt(14)
                h2.paragraph_format.space_after = Pt(4)
                i += 1
                continue
            elif sline.startswith("### "):
                h3 = doc.add_heading(sline[4:], level=3)
                h3.runs[0].font.color.rgb = RGBColor(30, 41, 59)
                h3.paragraph_format.space_before = Pt(10)
                h3.paragraph_format.space_after = Pt(2)
                i += 1
                continue
            elif sline.startswith("# "):
                # Skip duplicate main title
                i += 1
                continue

            # Standard paragraph
            if sline:
                # Clean markdown bold/italic tags slightly for clean docx readability
                clean_text = sline
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.line_spacing = 1.15
                
                # Simple parsing for bold **text**
                parts = re.split(r'(\*\*.*?\*\*)', clean_text)
                for part in parts:
                    if part.startswith("**") and part.endswith("**"):
                        r = p.add_run(part[2:-2])
                        r.font.bold = True
                        r.font.name = "Calibri"
                        r.font.size = Pt(10)
                    else:
                        r = p.add_run(part)
                        r.font.name = "Calibri"
                        r.font.size = Pt(10)
                        
            i += 1
            
        doc.add_page_break()

    print(f"Menyimpan berkas DOCX ke {OUTPUT_DOCX}...")
    doc.save(OUTPUT_DOCX)
    print(f"==========================================================================")
    print(f"🎉 SUKSES BESAR! Berkas DOCX Berhasil Diterbitkan:")
    print(f"📁 Lokasi File: {OUTPUT_DOCX}")
    print(f"📊 Ukuran File: {os.path.getsize(OUTPUT_DOCX) / (1024 * 1024):.2f} MB")
    print(f"==========================================================================")

if __name__ == "__main__":
    create_styled_document()
