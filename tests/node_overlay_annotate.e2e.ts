import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Overlay / Annotate Node settings and Drawing Layers inspector', async ({ app, browser, agent }) => {
  // 1. Open Studio application and wait for catalog to load
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();
  
  // Wait for catalog nodes to load
  const overlayLib = browser.locator('.library-item:has-text("Overlay / Annotate")').first();
  await expect(overlayLib).toBeVisible({ timeout: 15000 });
  await overlayLib.click();

  // 3. Select node on canvas to open inspector
  const overlayNode = browser.locator('.node-card:has-text("Overlay / Annotate")').first();
  await expect(overlayNode).toBeVisible();
  await overlayNode.click();

  // 4. Verify Node settings header and initial state
  const inspectorTitle = browser.locator('#inspectorTitle .inspector-title-text');
  await expect(inspectorTitle).toHaveText('Node settings');
  const badge = browser.locator('#inspectorTitle .inspector-node-badge');
  await expect(badge).toHaveText('Overlay / Annotate');

  const addLayerBtn = browser.locator('#btnAddOverlayLayer');
  await expect(addLayerBtn).toBeVisible();
  await app.screenshot('overlay-01-node-settings-initial');

  // 5. Click "+ Add layer" to open dropdown matching user reference
  await addLayerBtn.click();
  const dropdown = browser.locator('#addLayerDropdown');
  await expect(dropdown).toBeVisible();
  await app.screenshot('overlay-02-add-layer-dropdown-open');

  // 6. Select "Bounding box" from dropdown
  const bboxItem = browser.locator('.add-layer-item[data-layer-type="bounding_boxes"]').first();
  await expect(bboxItem).toBeVisible();
  await bboxItem.click();

  // Verify Bounding box layer card appears with thickness and color settings
  const bboxCard = browser.locator('.overlay-layer-card:has-text("Bounding box")').first();
  await expect(bboxCard).toBeVisible();
  await app.screenshot('overlay-03-bounding-box-added');

  // 7. Click "+ Add layer" again and add "Label"
  await addLayerBtn.click();
  const labelItem = browser.locator('.add-layer-item[data-layer-type="labels"]').first();
  await expect(labelItem).toBeVisible();
  await labelItem.click();

  const labelCard = browser.locator('.overlay-layer-card:has-text("Label")').first();
  await expect(labelCard).toBeVisible();
  await app.screenshot('overlay-04-multiple-layers-configured');

  // 8. Assert visual state matches expectations
  await agent.assert('The inspector shows Node settings for Overlay / Annotate with SETTINGS (Enabled switch) and DRAWING LAYERS list with Bounding box and Label layers.');
});
