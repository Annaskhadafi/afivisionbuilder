import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify OCR Text Reader (ONNX) node in Workflow Studio', async ({ app, browser, agent }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // Open workflow from Projects Hub if visible
  const openProjBtn = browser.locator('button:has-text("Open workflow →")').first();
  if (await openProjBtn.isVisible()) {
    await openProjBtn.click();
  }
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 10000 });
  const guideModal = browser.locator('#nodeUniversalGuideModal');

  // 2. Locate and click OCR Text Reader (ONNX) in the node library
  const ocrLib = browser.locator('.library-item:has-text("OCR Text Reader (ONNX)")').first();
  await expect(ocrLib).toBeVisible();
  await ocrLib.click();

  // 3. Verify card appears on canvas and open inspector
  const ocrNode = browser.locator('.node-card:has-text("OCR Text Reader (ONNX)")').first();
  await expect(ocrNode).toBeVisible();
  await browser.locator('.node-card:has-text("OCR Text Reader (ONNX)") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('OCR Text Reader (ONNX)');
  await app.screenshot('01-ocr-reader-inspector');

  // 4. Open Universal Guide Modal for OCR Text Reader
  const ocrInfoBtn = browser.locator('.library-item:has-text("OCR Text Reader (ONNX)") .library-info-btn').first();
  await ocrInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('02-ocr-reader-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 5. Select OCR node again and capture full canvas
  await browser.locator('.node-card:has-text("OCR Text Reader (ONNX)") .node-head').first().click();
  await expect(browser.locator('#inspectorTitle')).toContainText('OCR Text Reader (ONNX)');
  await app.screenshot('03-ocr-reader-canvas');

  // 6. Agent verification
  await agent.assert(
    'The workflow canvas contains the OCR Text Reader (ONNX) node and its inspector displays the ultra-lightweight ONNX OCR configuration fields such as recognition model path, detection model path, and character whitelist.'
  );
});
