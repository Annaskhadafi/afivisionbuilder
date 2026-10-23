import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify minimalist class multiselect dropdown list without large boxes', async ({ app, browser, agent }) => {
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

  // 3. Add "Detection & Geometry Filter" node from library
  const filterLib = browser.locator('.library-item:has-text("Detection & Geometry Filter")').first();
  await filterLib.click();
  
  // 4. Click the Filter node on canvas to open inspector
  const filterNode = browser.locator('.node-card:has-text("Detection & Geometry Filter")').last();
  await expect(filterNode).toBeVisible();
  await browser.locator('.node-card:has-text("Detection & Geometry Filter") .node-head').last().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();

  // 5. Verify the sleek compact dropdown trigger (no large boxes)
  const trigger = browser.locator('.class-dropdown-trigger').first();
  await expect(trigger).toBeVisible({ timeout: 5000 });
  await expect(browser.locator('.class-trigger-text').first()).toBeVisible();

  // Capture screenshot: Clean compact closed dropdown field
  await app.screenshot('01-class-dropdown-closed-compact');

  // 6. Click the dropdown trigger to open the floating checklist
  await trigger.click();

  const popover = browser.locator('.class-dropdown-popover').first();
  await expect(popover).toBeVisible();

  // Capture screenshot: Floating minimalist checklist list
  await app.screenshot('02-class-dropdown-open-list');

  // 7. Click "Bersihkan" to clear all selected classes
  const clearAllBtn = browser.locator('.class-mini-btn:has-text("Bersihkan")').first();
  await clearAllBtn.click();
  await expect(browser.locator('.class-trigger-text.placeholder').first()).toBeVisible();

  // 8. Select classes from checklist (e.g. car and truck)
  const carItem = browser.locator('.class-popover-item:has-text("car")').first();
  await carItem.click();
  const truckItem = browser.locator('.class-popover-item:has-text("truck")').first();
  await truckItem.click();

  // 9. Verify selection is reflected on trigger label
  await expect(browser.locator('.class-dropdown-trigger:has-text("car")').first()).toBeVisible();
  await expect(browser.locator('.class-dropdown-trigger:has-text("truck")').first()).toBeVisible();

  // Capture screenshot: Selected items reflected in compact trigger and checklist
  await app.screenshot('03-class-dropdown-selected');

  // 10. Close dropdown by clicking trigger again
  await trigger.click();
  await expect(popover).not.toBeVisible();

  // Capture screenshot: Closed sleek dropdown field with selected items
  await app.screenshot('04-class-dropdown-final-compact');
});
