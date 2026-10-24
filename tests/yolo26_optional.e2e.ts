import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('YOLO26n download is opt-in and leaves YOLOv8n untouched when declined', async ({ app, browser, agent }) => {
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  const openWorkflow = browser.locator('.hub-open-workflow-btn').first();
  if (await openWorkflow.isVisible()) {
    await openWorkflow.click();
  } else {
    const templateButton = browser.locator('.hub-template-card .hub-template-btn').first();
    if (await templateButton.isVisible()) await templateButton.click();
  }
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 15000 });

  const detectorLibraryItem = browser.locator('.library-item:has-text("Object Detection")').first();
  await expect(detectorLibraryItem).toBeVisible();
  await detectorLibraryItem.click();
  const detectorNode = browser.locator('.node-card:has-text("Object Detection")').last();
  await expect(detectorNode).toBeVisible();
  await browser.locator('.node-card:has-text("Object Detection") .node-head').last().click();

  const modelInput = browser.locator('[data-field-key="modelPath"] input').first();
  await expect(modelInput).toHaveValue('yolov8n.pt');
  const downloadButton = browser.locator('.yolo26-download-btn');
  await expect(downloadButton).toBeVisible();
  await expect(browser.locator('.yolo26-download-help')).toContainText('tidak diunduh saat startup');
  await app.screenshot('01-yolo26-optional-download-control');

  await browser.evaluate(() => {
    const testWindow = window as Window & { __yolo26RequestCount?: number };
    testWindow.__yolo26RequestCount = 0;
    const originalFetch = window.fetch.bind(window);
    window.fetch = async (input, init) => {
      if (String(input).includes('/api/models/download-yolo26')) {
        testWindow.__yolo26RequestCount = (testWindow.__yolo26RequestCount || 0) + 1;
        return new Response(JSON.stringify({
          name: 'yolo26n.pt',
          path: 'C:/mock-model-store/yolo26n.pt',
          sha256: 'a'.repeat(64),
          sizeBytes: 128
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      return originalFetch(input, init);
    };
  });

  await browser.evaluate(() => { window.confirm = () => false; });
  await downloadButton.click();
  expect(await browser.evaluate(() => (window as Window & { __yolo26RequestCount?: number }).__yolo26RequestCount)).toBe(0);
  await expect(modelInput).toHaveValue('yolov8n.pt');
  await app.screenshot('02-yolo26-download-declined-default-preserved');
  await agent.assert('At this point in the flow, after declining the confirmation, the Object Detection inspector visibly shows yolov8n.pt still selected as the default and the YOLO26n download remains an optional button; no YOLO26n model path is selected.');

  await browser.evaluate(() => { window.confirm = () => true; });
  await browser.locator('.yolo26-download-btn').click();
  expect(await browser.evaluate(() => (window as Window & { __yolo26RequestCount?: number }).__yolo26RequestCount)).toBe(1);
  await expect(modelInput).toHaveValue('C:/mock-model-store/yolo26n.pt');
  await expect(browser.locator('.yolo-quickstart-badge')).toContainText('YOLO26n dipilih');
  await app.screenshot('03-yolo26-opt-in-selection-mocked');

});
