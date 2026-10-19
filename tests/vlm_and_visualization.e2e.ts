import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Phase 4 nodes: Advanced Visualization, Model Diff, and VLM', async ({ app, browser, agent }) => {
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

  // 2. Test Node: Model Comparison Diff
  const modelCompLib = browser.locator('.library-item:has-text("Model Comparison Diff")').first();
  await expect(modelCompLib).toBeVisible();
  await modelCompLib.click();

  const modelCompNode = browser.locator('.node-card:has-text("Model Comparison Diff")').first();
  await expect(modelCompNode).toBeVisible();
  await browser.locator('.node-card:has-text("Model Comparison Diff") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Model Comparison Diff');
  await app.screenshot('01-model-comparison-inspector');

  const modelCompInfoBtn = browser.locator('.library-item:has-text("Model Comparison Diff") .library-info-btn').first();
  await modelCompInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('02-model-comparison-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 3. Test Node: Detections Difference
  const diffLib = browser.locator('.library-item:has-text("Detections Difference")').first();
  await expect(diffLib).toBeVisible();
  await diffLib.click();

  const diffNode = browser.locator('.node-card:has-text("Detections Difference")').first();
  await expect(diffNode).toBeVisible();
  await browser.locator('.node-card:has-text("Detections Difference") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Detections Difference');
  await app.screenshot('03-detections-difference-inspector');

  const diffInfoBtn = browser.locator('.library-item:has-text("Detections Difference") .library-info-btn').first();
  await diffInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('04-detections-difference-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 4. Test Overlay / Annotate Node with new layers (Motion Trace & Corner Bracket)
  const overlayLib = browser.locator('.library-item:has-text("Overlay / Annotate")').first();
  if (await overlayLib.isVisible()) {
    await overlayLib.click();
    const overlayNode = browser.locator('.node-card:has-text("Overlay / Annotate")').first();
    await expect(overlayNode).toBeVisible();
    await browser.locator('.node-card:has-text("Overlay / Annotate") .node-head').first().click();
    await app.screenshot('05-overlay-annotate-inspector');
  }

  // 5. Select Model Comparison Diff to show its inspector parameters
  await browser.locator('.node-card:has-text("Model Comparison Diff") .node-head').first().click();
  await expect(browser.locator('#inspectorTitle')).toContainText('Model Comparison Diff');
  await app.screenshot('06-model-comparison-selected-canvas');

  // 6. Agent verification
  await agent.assert(
    'The workflow canvas contains the Phase 4 nodes (Model Comparison Diff and Detections Difference) and the node inspector displays the Model Comparison Diff configuration options (such as Model A and Model B names).'
  );
});
