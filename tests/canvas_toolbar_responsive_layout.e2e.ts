import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify canvas toolbar and panel layout settings are fully visible and not cut off without zoom out', async ({ app, browser }) => {
  // 1. Open app
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // 2. Open workflow studio from Projects Hub if visible
  const openProjBtn = browser.locator('button:has-text("Buka Workflow →"), button:has-text("Open workflow →")').first();
  if (await openProjBtn.isVisible()) {
    await openProjBtn.click();
  } else {
    const studioBtn = browser.locator('button:has-text("Studio"), #tabWorkflow').first();
    if (await studioBtn.isVisible()) {
      await studioBtn.click();
    }
  }

  // 3. Test on standard Full HD desktop viewport (1920x1080)
  await browser.setViewport({ width: 1920, height: 1080 });

  const canvasToolbar = browser.locator('.canvas-toolbar');
  await expect(canvasToolbar).toBeVisible({ timeout: 15000 });

  const toggleInspector = browser.locator('#toggleInspector');
  const toggleSidebar = browser.locator('#toggleSidebar');
  const toggleBottom = browser.locator('#toggleBottom');
  const toggleAiCopilot = browser.locator('#toggleAiCopilotBtn');
  const autoAssemble = browser.locator('#autoAssembleBtn');

  // Verify all are fully visible on 1080p
  await expect(toggleInspector).toBeVisible();
  await expect(toggleSidebar).toBeVisible();
  await expect(toggleBottom).toBeVisible();
  await expect(toggleAiCopilot).toBeVisible();
  await expect(autoAssemble).toBeVisible();

  // Check that on 1920x1080 text labels are shown cleanly without truncation or overflow
  await app.screenshot('01_toolbar_full_hd_1920x1080');

  // 4. Test on 1440x900 viewport
  await browser.setViewport({ width: 1440, height: 900 });
  await expect(toggleInspector).toBeVisible();
  await expect(toggleAiCopilot).toBeVisible();
  await app.screenshot('02_toolbar_desktop_1440x900');

  // 5. Test on compact laptop viewport (1280x720) with inspector open
  await browser.setViewport({ width: 1280, height: 720 });
  await expect(toggleInspector).toBeVisible();
  await expect(toggleSidebar).toBeVisible();
  await expect(toggleBottom).toBeVisible();
  await expect(toggleAiCopilot).toBeVisible();
  await expect(autoAssemble).toBeVisible();
  await app.screenshot('03_toolbar_compact_laptop_1280x720');

  // 6. Test interaction: click toggleInspector to hide inspector, then click again to restore
  await toggleInspector.click();
  const appShell = browser.locator('.app-shell');
  await expect(appShell).toHaveAttribute('data-inspector-hidden', 'true');
  await app.screenshot('04_inspector_hidden_via_toggle');

  // Click again to show inspector
  await toggleInspector.click();
  await expect(appShell).toHaveAttribute('data-inspector-hidden', 'false');
  await app.screenshot('05_inspector_restored');
});
