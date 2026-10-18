import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Logic, Flow Control, and Output v2 nodes, inspector controls, and guides', async ({ app, browser, agent }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // Test Node: If / Else (Logic & Flow Control)
  const ifElseLib = browser.locator('.library-item:has-text("If / Else")').first();
  await expect(ifElseLib).toBeVisible();
  await ifElseLib.click();

  const ifElseNode = browser.locator('.node-card:has-text("If / Else")').first();
  await expect(ifElseNode).toBeVisible();
  await browser.locator('.node-card:has-text("If / Else") .node-head').first().click();
  await app.screenshot('18-node-if-else-inspector');

  // Test Guide Modal for If / Else
  const ifElseInfoBtn = browser.locator('.library-item:has-text("If / Else") .library-info-btn').first();
  await ifElseInfoBtn.click();
  const ifElseModal = browser.locator('#ifElseGuideModal, #nodeUniversalGuideModal').first();
  await expect(ifElseModal).toBeVisible();
  await app.screenshot('19-node-if-else-guide');
  const closeBtn = browser.locator('#ifElseGuideModal button:has-text("✕"), #nodeUniversalGuideModal button:has-text("✕")').first();
  await closeBtn.click();

  // Test Node: ROI Filter
  const roiLib = browser.locator('.library-item:has-text("ROI Filter")').first();
  await expect(roiLib).toBeVisible();
  await roiLib.click();

  const roiNode = browser.locator('.node-card:has-text("ROI Filter")').first();
  await expect(roiNode).toBeVisible();
  await browser.locator('.node-card:has-text("ROI Filter") .node-head').first().click();
  await app.screenshot('20-node-roi-filter-inspector');

  // Test Node: Alert Output (Outputs & Export)
  const alertLib = browser.locator('.library-item:has-text("Alert Output")').first();
  await expect(alertLib).toBeVisible();
  await alertLib.click();

  const alertNode = browser.locator('.node-card:has-text("Alert Output")').first();
  await expect(alertNode).toBeVisible();
  await browser.locator('.node-card:has-text("Alert Output") .node-head').first().click();
  await app.screenshot('21-node-alert-inspector');

  // Test Node: Save Images (image_output)
  const saveImagesLib = browser.locator('.library-item:has-text("Save Images")').first();
  await expect(saveImagesLib).toBeVisible();
  await saveImagesLib.click();

  const saveImagesNode = browser.locator('.node-card:has-text("Save Images")').first();
  await expect(saveImagesNode).toBeVisible();
  await browser.locator('.node-card:has-text("Save Images") .node-head').first().click();
  await app.screenshot('22-node-save-images-inspector');

  // Test Node: Database Output
  const dbOutputLib = browser.locator('.library-item:has-text("Database Output")').first();
  await expect(dbOutputLib).toBeVisible();
  await dbOutputLib.click();

  const dbOutputNode = browser.locator('.node-card:has-text("Database Output")').first();
  await expect(dbOutputNode).toBeVisible();
  await browser.locator('.node-card:has-text("Database Output") .node-head').first().click();
  await app.screenshot('23-node-database-output-inspector');

  // Verify Database Output buttons (Export CSV, View Logs)
  await expect(browser.locator('button:has-text("Export CSV")').first()).toBeVisible();
  await expect(browser.locator('button:has-text("View Logs")').first()).toBeVisible();

  // Test Node: Webhook / HTTP Outbound
  const webhookLib = browser.locator('.library-item:has-text("Webhook")').first();
  await expect(webhookLib).toBeVisible();
  await webhookLib.click();

  const webhookNode = browser.locator('.node-card:has-text("Webhook")').first();
  await expect(webhookNode).toBeVisible();
  await browser.locator('.node-card:has-text("Webhook") .node-head').first().click();
  await app.screenshot('24-node-webhook-inspector');

  // Verify visual state on canvas
  await agent.assert('The canvas contains the created Logic & Flow Control and Output nodes (If/Else, ROI Filter, Alert, Save Images, Database Output, Webhook).');
});
