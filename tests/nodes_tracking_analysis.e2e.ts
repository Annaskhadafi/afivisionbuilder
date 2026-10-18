import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Tracking and Analysis v2 nodes, inspector controls, and zone guides', async ({ app, browser, agent }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // Test Node: Object Tracking (ByteTrack / BoT-SORT / OC-SORT)
  const trackerLib = browser.locator('.library-item:has-text("Object Tracking")').first();
  await expect(trackerLib).toBeVisible();
  await trackerLib.click();

  const trackerNode = browser.locator('.node-card:has-text("Object Tracking")').first();
  await expect(trackerNode).toBeVisible();
  await browser.locator('.node-card:has-text("Object Tracking") .node-head').first().click();
  await app.screenshot('07-node-tracker-inspector');

  // Test Node: VLM Box Tracker
  const vlmTrackerLib = browser.locator('.library-item:has-text("VLM Box Tracker")').first();
  await expect(vlmTrackerLib).toBeVisible();
  await vlmTrackerLib.click();

  const vlmNode = browser.locator('.node-card:has-text("VLM Box Tracker")').first();
  await expect(vlmNode).toBeVisible();
  await browser.locator('.node-card:has-text("VLM Box Tracker") .node-head').first().click();
  await app.screenshot('08-node-vlm-box-tracker-inspector');

  // Test Node: Zone Activity Timer
  const zoneTimerLib = browser.locator('.library-item:has-text("Zone Activity Timer")').first();
  await expect(zoneTimerLib).toBeVisible();
  await zoneTimerLib.click();

  const zoneTimerNode = browser.locator('.node-card:has-text("Zone Activity Timer")').first();
  await expect(zoneTimerNode).toBeVisible();
  await browser.locator('.node-card:has-text("Zone Activity Timer") .node-head').first().click();
  await app.screenshot('09-node-zone-activity-timer-inspector');

  // Verify "Draw Zone on Preview" button is present
  const drawZoneBtn = browser.locator('button:has-text("Draw Zone on Preview")').first();
  await expect(drawZoneBtn).toBeVisible();

  // Test Guide Modal for Zone Activity Timer
  const zoneTimerInfoBtn = browser.locator('.library-item:has-text("Zone Activity Timer") .library-info-btn').first();
  await zoneTimerInfoBtn.click();
  const guideModal = browser.locator('#nodeUniversalGuideModal');
  await expect(guideModal).toBeVisible();
  await app.screenshot('10-node-zone-timer-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // Test Node: Zone Exit Event
  const zoneExitLib = browser.locator('.library-item:has-text("Zone Exit Event")').first();
  await expect(zoneExitLib).toBeVisible();
  await zoneExitLib.click();

  const zoneExitNode = browser.locator('.node-card:has-text("Zone Exit Event")').first();
  await expect(zoneExitNode).toBeVisible();
  await browser.locator('.node-card:has-text("Zone Exit Event") .node-head').first().click();
  await app.screenshot('11-node-zone-exit-inspector');

  // Test Node: Line Counter
  const lineCounterLib = browser.locator('.library-item:has-text("Line Counter")').first();
  await expect(lineCounterLib).toBeVisible();
  await lineCounterLib.click();

  const lineCounterNode = browser.locator('.node-card:has-text("Line Counter")').first();
  await expect(lineCounterNode).toBeVisible();
  await browser.locator('.node-card:has-text("Line Counter") .node-head').first().click();
  await app.screenshot('12-node-line-counter-inspector');

  // Verify visual state on canvas
  await agent.assert('The canvas contains the Tracking & Analysis nodes (Object Tracking, VLM Box Tracker, Zone Activity Timer, Zone Exit Event, Line Counter) and the inspector displays active configuration settings.');
});
