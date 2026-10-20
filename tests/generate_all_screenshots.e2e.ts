import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('capture updated high-resolution screenshots for README', async ({ app, browser }) => {
  // 1. Projects Hub (Landing View)
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible({ timeout: 10000 });
  await app.screenshot('01_projects_hub');

  // 2. Open Workflow Studio
  const openProjBtn = browser.locator('button:has-text("Buka Workflow →"), button:has-text("Open workflow →")').first();
  if (await openProjBtn.isVisible()) {
    await openProjBtn.click();
  } else {
    const studioBtn = browser.locator('button:has-text("Studio")').first();
    if (await studioBtn.isVisible()) {
      await studioBtn.click();
    }
  }
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 10000 });
  await app.screenshot('02_studio_canvas');
  await app.screenshot('03_restaurant_live_tracking');

  // 3. Face Registry Page
  const facesRailBtn = browser.locator('#railTabFaces');
  if (await facesRailBtn.isVisible()) {
    await facesRailBtn.click();
    await expect(browser.locator('#viewFaceRegistry')).toBeVisible({ timeout: 5000 });
    await app.screenshot('16_face_registry_gallery');
  }

  // 4. Enroll Face Modal
  const enrollBtn = browser.locator('#faceEnrollBtn');
  if (await enrollBtn.isVisible()) {
    await enrollBtn.click();
    await expect(browser.locator('#enrollFaceModal')).toBeVisible({ timeout: 5000 });
    await browser.locator('#enrollNameInput').fill('Budi Santoso');
    await browser.locator('#enrollRoleInput').fill('Supervisor Workshop Bay 1');
    await app.screenshot('17_enroll_face_modal');
    await browser.locator('#closeEnrollModalBtn').click();
  }

  // 5. Back to Workflow and Add UniFace & Object Timer nodes
  const workflowRailBtn = browser.locator('#railTabWorkflow');
  await workflowRailBtn.click();
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 5000 });

  // Add Face Detector & Face Tracker
  const faceDetectorLib = browser.locator('.library-item:has-text("Face Detector")').first();
  if (await faceDetectorLib.isVisible()) await faceDetectorLib.click();

  const faceTrackerLib = browser.locator('.library-item:has-text("Face Re-ID Tracker")').first();
  if (await faceTrackerLib.isVisible()) await faceTrackerLib.click();

  const objectTimerLib = browser.locator('.library-item:has-text("Object Timer")').first();
  if (await objectTimerLib.isVisible()) await objectTimerLib.click();

  await app.screenshot('18_uniface_and_timer_canvas');

  // 6. Open Face Tracker Inspector
  const trackerHead = browser.locator('.node-card:has-text("Face Re-ID Tracker") .node-head').first();
  if (await trackerHead.isVisible()) {
    await trackerHead.click();
    await expect(browser.locator('#inspectorBody')).toBeVisible({ timeout: 5000 });
    await app.screenshot('19_face_tracker_inspector');
  }

  // 7. Models Registry Manager
  const modelsRailBtn = browser.locator('#railTabModels');
  if (await modelsRailBtn.isVisible()) {
    await modelsRailBtn.click();
    await expect(browser.locator('#viewModelManager')).toBeVisible({ timeout: 5000 });
    await app.screenshot('10_models_registry');
  }

  // 8. Model Quantizer Modal
  const quantizerBtn = browser.locator('#modelsQuantizeBtn, button:has-text("Quantize"), button:has-text("Kuantisasi")').first();
  if (await quantizerBtn.isVisible()) {
    await quantizerBtn.click();
    await expect(browser.locator('#modelQuantizerModal')).toBeVisible({ timeout: 5000 });
    await app.screenshot('11_model_quantizer');
    await browser.locator('#closeQuantizerModalBtn').click();
  }

  // 9. Live Cameras Grid
  const liveCamBtn = browser.locator('button:has-text("Live Cameras")').first();
  if (await liveCamBtn.isVisible()) {
    await liveCamBtn.click();
    await expect(browser.locator('#viewLiveCameras')).toBeVisible({ timeout: 5000 });
    await app.screenshot('06_live_cctv_matrix');
  }

  // 10. Workshop Sessions
  const wsBtn = browser.locator('button:has-text("Workshop Sessions")').first();
  if (await wsBtn.isVisible()) {
    await wsBtn.click();
    await expect(browser.locator('#viewWorkshopSessions')).toBeVisible({ timeout: 5000 });
    await app.screenshot('08_workshop_sessions');
  }

  // 11. Warehouse Events
  const whBtn = browser.locator('button:has-text("Warehouse Events")').first();
  if (await whBtn.isVisible()) {
    await whBtn.click();
    await expect(browser.locator('#viewWarehouseEvents')).toBeVisible({ timeout: 5000 });
    await app.screenshot('09_warehouse_events');
  }
});
