import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Sources and AI Vision Models v2 nodes, inspector controls, and guides', async ({ app, browser, agent }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // Test Node: IP Camera (Sources)
  const ipCamLib = browser.locator('.library-item:has-text("IP Camera")').first();
  await expect(ipCamLib).toBeVisible();
  await ipCamLib.click();

  const ipCamNode = browser.locator('.node-card:has-text("IP Camera")').first();
  await expect(ipCamNode).toBeVisible();
  await browser.locator('.node-card:has-text("IP Camera") .node-head').first().click();
  await app.screenshot('01-node-ip-camera-inspector');

  // Verify IP Camera Inspector fields
  await expect(browser.locator('#inspectorBody input[type="text"]').first()).toBeVisible();

  // Test Guide Modal for IP Camera
  const ipCamInfoBtn = browser.locator('.library-item:has-text("IP Camera") .library-info-btn').first();
  await ipCamInfoBtn.click();
  const guideModal = browser.locator('#nodeUniversalGuideModal');
  await expect(guideModal).toBeVisible();
  await app.screenshot('02-node-ip-camera-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // Test Node: Object Detection (AI Vision Models)
  const detectorLib = browser.locator('.library-item:has-text("Object Detection")').first();
  await expect(detectorLib).toBeVisible();
  await detectorLib.click();

  const detectorNode = browser.locator('.node-card:has-text("Object Detection")').first();
  await expect(detectorNode).toBeVisible();
  await browser.locator('.node-card:has-text("Object Detection") .node-head').first().click();
  await app.screenshot('03-node-detector-inspector');

  // Test Node: Visual Inspection (EfficientAD)
  const effAdLib = browser.locator('.library-item:has-text("Visual Inspection")').first();
  await expect(effAdLib).toBeVisible();
  await effAdLib.click();

  const effAdNode = browser.locator('.node-card:has-text("Visual Inspection")').first();
  await expect(effAdNode).toBeVisible();
  await browser.locator('.node-card:has-text("Visual Inspection") .node-head').first().click();
  await app.screenshot('04-node-efficientad-inspector');

  // Test Node: Barcode & QR Reader
  const barcodeLib = browser.locator('.library-item:has-text("Barcode & QR Reader")').first();
  await expect(barcodeLib).toBeVisible();
  await barcodeLib.click();

  const barcodeNode = browser.locator('.node-card:has-text("Barcode & QR Reader")').first();
  await expect(barcodeNode).toBeVisible();
  await browser.locator('.node-card:has-text("Barcode & QR Reader") .node-head').first().click();
  await app.screenshot('05-node-barcode-inspector');

  // Open guide for Barcode Reader
  const barcodeInfoBtn = browser.locator('.library-item:has-text("Barcode & QR Reader") .library-info-btn').first();
  await barcodeInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('06-node-barcode-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // Verify visual state on canvas
  await agent.assert('The canvas contains the created nodes (IP Camera, Object Detection, Visual Inspection, Barcode & QR Reader) and the inspector displays active configuration settings for the currently selected node.');
});
