import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Phase 5 nodes: Cloud Sinks, Aggregation, and PTZ Controller', async ({ app, browser, agent }) => {
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

  // 2. Test Node: Data Aggregator (Rollup)
  const aggLib = browser.locator('.library-item:has-text("Data Aggregator (Rollup)")').first();
  await expect(aggLib).toBeVisible();
  await aggLib.click();

  const aggNode = browser.locator('.node-card:has-text("Data Aggregator (Rollup)")').first();
  await expect(aggNode).toBeVisible();
  await browser.locator('.node-card:has-text("Data Aggregator (Rollup)") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Data Aggregator (Rollup)');
  await app.screenshot('01-data-aggregator-inspector');

  const aggInfoBtn = browser.locator('.library-item:has-text("Data Aggregator (Rollup)") .library-info-btn').first();
  await aggInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('02-data-aggregator-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 3. Test Node: CSV Formatter
  const csvLib = browser.locator('.library-item:has-text("CSV Formatter")').first();
  await expect(csvLib).toBeVisible();
  await csvLib.click();

  const csvNode = browser.locator('.node-card:has-text("CSV Formatter")').first();
  await expect(csvNode).toBeVisible();
  await browser.locator('.node-card:has-text("CSV Formatter") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('CSV Formatter');
  await app.screenshot('03-csv-formatter-inspector');

  const csvInfoBtn = browser.locator('.library-item:has-text("CSV Formatter") .library-info-btn').first();
  await csvInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('04-csv-formatter-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 4. Test Node: S3 Cloud Sink
  const s3Lib = browser.locator('.library-item:has-text("S3 Cloud Sink")').first();
  await expect(s3Lib).toBeVisible();
  await s3Lib.click();

  const s3Node = browser.locator('.node-card:has-text("S3 Cloud Sink")').first();
  await expect(s3Node).toBeVisible();
  await browser.locator('.node-card:has-text("S3 Cloud Sink") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('S3 Cloud Sink');
  await app.screenshot('05-s3-sink-inspector');

  const s3InfoBtn = browser.locator('.library-item:has-text("S3 Cloud Sink") .library-info-btn').first();
  await s3InfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('06-s3-sink-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 5. Test Node: Notification Dispatcher
  const notifLib = browser.locator('.library-item:has-text("Notification Dispatcher")').first();
  await expect(notifLib).toBeVisible();
  await notifLib.click();

  const notifNode = browser.locator('.node-card:has-text("Notification Dispatcher")').first();
  await expect(notifNode).toBeVisible();
  await browser.locator('.node-card:has-text("Notification Dispatcher") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Notification Dispatcher');
  await app.screenshot('07-notification-dispatcher-inspector');

  const notifInfoBtn = browser.locator('.library-item:has-text("Notification Dispatcher") .library-info-btn').first();
  await notifInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('08-notification-dispatcher-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 6. Test Node: PTZ Controller (ONVIF)
  const ptzLib = browser.locator('.library-item:has-text("PTZ Controller (ONVIF)")').first();
  await expect(ptzLib).toBeVisible();
  await ptzLib.click();

  const ptzNode = browser.locator('.node-card:has-text("PTZ Controller (ONVIF)")').first();
  await expect(ptzNode).toBeVisible();
  await browser.locator('.node-card:has-text("PTZ Controller (ONVIF)") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('PTZ Controller (ONVIF)');
  await app.screenshot('09-ptz-controller-inspector');

  const ptzInfoBtn = browser.locator('.library-item:has-text("PTZ Controller (ONVIF)") .library-info-btn').first();
  await ptzInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('10-ptz-controller-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 7. Focus on PTZ Controller node on canvas
  await browser.locator('.node-card:has-text("PTZ Controller (ONVIF)") .node-head').first().click();
  await expect(browser.locator('#inspectorTitle')).toContainText('PTZ Controller (ONVIF)');
  await app.screenshot('11-canvas-phase5-complete');

  // 8. Agent verification
  await agent.assert(
    'The workflow canvas contains Phase 5 nodes (Data Aggregator, CSV Formatter, S3 Cloud Sink, Notification Dispatcher, PTZ Controller) and the node inspector displays the PTZ Controller configuration parameters.'
  );
});
