import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Face Registry Modal Camera Capture Support', async ({ app, browser, agent }) => {
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

  // 3. Open Modal Daftarkan Wajah Baru
  const enrollBtn = browser.locator('#faceEnrollBtn');
  await expect(enrollBtn).toBeVisible();
  await enrollBtn.click();

  const enrollModal = browser.locator('#enrollFaceModal');
  await expect(enrollModal).toBeVisible();

  // 4. Verify mode switcher tabs (Upload vs Camera)
  const tabUpload = browser.locator('#faceTabUpload');
  const tabCamera = browser.locator('#faceTabCamera');
  await expect(tabUpload).toBeVisible();
  await expect(tabCamera).toBeVisible();

  // Default is Upload
  await expect(browser.locator('#facePhotoDropArea')).toBeVisible();

  // 5. Switch to Camera Capture Mode
  await tabCamera.click();
  const cameraArea = browser.locator('#faceCameraArea');
  await expect(cameraArea).toBeVisible();
  await expect(browser.locator('#captureWebcamBtn')).toBeVisible();
  await expect(browser.locator('#faceWebcamVideo')).toBeVisible();
  await app.screenshot('01-camera-tab-active-in-modal');

  // 6. Fill identification details
  await browser.locator('#enrollNameInput').fill('Annas Khadafi');
  await browser.locator('#enrollRoleInput').fill('Lead Vision Engineer');

  // 7. Switch back to Camera Capture Mode to test camera view
  await tabCamera.click();
  await expect(cameraArea).toBeVisible();
  await expect(browser.locator('#captureWebcamBtn')).toBeVisible();
  await app.screenshot('03-camera-mode-ready');

  // 8. Agent assertion
  await agent.assert(
    'The enroll face modal provides both Unggah and Kamera source options with an intuitive tab switcher, displaying camera controls for capturing a photo when the Kamera tab is selected.'
  );
});
