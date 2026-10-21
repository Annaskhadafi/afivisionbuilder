import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Velocity Calculator node functionality, inspector controls, and guidance', async ({ app, browser, agent }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // Open workflow from Projects Hub
  const openProjBtn = browser.locator('button:has-text("Buka Workflow →"), button:has-text("Open workflow →")').first();
  if (await openProjBtn.isVisible()) {
    await openProjBtn.click();
  }
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 15000 });

  // 2. Select or Add Velocity Calculator
  let velocityNode = browser.locator('.node-card:has-text("Velocity Calculator")').first();
  if (!await velocityNode.isVisible()) {
    const velocityLib = browser.locator('.library-item:has-text("Velocity Calculator")').first();
    await expect(velocityLib).toBeVisible();
    await velocityLib.click();
    velocityNode = browser.locator('.node-card:has-text("Velocity Calculator")').first();
    await expect(velocityNode).toBeVisible();
  }

  // Focus Velocity Calculator on canvas
  await browser.locator('.node-card:has-text("Velocity Calculator") .node-head').first().click();
  await app.screenshot('01-velocity-node-on-canvas');

  // 3. Inspect configuration fields
  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Velocity Calculator');

  // Verify fields are present
  await expect(browser.locator('.field[data-field-key="speedLimitKmh"]')).toBeVisible();
  await expect(browser.locator('.field[data-field-key="speedUnit"]')).toBeVisible();
  await expect(browser.locator('.field[data-field-key="minSpeedKmh"]')).toBeVisible();

  // Verify speedUnit select dropdown
  const speedUnitSelect = browser.locator('.field[data-field-key="speedUnit"] select');
  await expect(speedUnitSelect).toBeVisible();
  await speedUnitSelect.selectOption({ value: 'mps' });

  await app.screenshot('02-velocity-inspector-controls');

  // 4. Open Universal Guidance Modal
  const velocityInfoBtn = browser.locator('.library-item:has-text("Velocity Calculator") .library-info-btn').first();
  if (await velocityInfoBtn.isVisible()) {
    await velocityInfoBtn.click();
    const guideModal = browser.locator('#nodeUniversalGuideModal');
    await expect(guideModal).toBeVisible();
    await expect(guideModal).toContainText('Velocity Calculator');
    await expect(guideModal).toContainText('v = ds/dt');
    await app.screenshot('03-velocity-universal-guide-modal');
    await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();
  }

  // 5. Final assertion
  await agent.assert('Velocity Calculator node is fully functional with interactive inspector controls, speed unit options (kmh, mps, mph), deadzone noise filter, and comprehensive guidance documentation.');
});
