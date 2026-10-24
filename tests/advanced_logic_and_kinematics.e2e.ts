import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Phase 3 nodes: Advanced Logic, Kinematics, and Compute Throttling', async ({ app, browser, agent }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // Open workflow from Projects Hub if visible
  const openProjBtn = browser.locator('.hub-open-workflow-btn').first();
  if (await openProjBtn.isVisible()) {
    await openProjBtn.click();
  }
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 10000 });
  const guideModal = browser.locator('#nodeUniversalGuideModal');

  // 2. Test Node: Overlap Analysis
  const overlapLib = browser.locator('.library-item:has-text("Overlap Analysis")').first();
  await expect(overlapLib).toBeVisible();
  await overlapLib.click();

  const overlapNode = browser.locator('.node-card:has-text("Overlap Analysis")').first();
  await expect(overlapNode).toBeVisible();
  await browser.locator('.node-card:has-text("Overlap Analysis") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Overlap Analysis');
  await app.screenshot('01-overlap-analysis-inspector');

  const overlapInfoBtn = browser.locator('.library-item:has-text("Overlap Analysis") .library-info-btn').first();
  await overlapInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('02-overlap-analysis-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 3. Test Node: Velocity Calculator
  const velocityLib = browser.locator('.library-item:has-text("Velocity Calculator")').first();
  await expect(velocityLib).toBeVisible();
  await velocityLib.click();

  const velocityNode = browser.locator('.node-card:has-text("Velocity Calculator")').first();
  await expect(velocityNode).toBeVisible();
  await browser.locator('.node-card:has-text("Velocity Calculator") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Velocity Calculator');
  await app.screenshot('03-velocity-calculator-inspector');

  const velocityInfoBtn = browser.locator('.library-item:has-text("Velocity Calculator") .library-info-btn').first();
  await velocityInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('04-velocity-calculator-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 4. Test Node: Path Deviation Monitor
  const devLib = browser.locator('.library-item:has-text("Path Deviation Monitor")').first();
  await expect(devLib).toBeVisible();
  await devLib.click();

  const devNode = browser.locator('.node-card:has-text("Path Deviation Monitor")').first();
  await expect(devNode).toBeVisible();
  await browser.locator('.node-card:has-text("Path Deviation Monitor") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Path Deviation Monitor');
  await app.screenshot('05-path-deviation-inspector');

  const devInfoBtn = browser.locator('.library-item:has-text("Path Deviation Monitor") .library-info-btn').first();
  await devInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('06-path-deviation-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 5. Test Node: Delta Motion Filter
  const deltaLib = browser.locator('.library-item:has-text("Delta Motion Filter")').first();
  await expect(deltaLib).toBeVisible();
  await deltaLib.click();

  const deltaNode = browser.locator('.node-card:has-text("Delta Motion Filter")').first();
  await expect(deltaNode).toBeVisible();
  await browser.locator('.node-card:has-text("Delta Motion Filter") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Delta Motion Filter');
  await app.screenshot('07-delta-filter-inspector');

  const deltaInfoBtn = browser.locator('.library-item:has-text("Delta Motion Filter") .library-info-btn').first();
  await deltaInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('08-delta-filter-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 6. Test Node: Switch Case Router
  const switchLib = browser.locator('.library-item:has-text("Switch Case Router")').first();
  await expect(switchLib).toBeVisible();
  await switchLib.click();

  const switchNode = browser.locator('.node-card:has-text("Switch Case Router")').first();
  await expect(switchNode).toBeVisible();
  await browser.locator('.node-card:has-text("Switch Case Router") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Switch Case Router');
  await app.screenshot('09-switch-case-inspector');

  const switchInfoBtn = browser.locator('.library-item:has-text("Switch Case Router") .library-info-btn').first();
  await switchInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('10-switch-case-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 7. Visual verification
  await agent.assert('The workflow canvas contains the newly added Phase 3 nodes (Overlap Analysis, Velocity Calculator, Path Deviation Monitor, Delta Motion Filter, Switch Case Router) and the inspector displays active configuration controls.');
});
