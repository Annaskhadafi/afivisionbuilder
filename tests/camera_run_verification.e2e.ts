import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify workflow run with camera input and model inference without capture thread error', async ({ app, browser, agent }) => {
  // 1. Open the studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // 2. Open project from Hub
  const openBtn = browser.locator('.hub-open-workflow-btn').first();
  await openBtn.click();

  // 3. Verify in Studio Canvas
  await expect(browser.locator('#viewStudio')).toBeVisible();
  await expect(browser.locator('#canvas')).toBeVisible();

  // 4. Capture screenshot of canvas before run
  await app.screenshot('01-workflow-canvas-ready');

  // 5. Trigger workflow run
  await new Promise(r => setTimeout(r, 1200));
  const isRunning = await browser.locator('#stopBtn').isEnabled();
  if (!isRunning) {
    await browser.evaluate(() => (document.getElementById('runBtn') as HTMLButtonElement)?.click());
  }

  // 6. Verify pipeline reaches RUNNING state
  await expect(browser.locator('#stopBtn')).toBeEnabled({ timeout: 20000 });
  await expect(browser.locator('#runState')).toHaveText('RUNNING', { timeout: 20000 });

  // 7. Allow streaming frames to process and verify no error banner
  await new Promise(r => setTimeout(r, 4000));
  await app.screenshot('02-workflow-running-live');

  // 8. Assert workflow is running healthy with AI agent
  await agent.assert('The workflow studio is active, the pipeline status is RUNNING, and no capture thread error is displayed');

  // 9. Stop workflow cleanly
  await browser.evaluate(() => (document.getElementById('stopBtn') as HTMLButtonElement)?.click());
  await new Promise(r => setTimeout(r, 1500));
  await app.screenshot('03-workflow-stopped-cleanly');
});
