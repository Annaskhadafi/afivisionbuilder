import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Phase 2 nodes: Spatial Measurement and Classical Computer Vision', async ({ app, browser, agent }) => {
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

  // 2. Test Node: Distance Measurement
  const distLib = browser.locator('.library-item:has-text("Distance Measurement")').first();
  await expect(distLib).toBeVisible();
  await distLib.click();

  const distNode = browser.locator('.node-card:has-text("Distance Measurement")').first();
  await expect(distNode).toBeVisible();
  await browser.locator('.node-card:has-text("Distance Measurement") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Distance Measurement');
  await app.screenshot('01-distance-measurement-inspector');

  const distInfoBtn = browser.locator('.library-item:has-text("Distance Measurement") .library-info-btn').first();
  await distInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('02-distance-measurement-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 3. Test Node: Size Measurement
  const sizeLib = browser.locator('.library-item:has-text("Size Measurement")').first();
  await expect(sizeLib).toBeVisible();
  await sizeLib.click();

  const sizeNode = browser.locator('.node-card:has-text("Size Measurement")').first();
  await expect(sizeNode).toBeVisible();
  await browser.locator('.node-card:has-text("Size Measurement") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Size Measurement');
  await app.screenshot('03-size-measurement-inspector');

  const sizeInfoBtn = browser.locator('.library-item:has-text("Size Measurement") .library-info-btn').first();
  await sizeInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('04-size-measurement-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 4. Test Node: Camera Focus Health
  const focusLib = browser.locator('.library-item:has-text("Camera Focus Health")').first();
  await expect(focusLib).toBeVisible();
  await focusLib.click();

  const focusNode = browser.locator('.node-card:has-text("Camera Focus Health")').first();
  await expect(focusNode).toBeVisible();
  await browser.locator('.node-card:has-text("Camera Focus Health") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Camera Focus Health');
  await app.screenshot('05-camera-focus-inspector');

  const focusInfoBtn = browser.locator('.library-item:has-text("Camera Focus Health") .library-info-btn').first();
  await focusInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('06-camera-focus-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 5. Test Node: Auto Rotate Edges
  const rotateLib = browser.locator('.library-item:has-text("Auto Rotate Edges")').first();
  await expect(rotateLib).toBeVisible();
  await rotateLib.click();

  const rotateNode = browser.locator('.node-card:has-text("Auto Rotate Edges")').first();
  await expect(rotateNode).toBeVisible();
  await browser.locator('.node-card:has-text("Auto Rotate Edges") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Auto Rotate Edges');
  await app.screenshot('07-auto-rotate-edges-inspector');

  const rotateInfoBtn = browser.locator('.library-item:has-text("Auto Rotate Edges") .library-info-btn').first();
  await rotateInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('08-auto-rotate-edges-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 6. Visual verification
  await agent.assert('The workflow canvas contains the newly added Phase 2 nodes (Distance Measurement, Size Measurement, Camera Focus Health, Auto Rotate Edges) and the inspector displays active configuration controls.');
});
