import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Web UI preview compression (720p/480p) and async sink outputs', async ({ app, browser }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // Open workflow from Projects Hub or switch to Studio view
  const openBtn = browser.locator('button:has-text("Buka Proyek →"), button:has-text("Open workflow →"), button:has-text("Gunakan Template →"), .project-card, #tabStudio').first();
  if (await openBtn.isVisible()) {
    await openBtn.click();
  }
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 15000 });

  // 2. Verify Live Preview Resolution & Compression Dropdown
  const previewResSelect = browser.locator('#previewResSelect');
  await expect(previewResSelect).toBeVisible();

  // Verify dropdown contains 720p and 480p options
  const val = await previewResSelect.inputValue();
  expect(val).toBe('720p');
  await app.screenshot('01-preview-res-default-720p');

  // Switch resolution to 480p (low bandwidth / high speed)
  await previewResSelect.selectOption({ value: '480p' });
  expect(await previewResSelect.inputValue()).toBe('480p');
  await app.screenshot('02-preview-res-switch-480p');

  // 3. Inspect Telegram Alert node in sidebar library
  const tgLib = browser.locator('.library-item:has-text("Telegram Alert")').first();
  if (await tgLib.isVisible()) {
    await tgLib.click();
    const tgNode = browser.locator('.node-card:has-text("Telegram Alert")').first();
    await expect(tgNode).toBeVisible();
    await browser.locator('.node-card:has-text("Telegram Alert") .node-head').first().click();
    await expect(browser.locator('#inspectorBody')).toBeVisible();
    await app.screenshot('03-telegram-alert-async-sink-inspector');
  }

  // 4. Switch back to 720p
  await previewResSelect.selectOption({ value: '720p' });
  expect(await previewResSelect.inputValue()).toBe('720p');
  await app.screenshot('04-preview-res-restored-720p');
});
