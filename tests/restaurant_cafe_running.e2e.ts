import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Restaurant Cafe CCTV video workflow execution and live table tracking', async ({ app, browser, agent }) => {
  // 1. Open Web Application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // 2. Open Restaurant Project
  const openBtn = browser.locator('.hub-open-workflow-btn').first();
  await openBtn.click();

  // 3. Verify in Studio Canvas
  await expect(browser.locator('#viewStudio')).toBeVisible();
  await expect(browser.locator('.node-card:has-text("Input")')).toBeVisible();
  await expect(browser.locator('.node-card:has-text("Multi-Zone Occupancy")')).toBeVisible();

  // 4. Wait for status poll to settle
  await new Promise(r => setTimeout(r, 1200));
  const isRunning = await browser.locator('#stopBtn').isEnabled();

  if (!isRunning) {
    await browser.evaluate(() => document.getElementById('runBtn')?.click());
  }

  // 5. Verify the pipeline is in RUNNING state
  await expect(browser.locator('#stopBtn')).toBeEnabled({ timeout: 15000 });
  await expect(browser.locator('#runState')).toHaveText('RUNNING', { timeout: 15000 });

  // 6. Wait for inference and live frame stream to establish timer
  await expect(browser.locator('#previewImage')).toBeVisible({ timeout: 15000 });
  await new Promise(r => setTimeout(r, 4000));

  // Take Screenshot 1: Running Cafe Pipeline with live frames & status
  await app.screenshot('01-cafe-video-running-pipeline');

  // 7. Click Multi-Zone Occupancy node to view table settings
  await browser.locator('.node-card:has-text("Multi-Zone Occupancy")').click();
  await expect(browser.locator('.inspector h2')).toContainText('Multi-Zone Occupancy');
  await expect(browser.locator('.inspector:has-text("1. Meja 01 (Tengah)")')).toBeVisible();
  await expect(browser.locator('.inspector:has-text("2. Meja 02 (Kiri Depan)")')).toBeVisible();
  await expect(browser.locator('.inspector:has-text("3. Meja 03 (Kiri Belakang)")')).toBeVisible();
  await expect(browser.locator('.inspector:has-text("4. Meja 04 (Kanan Depan)")')).toBeVisible();
  await expect(browser.locator('#mzLabelPosition')).toHaveValue('center');
  await expect(browser.locator('#mzCompactLabel')).toHaveValue('true');

  // Take Screenshot 2: Inspector showing centered timer, compact label & 4 mapped Cafe tables
  await app.screenshot('02-cafe-tables-inspector');

  // 8. Pipeline remains running for the user
  await expect(browser.locator('#stopBtn')).toBeEnabled();

  // 9. AI Agent verification
  await agent.assert('the video workflow is in running state with 4 table zones configured in the multi-zone occupancy node');
});
