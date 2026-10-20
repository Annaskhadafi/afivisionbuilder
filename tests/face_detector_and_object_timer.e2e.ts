import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Face Detector, Face Tracker, and Object Timer interoperability on canvas', async ({ app, browser, agent }) => {
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

  // 2. Add Face Detector from library
  const faceDetectorLib = browser.locator('.library-item:has-text("Face Detector")').first();
  await expect(faceDetectorLib).toBeVisible({ timeout: 5000 });
  await faceDetectorLib.click();

  // 3. Add Face Re-ID Tracker from library
  const faceTrackerLib = browser.locator('.library-item:has-text("Face Re-ID Tracker")').first();
  await expect(faceTrackerLib).toBeVisible({ timeout: 5000 });
  await faceTrackerLib.click();

  // 4. Add Object Timer from library
  const objectTimerLib = browser.locator('.library-item:has-text("Object Timer")').first();
  await expect(objectTimerLib).toBeVisible({ timeout: 5000 });
  await objectTimerLib.click();

  // 5. Verify all three cards are visible on the canvas
  const faceDetectorNode = browser.locator('.node-card:has-text("Face Detector")').first();
  const faceTrackerNode = browser.locator('.node-card:has-text("Face Re-ID Tracker")').first();
  const objectTimerNode = browser.locator('.node-card:has-text("Object Timer")').first();

  await expect(faceDetectorNode).toBeVisible();
  await expect(faceTrackerNode).toBeVisible();
  await expect(objectTimerNode).toBeVisible();

  await app.screenshot('01-face-and-timer-nodes-on-canvas');

  // 6. Open Inspector for Object Timer and verify Target Classes includes face
  await browser.locator('.node-card:has-text("Object Timer") .node-head').first().click();
  await expect(browser.locator('#inspectorTitle')).toContainText('Object Timer');

  // Find Target Classes input in inspector
  const targetClassesInput = browser.locator('.field:has-text("Target Classes") input, .field:has-text("Filter Kelas Target") input').first();
  if (await targetClassesInput.isVisible()) {
    const targetVal = await targetClassesInput.inputValue();
    expect(targetVal.toLowerCase()).toContain('face');
  }

  await app.screenshot('02-object-timer-inspector-face-support');

  // 7. Open Inspector for Face Detector
  await browser.locator('.node-card:has-text("Face Detector") .node-head').first().click();
  await expect(browser.locator('#inspectorTitle')).toContainText('Face Detector');
  await app.screenshot('03-face-detector-inspector');

  // 8. Re-select Object Timer to show its inspector with Target Classes
  await browser.locator('.node-card:has-text("Object Timer") .node-head').first().click();
  await expect(browser.locator('#inspectorTitle')).toContainText('Object Timer');
  await app.screenshot('04-object-timer-inspector-configured');

  // 9. Assert workflow setup
  await agent.assert(
    'The Workflow Studio canvas shows Face Detector, Face Re-ID Tracker, and Object Timer cards on the canvas, with the Object Timer node selected in the inspector showing Target Classes configuration.'
  );
});
