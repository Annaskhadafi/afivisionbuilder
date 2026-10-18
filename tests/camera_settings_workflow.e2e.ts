import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Camera Settings modal, workflow auto-binding, and adding new CCTV camera', async ({ app, browser }) => {
  // 1. Open Application and Navigate to Live Cameras Dashboard
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // If in Projects Hub, open studio or switch to Live Cameras directly via topbar
  await expect(browser.locator('#tabLiveCameras')).toBeVisible();
  await browser.locator('#tabLiveCameras').click();

  // 2. Verify Live Cameras Matrix and Toolbar
  await expect(browser.locator('#viewLiveCameras')).toBeVisible();
  await expect(browser.locator('#viewProjectsHub')).toBeHidden();
  await expect(browser.locator('#cameraGridContainer .camera-card').first()).toBeVisible();
  await expect(browser.locator('#btnAddNewCamera')).toBeVisible();

  // Verify camera settings button exists on WS-01 card
  const ws01SettingsBtn = browser.locator('[data-settings-cam="WS-01"]').first();
  await expect(ws01SettingsBtn).toBeVisible();

  // Take Screenshot 1: CCTV Matrix with settings buttons
  await app.screenshot('01-cctv-matrix-with-settings');

  // 3. Open Camera Settings Modal for WS-01
  await ws01SettingsBtn.click();
  await expect(browser.locator('#cameraSettingsModal')).toBeVisible();
  await expect(browser.locator('#cameraSettingsModalTitle')).toContainText('WS-01');

  // Verify modal form fields are pre-filled
  await expect(browser.locator('#camEditName')).toHaveValue('Workshop Bay 1');
  await expect(browser.locator('#camEditStreamUrl')).toHaveValue('rtsp://192.168.1.101:554/live');
  await expect(browser.locator('#camEditType')).toHaveValue('workshop');
  await expect(browser.locator('#camAutoGenerateWorkflowBtn')).toBeVisible();

  // Take Screenshot 2: Camera Settings Modal
  await app.screenshot('02-camera-settings-modal');

  // 4. Auto-generate Project Workflow from Template
  await browser.locator('#camAutoGenerateWorkflowBtn').click();

  // Wait for binding to complete and Buka di Studio + Gambar Poligon Area buttons to appear
  await expect(browser.locator('#camOpenInStudioBtn')).toBeVisible();
  await expect(browser.locator('#camDrawPolygonBtn')).toBeVisible();
  await expect(browser.locator('#camWorkflowStatusHint')).toContainText('Terhubung ke workflow');

  // Take Screenshot 3: Workflow Auto-Generated & Bound with Draw Polygon Button
  await app.screenshot('03-workflow-auto-generated-with-draw-polygon');

  // 5. Click "Gambar Poligon Area" to jump directly into Studio with Zone Polygon Editor active
  await browser.locator('#camDrawPolygonBtn').click();
  await expect(browser.locator('#cameraSettingsModal')).toBeHidden();
  await expect(browser.locator('#viewStudio')).toBeVisible();
  await expect(browser.locator('#projectLeftRail')).toBeVisible();
  await expect(browser.locator('#railTabWorkflow')).toBeVisible();

  // Verify Zone Activity Timer node is selected and SVG polygon editor is mounted on preview
  await expect(browser.locator('.zone-preview-editor')).toBeVisible({ timeout: 6000 });
  await expect(browser.locator('.zone-preview-toolbar')).toBeVisible();
  await expect(browser.locator('.zone-preview-vertex').first()).toBeVisible();

  // Take Screenshot 4: Interactive Polygon Drawing Tool Active on Preview Frame
  await app.screenshot('04-polygon-drawing-active');

  // Click "Simpan zona" to save configured polygon
  const saveZoneBtn = browser.locator('.zone-preview-toolbar button:has-text("Simpan zona")');
  await expect(saveZoneBtn).toBeVisible();
  await saveZoneBtn.click();
  await expect(browser.locator('.zone-preview-editor')).toBeHidden();

  // Take Screenshot 5: Polygon Saved and Workflow Canvas Active
  await app.screenshot('05-polygon-saved-canvas');

  // 6. Switch Back to Live Cameras and Add a New Camera
  await browser.locator('#tabLiveCameras').click();
  await expect(browser.locator('#viewLiveCameras')).toBeVisible();

  await browser.locator('#btnAddNewCamera').click();
  await expect(browser.locator('#cameraSettingsModal')).toBeVisible();
  await expect(browser.locator('#cameraSettingsModalTitle')).toContainText('Tambah Kamera');

  // Fill in new camera fields
  await browser.locator('#camEditName').fill('Workshop Bay 6 (Inspection)');
  await browser.locator('#camEditStreamUrl').fill('rtsp://192.168.1.106:554/live');
  await browser.locator('#camEditZone').fill('Bay 6 Area');

  // Save new camera
  await browser.locator('#saveCameraSettingsBtn').click();
  await expect(browser.locator('#cameraSettingsModal')).toBeHidden();

  // Verify new camera card is rendered in matrix
  await expect(browser.locator('.camera-card:has-text("Workshop Bay 6")').first()).toBeVisible();

  // Take Screenshot 6: New Camera Added to Matrix
  await app.screenshot('06-new-camera-card-added');
});
