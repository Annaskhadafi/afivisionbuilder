import { test } from '@e2e-dev/web';
import { expect } from 'e2e';
import fs from 'node:fs';

test('verify Face Detector anti-spoofing and Face Crop quality nodes', async ({ app, browser }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // Open workflow from Projects Hub or switch to Studio view
  const openBtn = browser.locator('button:has-text("Buka Proyek →"), button:has-text("Open workflow →"), button:has-text("Gunakan Template →"), .project-card, #tabStudio').first();
  if (await openBtn.isVisible()) {
    await openBtn.click();
  }
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 15000 });
  await app.screenshot('01-studio-canvas');

  // 2. Add Face Detector node if not already present
  const faceDetectorLib = browser.locator('.library-item:has-text("Face Detector")').first();
  if (await faceDetectorLib.isVisible()) {
    await faceDetectorLib.click();
  }

  const faceDetectorNode = browser.locator('.node-card:has-text("Face Detector")').first();
  await expect(faceDetectorNode).toBeVisible({ timeout: 10000 });

  // Click on Face Detector node to open inspector
  await browser.locator('.node-card:has-text("Face Detector") .node-head').first().click();
  await expect(browser.locator('#inspectorBody')).toBeVisible();

  // Verify Anti-Spoofing fields in inspector
  const antiSpoofField = browser.locator('.field[data-field-key="enableAntiSpoofing"]').first();
  await expect(antiSpoofField).toBeVisible({ timeout: 5000 });
  await app.screenshot('02-face-detector-antispoof-inspector');

  // 3. Add Face Crop node from library
  const faceCropLib = browser.locator('.library-item:has-text("Face Crop")').first();
  if (await faceCropLib.isVisible()) {
    await faceCropLib.click();
  }

  const faceCropNode = browser.locator('.node-card:has-text("Face Crop")').first();
  await expect(faceCropNode).toBeVisible({ timeout: 10000 });

  // Click on Face Crop node to open inspector
  await browser.locator('.node-card:has-text("Face Crop") .node-head').first().click();
  await expect(browser.locator('#inspectorBody')).toBeVisible();

  // Verify Face Crop quality fields in inspector
  const assessQualityField = browser.locator('.field[data-field-key="assessQuality"]').first();
  await expect(assessQualityField).toBeVisible({ timeout: 5000 });
  await app.screenshot('03-face-crop-quality-inspector');

  // 4. Capture workflow canvas with Face Detector & Face Crop
  await app.screenshot('04-workflow-face-antispoof-and-crop');
});
