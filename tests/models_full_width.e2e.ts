import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Models manager panel is full width and neat', async ({ app, browser, agent }) => {
  // 1. Open application at Hub
  await app.open('/');
  await expect(browser.locator('.brand, .hub-brand')).toBeVisible();

  // 2. Open project studio by clicking "Open workflow →" on the recent project
  const openWorkflowBtn = browser.locator('.btn-open-project, button:has-text("Open workflow")').first();
  await expect(openWorkflowBtn).toBeVisible({ timeout: 10000 });
  await openWorkflowBtn.click();

  // 3. Click on the Models tab in the left rail
  const railTabModels = browser.locator('#railTabModels');
  await expect(railTabModels).toBeVisible({ timeout: 10000 });
  await railTabModels.click();

  // 3. Verify Models manager panel is visible and app-shell is hidden
  const modelManager = browser.locator('#viewModelManager');
  await expect(modelManager).toBeVisible();

  const appShell = browser.locator('#viewStudio .app-shell');
  await expect(appShell).toBeHidden();

  // 4. Verify table and "+ Add model" button
  const addModelBtn = browser.locator('#modelsAddBtn');
  await expect(addModelBtn).toBeVisible();

  const modelsTable = browser.locator('.models-table');
  await expect(modelsTable).toBeVisible();

  // Verify bounding box width is full-width (greater than 1000px on 1280px viewport)
  const box = await modelManager.boundingBox();
  expect(box?.width).toBeGreaterThan(1000);

  // Take screenshot of the full-width, clean Models view
  await app.screenshot('models-manager-full-width');

  // 5. Assert elements presence
  await agent.assert('The Models title, Add model button, and the models registry table with multiple model entries are visible on the page.');
});
