import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Face Analyzer (UniFace) node with age, emotion checkboxes and corner HUD options', async ({ app, browser }) => {
  // 1. Open Studio web app
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

  // 2. Add Face Analyzer (UniFace) from library
  const faceAnalyzerLib = browser.locator('.library-item:has-text("Face Analyzer")').first();
  await expect(faceAnalyzerLib).toBeVisible({ timeout: 5000 });
  await faceAnalyzerLib.click();

  // 3. Verify Face Analyzer node appears on canvas
  const faceAnalyzerNode = browser.locator('.node-card:has-text("Face Analyzer")').first();
  await expect(faceAnalyzerNode).toBeVisible();

  // Screenshot 1: Node on Canvas
  await app.screenshot('01-face-analyzer-node-on-canvas');

  // 4. Click node header to open Inspector
  await browser.locator('.node-card:has-text("Face Analyzer") .node-head').first().click();
  await expect(browser.locator('#inspectorTitle')).toContainText('Face Analyzer');

  // 5. Verify the presence of checkboxes and configuration controls
  const ageGenderCheck = browser.locator('.field:has-text("Estimasi Umur & Jenis Kelamin") input[type="checkbox"]').first();
  await expect(ageGenderCheck).toBeVisible();
  expect(await ageGenderCheck.isChecked()).toBe(true);

  const emotionCheck = browser.locator('.field:has-text("Klasifikasi Ekspresi & Emosi Wajah") input[type="checkbox"]').first();
  await expect(emotionCheck).toBeVisible();
  expect(await emotionCheck.isChecked()).toBe(true);

  const hudCheck = browser.locator('.field:has-text("Tampilkan Ringkasan Statistik di Pojok Layar (HUD)") input[type="checkbox"]').first();
  await expect(hudCheck).toBeVisible();
  expect(await hudCheck.isChecked()).toBe(true);

  const landmarksCheck = browser.locator('.field:has-text("Deteksi 5-Titik Facial Landmark") input[type="checkbox"]').first();
  await expect(landmarksCheck).toBeVisible();

  const faceBadgesCheck = browser.locator('.field:has-text("Tampilkan Badge Label di Atas Wajah") input[type="checkbox"]').first();
  await expect(faceBadgesCheck).toBeVisible();

  const hudPosSelect = browser.locator('.field:has-text("Posisi Panel Ringkasan (HUD)") select').first();
  await expect(hudPosSelect).toBeVisible();

  const ageGroupingSelect = browser.locator('.field:has-text("Model Pengelompokan Usia") select').first();
  await expect(ageGroupingSelect).toBeVisible();

  // Screenshot 2: Inspector Options & Checkboxes
  await app.screenshot('02-face-analyzer-inspector-options');

  // 6. Test interaction: change HUD Position to top-right
  await hudPosSelect.selectOption({ value: 'top-right' });
  expect(await hudPosSelect.inputValue()).toBe('top-right');

  // Screenshot 3: Configured Inspector
  await app.screenshot('03-face-analyzer-configured');
});
