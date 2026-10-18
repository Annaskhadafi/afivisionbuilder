import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('load Afi Vision Builder workspace and verify studio interface', async ({ app, screen, browser, agent }) => {
  // 1. Open the studio application
  await app.open('/');

  // 2. Wait for page body to load
  await expect(browser.locator('body')).toBeVisible();

  // 3. Verify brand header is visible
  await expect(browser.locator('.brand')).toBeVisible();

  // 4. Capture screenshot of the workspace
  await app.screenshot('vision-builder-home');

  // 5. Verify interface state using AI Agent assertion
  await agent.assert('the Afi Vision Builder interface is loaded and visible');
});
