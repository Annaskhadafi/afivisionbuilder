import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify UniFace Face Detector, Face Tracker and Face Registry Gallery', async ({ app, browser, agent }) => {
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

  // 2. Navigate to Face Registry Gallery via Left Rail
  const facesRailBtn = browser.locator('#railTabFaces');
  await expect(facesRailBtn).toBeVisible();
  await facesRailBtn.click();

  const faceRegistryView = browser.locator('#viewFaceRegistry');
  await expect(faceRegistryView).toBeVisible();
  await app.screenshot('01-face-registry-gallery-view');

  // 3. Open Modal Daftarkan Wajah Baru
  const enrollBtn = browser.locator('#faceEnrollBtn');
  await expect(enrollBtn).toBeVisible();
  await enrollBtn.click();

  const enrollModal = browser.locator('#enrollFaceModal');
  await expect(enrollModal).toBeVisible();

  await browser.locator('#enrollNameInput').fill('Anas Supervisor (Workshop)');
  await browser.locator('#enrollRoleInput').fill('Lead Vision Engineer');
  await app.screenshot('02-enroll-face-modal');

  // Close modal
  await browser.locator('#closeEnrollModalBtn').click();
  await expect(enrollModal).toBeHidden();

  // 4. Return to Workflow Studio
  const workflowRailBtn = browser.locator('#railTabWorkflow');
  await workflowRailBtn.click();
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible();

  // 5. Add Face Detector from AI Vision Models
  const faceDetectorLib = browser.locator('.library-item:has-text("Face Detector")').first();
  await expect(faceDetectorLib).toBeVisible({ timeout: 5000 });
  await faceDetectorLib.click();

  // 6. Add Face Tracker from Tracking & Analysis
  const faceTrackerLib = browser.locator('.library-item:has-text("Face Re-ID Tracker")').first();
  await expect(faceTrackerLib).toBeVisible({ timeout: 5000 });
  await faceTrackerLib.click();

  const detectorCard = browser.locator('.node-card:has-text("Face Detector")').first();
  const trackerCard = browser.locator('.node-card:has-text("Face Re-ID Tracker")').first();
  await expect(detectorCard).toBeVisible();
  await expect(trackerCard).toBeVisible();
  await app.screenshot('03-uniface-nodes-canvas');

  // 7. Click Face Tracker node head to open Inspector
  await browser.locator('.node-card:has-text("Face Re-ID Tracker") .node-head').first().click();
  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Face Re-ID Tracker');

  // Verify shortcut button to Face Registry is present
  const shortcutBtn = browser.locator('#openFaceRegistryFromNode');
  await expect(shortcutBtn).toBeVisible();
  await app.screenshot('04-face-tracker-inspector-shortcut');

  // 8. Click shortcut button to navigate to Face Registry directly from Inspector
  await shortcutBtn.click();
  await expect(faceRegistryView).toBeVisible();
  await app.screenshot('05-navigated-to-face-registry-from-node');

  // 9. Agent assertion on the active Face Registry view
  await agent.assert(
    'The current view is the dedicated Face Registry gallery (Database Wajah Terdaftar) management page, featuring the page header with UniFace ArcFace subtitle, search input, stats badge, and Daftarkan Wajah Baru button.'
  );
});
