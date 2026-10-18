import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Multi-Zone Occupancy & Activity Tracker node inspector and visual polygon editor', async ({ app, browser, agent }) => {
  // 1. Open studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // Open the first project from Projects Hub
  const openProjBtn = browser.locator('button:has-text("Open workflow →")').first();
  await expect(openProjBtn).toBeVisible({ timeout: 10000 });
  await openProjBtn.click();

  // Ensure Workflow Studio canvas and sidebar are ready
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 10000 });
  await expect(browser.locator('#canvas')).toBeVisible({ timeout: 10000 });

  // 2. Locate Multi-Zone Occupancy in the node library
  const nodeItem = browser.locator('.library-item:has-text("Multi-Zone Occupancy")').first();
  await expect(nodeItem).toBeVisible({ timeout: 10000 });
  await nodeItem.click();

  // 3. Select node on canvas to display Inspector
  const canvasCard = browser.locator('.node-card:has-text("Multi-Zone Occupancy")').first();
  await expect(canvasCard).toBeVisible({ timeout: 10000 });
  await canvasCard.click();

  // 4. Verify Inspector contents
  const badge = browser.locator('#inspectorTitle .inspector-node-badge');
  await expect(badge).toHaveText('Multi-Zone Occupancy');

  const openEditorBtn = browser.locator('#openMultiZoneEditorBtn');
  await expect(openEditorBtn).toBeVisible();

  const targetClassesInput = browser.locator('#mzTargetClasses');
  await expect(targetClassesInput).toBeVisible();
  await expect(targetClassesInput).toHaveValue('person');

  await app.screenshot('multi-zone-01-inspector');

  // 5. Open Multi-Zone Visual Polygon Editor on preview
  await openEditorBtn.click();

  // Verify toolbar elements appear
  const toolbar = browser.locator('.multi-zone-toolbar');
  await expect(toolbar).toBeVisible();

  const zoneSelect = browser.locator('.multi-zone-select');
  await expect(zoneSelect).toBeVisible();

  const addZoneBtn = browser.locator('.multi-zone-toolbar button:has-text("+ Area")');
  await expect(addZoneBtn).toBeVisible();

  await app.screenshot('multi-zone-02-editor-open');

  // 6. Add a new zone via the editor toolbar
  await addZoneBtn.click();
  await app.screenshot('multi-zone-03-zone-added');

  // 7. Save zones
  const saveBtn = browser.locator('.multi-zone-toolbar button:has-text("Simpan Semua Area")');
  await expect(saveBtn).toBeVisible();
  await saveBtn.click();

  // 8. Verify toolbar closes and inspector reflects saved areas
  await expect(toolbar).not.toBeVisible();
  await app.screenshot('multi-zone-04-zones-saved');

  // 9. Agent assert
  await agent.assert('The application has opened the Multi-Zone visual editor, added an area, saved all areas, and returned to the canvas with the node configured.');
});
