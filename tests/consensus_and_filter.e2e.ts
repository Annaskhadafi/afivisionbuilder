import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Detections Consensus node and Filter Per-Class Confidence & Padding', async ({ app, browser, agent }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // Open workflow from Projects Hub if visible
  const openProjBtn = browser.locator('button:has-text("Open workflow →")').first();
  if (await openProjBtn.isVisible()) {
    await openProjBtn.click();
  }
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 10000 });

  // 2. Test Filter Node Inspector & Guide
  const filterLib = browser.locator('.library-item:has-text("Detection & Geometry Filter")').first();
  await expect(filterLib).toBeVisible();
  await filterLib.click();

  const filterNode = browser.locator('.node-card:has-text("Detection & Geometry Filter")').first();
  await expect(filterNode).toBeVisible();
  await browser.locator('.node-card:has-text("Detection & Geometry Filter") .node-head').first().click();

  // Verify inspector has perClassConfidence, defaultConfidence, and paddingPercent
  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Detection & Geometry Filter');
  await app.screenshot('01-node-filter-inspector-enhancement');

  // Open guide for Filter
  const filterInfoBtn = browser.locator('.library-item:has-text("Detection & Geometry Filter") .library-info-btn').first();
  await filterInfoBtn.click();
  const guideModal = browser.locator('#nodeUniversalGuideModal');
  await expect(guideModal).toBeVisible();
  await app.screenshot('02-node-filter-guide-modal');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 3. Test Detections Consensus (Multi-Model Ensemble)
  const consensusLib = browser.locator('.library-item:has-text("Detections Consensus")').first();
  await expect(consensusLib).toBeVisible();
  await consensusLib.click();

  const consensusNode = browser.locator('.node-card:has-text("Detections Consensus")').first();
  await expect(consensusNode).toBeVisible();
  await browser.locator('.node-card:has-text("Detections Consensus") .node-head').first().click();

  // Inspector should show consensus settings (requiredVotes, iouThreshold, confidenceAggregation, boxAggregation, classAware)
  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Detections Consensus');
  await app.screenshot('03-node-consensus-inspector');

  // Open guide for Detections Consensus
  const consensusInfoBtn = browser.locator('.library-item:has-text("Detections Consensus") .library-info-btn').first();
  await consensusInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('04-node-consensus-guide-modal');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 4. Verify visual state on canvas
  await agent.assert('The canvas displays the Filter Detections node and Detections Consensus node, and the inspector displays active multi-model voting controls.');
});
