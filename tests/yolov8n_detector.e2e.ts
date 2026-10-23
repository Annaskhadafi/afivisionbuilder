import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Object Detection node comes pre-selected with YOLOv8n ready for first-time users', async ({ app, browser, agent }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // 2. Open workflow studio from Projects Hub
  const openProjBtn = browser.locator('button:has-text("Buka Workflow →"), button:has-text("Open workflow →")').first();
  if (await openProjBtn.isVisible()) {
    await openProjBtn.click();
  } else {
    const studioBtn = browser.locator('button:has-text("Studio")').first();
    if (await studioBtn.isVisible()) {
      await studioBtn.click();
    }
  }
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 15000 });
  await app.screenshot('01-workflow-studio-canvas');

  // 3. Check Library item for Object Detection
  const detectorLib = browser.locator('.library-item:has-text("Object Detection")').first();
  await expect(detectorLib).toBeVisible({ timeout: 10000 });
  await app.screenshot('02-library-detector-yolov8n-badge');

  // 4. Click Object Detection in Library to add a node (or inspect existing one)
  await detectorLib.click();
  const detectorNode = browser.locator('.node-card:has-text("Object Detection")').last();
  await expect(detectorNode).toBeVisible();

  // 5. Click the Object Detection node header to open the Inspector
  await browser.locator('.node-card:has-text("Object Detection") .node-head').last().click();
  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Object Detection');

  // 6. Verify Engine is pre-selected with Ultralytics YOLOv8n
  const engineSelect = browser.locator('[data-field-key="engine"] select');
  await expect(engineSelect).toBeVisible();
  const selectedEngine = await engineSelect.inputValue();
  expect(selectedEngine).toBe('ultralytics_yolo');

  // 7. Verify Model Path input is pre-populated with yolov8n.pt
  const modelInput = browser.locator('[data-field-key="modelPath"] input, [data-field-key="customModelPath"] input').first();
  await expect(modelInput).toBeVisible();
  const modelVal = await modelInput.inputValue();
  expect(modelVal).toBe('yolov8n.pt');

  // 8. Verify the friendly beginner-ready banner is displayed
  const quickstartBadge = browser.locator('.yolo-quickstart-badge');
  await expect(quickstartBadge).toBeVisible();
  await expect(quickstartBadge).toContainText('YOLOv8n Siap Pakai');

  // 9. Capture screenshot proving pre-selection out of the box
  await app.screenshot('03-yolov8n-preselected-inspector');
});
