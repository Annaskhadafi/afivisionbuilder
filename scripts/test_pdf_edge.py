import os
from playwright.sync_api import sync_playwright

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(edge_path):
    edge_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

print(f"Using browser: {edge_path}")

html_content = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {
    size: A4;
    margin: 20mm;
  }
  body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    color: #1e293b;
    line-height: 1.6;
  }
  h1 {
    color: #0f172a;
    border-bottom: 2px solid #10b981;
    padding-bottom: 8px;
  }
  .card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 16px;
    margin-top: 16px;
  }
</style>
</head>
<body>
  <h1>Afi Vision Builder & Integrated Open-NVR</h1>
  <p>Pengujian pembuatan dokumen PDF via Playwright & Edge Headless.</p>
  <div class="card">
    <h3>Status: Berhasil</h3>
    <p>Dokumen ini dirender dengan styling CSS A4 presisi tinggi.</p>
  </div>
</body>
</html>
"""

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=edge_path)
    page = browser.new_page()
    page.set_content(html_content, wait_until="networkidle")
    pdf_path = "test_output.pdf"
    page.pdf(path=pdf_path, format="A4", print_background=True)
    browser.close()

print(f"Generated: {os.path.exists(pdf_path)}, Size: {os.path.getsize(pdf_path)} bytes")
