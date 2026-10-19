import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify n8n-style node activation toggle and execution telemetry logs', async ({ app, browser, agent }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // Open workflow from Projects Hub if visible
  const openProjBtn = browser.locator('button:has-text("Open workflow →")').first();
  if (await openProjBtn.isVisible()) {
    await openProjBtn.click();
  }
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 10000 });

  // 2. Verify Canvas Node Cards have 1-Click Toggle Switch and Status Bar Footer
  const firstNode = browser.locator('.node-card').first();
  await expect(firstNode).toBeVisible();

  const toggleSlider = browser.locator('.node-card .toggle-slider').first();
  await expect(toggleSlider).toBeVisible();

  const statusBar = browser.locator('.node-card .node-status-bar').first();
  await expect(statusBar).toBeVisible();

  await app.screenshot('01-n8n-canvas-node-toggle');

  // 3. Toggle off the node to enter Bypass Mode
  await toggleSlider.click();
  const disabledNode = browser.locator('.node-card.node-disabled').first();
  await expect(disabledNode).toBeVisible();
  await expect(browser.locator('.node-card .node-bypassed-badge').first()).toBeVisible();
  await expect(statusBar).toContainText('BYPASSED');

  await app.screenshot('02-n8n-node-bypassed');

  // 4. Click the node card header to open Inspector
  await browser.locator('.node-card .node-head strong').first().click();
  await expect(browser.locator('#inspectorBody')).toBeVisible();

  // 5. Verify Inspector Active Row & Data & Logs tab
  const inspectorActiveRow = browser.locator('.inspector-active-row');
  await expect(inspectorActiveRow).toBeVisible();
  await expect(inspectorActiveRow).toContainText('Node Bypassed');

  const logsTabBtn = browser.locator('.inspector-tab-btn:has-text("Data & Logs")');
  await expect(logsTabBtn).toBeVisible();

  // 6. Switch to "Data & Logs" Tab
  await logsTabBtn.click();
  await expect(browser.locator('.telemetry-hud')).toBeVisible();
  await expect(browser.locator('.payload-box').first()).toBeVisible();
  await expect(browser.locator('button:has-text("Copy Full JSON Payload")')).toBeVisible();

  await app.screenshot('03-n8n-inspector-data-logs');

  // 7. Toggle node back to active to verify real-time canvas & inspector synchronization
  const inspectorSlider = browser.locator('.inspector-active-row .toggle-slider').first();
  await inspectorSlider.click();
  await expect(inspectorActiveRow).toContainText('Node Aktif');
  await expect(browser.locator('.node-card:not(.node-disabled)').first()).toBeVisible();

  await app.screenshot('04-n8n-node-reactivated');

  // 8. Agent verification
  await agent.assert(
    'The workflow interface supports n8n-style node activation with 1-click toggle switches on canvas cards, bypassed visual styling, live status bars, and an inspector Data & Logs tab with telemetry HUD and payload explorer.'
  );
});
