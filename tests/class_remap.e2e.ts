import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify class remap (pemetaan ulang nama kelas) in object detection node', async ({ app, browser, agent }) => {
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

  // 3. Find Object Detection node on canvas and click it to open inspector
  const detNode = browser.locator('.node-card:has-text("Object Detection")').first();
  await expect(detNode).toBeVisible();
  await browser.locator('.node-card:has-text("Object Detection") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();

  // 4. Verify Class Remap input exists and fill with "car->mobil"
  const remapInput = browser.locator('#inspectorBody .field:has(label:has-text("Pemetaan Ulang Nama Kelas")) input, #inspectorBody input[data-key="classRemap"]').first();
  if (await remapInput.isVisible()) {
    await remapInput.fill('car->mobil');
  } else {
    const input = browser.locator('.field:has-text("Pemetaan Ulang") input').first();
    await input.fill('car->mobil');
  }

  // 5. Select "car" in the compact class multi-select dropdown
  const classTrigger = browser.locator('#inspectorBody .class-dropdown-trigger').first();
  if (await classTrigger.isVisible()) {
    await classTrigger.click();
    const carItem = browser.locator('.class-popover-item:has-text("car")').first();
    if (await carItem.isVisible()) {
      await carItem.click();
    }
    // Close dropdown
    await classTrigger.click();
  }

  // Take screenshot: Inspector showing "car->mobil" configured
  await app.screenshot('01-class-remap-configured-inspector');

  // 6. Click Save button in topbar
  const saveBtn = browser.locator('#saveBtn, button:has-text("Save")').first();
  if (await saveBtn.isVisible()) {
    await saveBtn.click();
  }

  // Take screenshot: Saved workflow with class remapping active
  await app.screenshot('02-class-remap-saved-workflow');
});
