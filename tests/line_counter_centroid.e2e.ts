import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('line counter allows custom centroid controls', async ({ app, browser }) => {
  await app.open('/');
  if (!(await browser.locator('#viewStudio').isVisible())) await browser.locator('#tabStudio, #hubBottomCreateBtn, .hub-open-workflow-btn, .hub-template-btn').first().click();
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 15000 });
  await browser.locator('.library-item:has-text("Line Counter")').first().click();
  await browser.locator('.node-card:has-text("Line Counter") .node-head').first().click();
  const inspector = browser.locator('#inspectorBody');
  const anchor = browser.locator('#inspectorBody select:has(option[value="custom"])').first();
  await anchor.selectOption({ value: 'custom' });
  await expect(inspector).toContainText('Posisi Centroid Horizontal');
  await expect(inspector).toContainText('Posisi Centroid Vertikal');
  await expect(inspector).toContainText('Tampilkan Titik Centroid');
  await app.screenshot('line-counter-custom-centroid');
});
