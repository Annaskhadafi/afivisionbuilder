import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Preprocessing and Drawing v2 nodes, Python Script editor, and inspector', async ({ app, browser, agent }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // Test Node: Brightness / Contrast
  const bcLib = browser.locator('.library-item:has-text("Brightness / Contrast")').first();
  await expect(bcLib).toBeVisible();
  await bcLib.click();

  const bcNode = browser.locator('.node-card:has-text("Brightness / Contrast")').first();
  await expect(bcNode).toBeVisible();
  await browser.locator('.node-card:has-text("Brightness / Contrast") .node-head').first().click();
  await app.screenshot('13-node-brightness-contrast-inspector');

  // Test Node: Custom Python Script
  const pyLib = browser.locator('.library-item:has-text("Custom Python Script")').first();
  await expect(pyLib).toBeVisible();
  await pyLib.click();

  const pyNode = browser.locator('.node-card:has-text("Custom Python Script")').first();
  await expect(pyNode).toBeVisible();
  await browser.locator('.node-card:has-text("Custom Python Script") .node-head').first().click();
  await app.screenshot('14-node-python-script-inspector');

  // Verify python textarea and Check Script button
  const pyTextarea = browser.locator('#inspectorBody textarea').first();
  await expect(pyTextarea).toBeVisible();
  const checkScriptBtn = browser.locator('#inspectorBody button:has-text("Check Script")').first();
  await expect(checkScriptBtn).toBeVisible();

  // Test Guide Modal for Custom Python Script
  const pyInfoBtn = browser.locator('.library-item:has-text("Custom Python Script") .library-info-btn').first();
  await pyInfoBtn.click();
  const guideModal = browser.locator('#nodeUniversalGuideModal');
  await expect(guideModal).toBeVisible();
  await app.screenshot('15-node-python-script-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // Test Node: Privacy Blur (Annotations & Drawing)
  const blurAnonLib = browser.locator('.library-item:has-text("Privacy Blur")').first();
  await expect(blurAnonLib).toBeVisible();
  await blurAnonLib.click();

  const blurAnonNode = browser.locator('.node-card:has-text("Privacy Blur")').first();
  await expect(blurAnonNode).toBeVisible();
  await browser.locator('.node-card:has-text("Privacy Blur") .node-head').first().click();
  await app.screenshot('16-node-privacy-blur-inspector');

  // Test Node: Overlay / Annotate
  const overlayLib = browser.locator('.library-item:has-text("Overlay / Annotate")').first();
  await expect(overlayLib).toBeVisible();
  await overlayLib.click();

  const overlayNode = browser.locator('.node-card:has-text("Overlay / Annotate")').first();
  await expect(overlayNode).toBeVisible();
  await browser.locator('.node-card:has-text("Overlay / Annotate") .node-head').first().click();
  await app.screenshot('17-node-overlay-inspector');

  // Verify visual state on canvas
  await agent.assert('The canvas contains the created Preprocessing and Drawing nodes (Brightness / Contrast, Custom Python Script, Privacy Blur, and Overlay / Annotate).');
});
