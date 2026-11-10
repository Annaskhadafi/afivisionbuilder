import os
import sys
import time

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from playwright.sync_api import sync_playwright
import engine.node_catalog as nc

OUTPUT_DIR = os.path.join(PROJECT_DIR, "docs", "screenshots", "nodes")
os.makedirs(OUTPUT_DIR, exist_ok=True)

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(edge_path):
    edge_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

print(f"Connecting with browser: {edge_path}")

all_nodes = sorted(list(nc.NODE_BLUEPRINTS.keys()))
print(f"Total nodes to capture: {len(all_nodes)}")

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=edge_path)
    page = browser.new_page(viewport={"width": 1600, "height": 950})
    page.goto("http://127.0.0.1:8765/")
    page.wait_for_selector(".brand")
    
    # Masuk ke Studio
    studio_btn = page.locator('button:has-text("Buka Workflow →"), button:has-text("Studio")').first
    if studio_btn.is_visible():
        studio_btn.click()
    page.wait_for_selector("#studioWorkflowArea")
    time.sleep(1)

    captured_count = 0
    for node_type in all_nodes:
        card_path = os.path.join(OUTPUT_DIR, f"{node_type}_card.png")
        insp_path = os.path.join(OUTPUT_DIR, f"{node_type}_inspector.png")
        
        # Eksekusi via DOM JavaScript state
        success = page.evaluate(f"""(type) => {{
            if (!state.catalog || !state.catalog[type]) return false;
            state.workflow.nodes = [];
            state.workflow.connections = [];
            addNode(type);
            if (state.workflow.nodes.length > 0) {{
                const n = state.workflow.nodes[0];
                n.x = 200;
                n.y = 150;
                selectNode(n.id);
                return true;
            }}
            return false;
        }}""", node_type)
        
        if not success:
            continue
            
        time.sleep(0.08)
        
        # Tangkap screenshot node card di kanvas
        try:
            node_el = page.locator(".node-card").first
            if node_el.is_visible():
                node_el.screenshot(path=card_path)
        except Exception as e:
            pass
            
        # Tangkap screenshot inspector panel di sebelah kanan
        try:
            insp_el = page.locator(".inspector.panel")
            if insp_el.is_visible():
                insp_el.screenshot(path=insp_path)
        except Exception as e:
            pass
            
        captured_count += 1
        if captured_count % 20 == 0 or captured_count == len(all_nodes):
            print(f"[{captured_count}/{len(all_nodes)}] Cropped node screenshots captured...")

    browser.close()

print(f"\n[SELESAI] Berhasil menangkap screenshot cropped untuk {captured_count} node di {OUTPUT_DIR}!")
