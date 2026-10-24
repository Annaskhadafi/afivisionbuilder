import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Human Pose Estimator node library, canvas addition, and skeleton inspector configurations', async ({ app, browser, agent }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // 2. Open workflow studio from Projects Hub
  const openProjBtn = browser.locator('button:has-text("Buka Workflow →"), button:has-text("Open workflow →")').first();
  if (await openProjBtn.isVisible()) {
    await openProjBtn.click();
  } else {
    const studioBtn = browser.locator('button:has-text("Studio")').first();
    if (await studioBtn.isVisible()) {
      await studioBtn.click();
    }
  }
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 15000 });

  // 3. Find and click "Human Pose Estimator" in node library
  const poseLib = browser.locator('.library-item:has-text("Human Pose Estimator")').first();
  await expect(poseLib).toBeVisible({ timeout: 10000 });
  await poseLib.click();

  // 4. Click node on canvas to open inspector
  const poseNode = browser.locator('.node-card:has-text("Human Pose Estimator")').first();
  await expect(poseNode).toBeVisible();
  await browser.locator('.node-card:has-text("Human Pose Estimator") .node-head').first().click();

  // 5. Verify Inspector title & options
  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Human Pose Estimator');
  await app.screenshot('01-pose-node-config');

  // 6. Verify Model combobox contains yolov8n-pose.pt
  const modelCombobox = browser.locator('#inspectorBody select').filter({ hasText: 'yolov8n-pose' }).first();
  if (await modelCombobox.isVisible()) {
    const val = await modelCombobox.inputValue();
    expect(val).toContain('yolov8n-pose');
  } else {
    await expect(browser.locator('#inspectorBody')).toContainText('yolov8n-pose.pt');
  }

  // Verify skeleton and joint toggles exist in inspector
  await expect(browser.locator('#inspectorBody')).toContainText('Skeleton');

  // 7. Take full canvas view screenshot
  await app.screenshot('02-pose-node-canvas-inspector');

  // 8. Assert with AI agent
  await agent.assert('The Human Pose Estimator node is added to the canvas and its inspector panel exposes pose estimation configuration options including model selection with yolov8n-pose, keypoint thresholds, and skeleton visualization toggles.');
  await app.screenshot('03-pose-verified');
});
