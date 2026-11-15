import { test } from '@e2e-dev/web';
import { expect } from 'e2e';
test('passerby node provides two drawable lines', async ({ app, browser }) => {
  await app.open('/');
  if (!(await browser.locator('#viewStudio').isVisible())) await browser.locator('#tabStudio, #hubBottomCreateBtn, .hub-open-workflow-btn, .hub-template-btn').first().click();
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 15000 });
  await browser.locator('.library-item:has-text("Passerby & Store Visitors")').first().click();
  await browser.locator('.node-card:has-text("Passerby & Store Visitors") .node-head').first().click();
  await expect(browser.locator('#inspectorBody')).toContainText("Daftar Garis (2)");
  await expect(browser.locator('#inspectorBody button:has-text("Gambar Garis di Preview")')).toHaveCount(2);
  await app.screenshot('passerby-two-lines');
});
