import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Object Timer node in Workflow Studio canvas and inspector', async ({ app, browser, agent }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // Open workflow from Projects Hub if visible
  const openProjBtn = browser.locator('button:has-text("Buka Workflow →"), button:has-text("Open workflow →")').first();
  if (await openProjBtn.isVisible()) {
    await openProjBtn.click();
  } else {
    const studioBtn = browser.locator('button:has-text("Studio")').first();
    if (await studioBtn.isVisible()) {
      await studioBtn.click();
    }
  }
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 10000 });
  const guideModal = browser.locator('#nodeUniversalGuideModal');

  // 2. Locate and click Object Timer in the node library under Tracking & Analysis
  const timerLib = browser.locator('.library-item:has-text("Object Timer")').first();
  await expect(timerLib).toBeVisible({ timeout: 5000 });
  await timerLib.click();

  // 3. Verify card appears on canvas and take screenshot
  const timerNode = browser.locator('.node-card:has-text("Object Timer")').first();
  await expect(timerNode).toBeVisible();
  await app.screenshot('01-object-timer-node-added');

  // 4. Click node head to open the Inspector
  await browser.locator('.node-card:has-text("Object Timer") .node-head').first().click();
  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Object Timer');
  await app.screenshot('02-object-timer-inspector');

  // 5. Open Universal Guide Modal for Object Timer
  const timerInfoBtn = browser.locator('.library-item:has-text("Object Timer") .library-info-btn').first();
  await timerInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('03-object-timer-guide-modal');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 6. Select Object Timer node again, configure Badge Position to Inside, and capture full canvas
  await browser.locator('.node-card:has-text("Object Timer") .node-head').first().click();
  await expect(browser.locator('#inspectorTitle')).toContainText('Object Timer');

  // Verify badgePosition select field is present and has valid options
  const badgePosSelect = browser.locator('.field:has-text("Posisi Badge Timer") select').first();
  await expect(badgePosSelect).toBeVisible();
  const currentVal = await badgePosSelect.inputValue();
  expect(['top', 'bottom', 'inside']).toContain(currentVal);

  await app.screenshot('04-object-timer-canvas-workflow');

  // 7. Agent verification
  await agent.assert(
    'The workflow studio canvas contains the Object Timer node under Tracking & Analysis, and its inspector displays configuration fields such as Target Classes, Alert Threshold Seconds, Timer Format, and Show Overlay.'
  );
});
