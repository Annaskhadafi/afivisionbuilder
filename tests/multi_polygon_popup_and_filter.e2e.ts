import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Multi-Zone polygon toolbar popup hide/unhide and class filtering', async ({ app, browser, agent }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // Open workflow from Projects Hub if visible
  const openProjBtn = browser.locator('button:has-text("Buka Workflow →"), button:has-text("Open workflow →")').first();
  if (await openProjBtn.isVisible()) {
    await openProjBtn.click();
  } else {
    const studioBtn = browser.locator('button:has-text("Studio")').first();
    if (await studioBtn.isVisible()) {
      await studioBtn.click();
    }
  }
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 10000 });

  // 2. Add Multi-Zone Occupancy node from library
  const mzoLib = browser.locator('.library-item:has-text("Multi-Zone Occupancy")').first();
  await expect(mzoLib).toBeVisible({ timeout: 5000 });
  await mzoLib.click();

  const mzoNode = browser.locator('.node-card:has-text("Multi-Zone Occupancy")').first();
  await expect(mzoNode).toBeVisible();

  // 3. Open Inspector and click "Gambar Poligon Zona di Preview"
  await browser.locator('.node-card:has-text("Multi-Zone Occupancy") .node-head').first().click();
  await expect(browser.locator('#inspectorBody')).toBeVisible();

  const drawZoneBtn = browser.locator('button:has-text("Gambar Poligon Zona di Preview")').first();
  await expect(drawZoneBtn).toBeVisible();
  await drawZoneBtn.click();

  // 4. Verify Multi-Zone toolbar appears docked OUTSIDE the preview frame
  const multiToolbar = browser.locator('.multi-zone-toolbar');
  await expect(multiToolbar).toBeVisible({ timeout: 5000 });
  await expect(browser.locator('.multi-zone-drag-handle')).toBeVisible();
  await expect(browser.locator('.multi-zone-toggle-btn')).toBeVisible();

  // Verify that toolbar is strictly OUTSIDE #previewContainer (not inside the video frame)
  const isInsidePreview = await browser.evaluate(() => {
    const container = document.getElementById('previewContainer');
    const toolbar = document.querySelector('.multi-zone-toolbar');
    return container && toolbar ? container.contains(toolbar) : false;
  });
  expect(isInsidePreview).toBe(false);

  // Capture screenshot of expanded toolbar
  await app.screenshot('01-multi-zone-toolbar-expanded');

  // 5. Test HIDE / MINIMIZE: Click "👁️ Sembunyikan"
  const toggleBtn = browser.locator('.multi-zone-toggle-btn').first();
  await toggleBtn.click();

  // Verify body is hidden / collapsed
  await expect(browser.locator('.multi-zone-toolbar-body')).toBeHidden();
  await app.screenshot('02-multi-zone-toolbar-collapsed');

  // 6. Test UNHIDE: Click "Buka Setting" to expand back
  await toggleBtn.click();
  await expect(browser.locator('.multi-zone-toolbar-body')).toBeVisible();
  await app.screenshot('03-multi-zone-toolbar-unhidden');

  // 7. Agent assert while the toolbar is active and visible
  await agent.assert(
    'The minimalist Multi-Zone polygon editor dock bar is visible above the preview with area controls, allowing users to configure areas and toggle details.'
  );

  // 8. Close multi-zone editor with Batal
  await browser.locator('.multi-zone-toolbar button:has-text("Batal")').first().click();
  await expect(multiToolbar).toBeHidden();
});
