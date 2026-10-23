import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Interactive Object Zoom node creation, configuration, and interactive click-to-zoom floating popup', async ({ app, browser, agent }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // 2. Open workflow studio from Projects Hub
  const openProjBtn = browser.locator('button:has-text("Buka Workflow →"), button:has-text("Open workflow →")').first();
  if (await openProjBtn.isVisible()) {
    await openProjBtn.click();
  } else {
    const studioBtn = browser.locator('button:has-text("Studio")').first();
    if (await studioBtn.isVisible()) {
      await studioBtn.click();
    }
  }
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 15000 });

  // 3. Find and click "Interactive Object Zoom" in node library
  const zoomLib = browser.locator('.library-item:has-text("Interactive Object Zoom")').first();
  await expect(zoomLib).toBeVisible({ timeout: 10000 });
  await zoomLib.click();

  // 4. Click node on canvas to open inspector
  const zoomNode = browser.locator('.node-card:has-text("Interactive Object Zoom")').first();
  await expect(zoomNode).toBeVisible();
  await browser.locator('.node-card:has-text("Interactive Object Zoom") .node-head').first().click();

  // 5. Verify Inspector title & options
  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Interactive Object Zoom');
  await app.screenshot('01-interactive-zoom-node-config');

  // 6. Test Interactive Hit-testing & Floating Card UI
  // Simulate active target state on runtime to test the Live Preview Zoom Card
  await browser.evaluate(async () => {
    const node = (window as any).state?.workflow?.nodes?.find((n: any) => n.type === 'interactive_zoom') || { id: 'interactive_zoom', type: 'interactive_zoom' };
    await fetch('/api/interactive-zoom/' + encodeURIComponent(node.id) + '/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trackId: 108 })
    });
    const targetState = {
      nodeId: node.id,
      status: 'locked',
      trackId: 108,
      className: 'car',
      confidence: 0.96,
      bbox: [120, 150, 480, 460],
      hasCrop: true,
    };
    (window as any).renderInteractiveZoomPopup?.(node, targetState);
  });

  // Verify floating card appears over the preview area
  const zoomCard = browser.locator('#interactiveZoomCard');
  await expect(zoomCard).toBeVisible({ timeout: 5000 });
  await expect(zoomCard).toContainText('TARGET #108');
  await expect(zoomCard).toContainText('CAR (96%)');
  await expect(browser.locator('#zoomDownloadBtn')).toBeVisible();
  await expect(browser.locator('#zoomUnlockBtn')).toBeVisible();
  await app.screenshot('02-interactive-zoom-floating-card-active');

  // Test PiP Size switcher buttons (S, M, L, XL capped at max 50%)
  const sizeLBtn = browser.locator('.btn-pip-size[data-size="40"]').first();
  await expect(sizeLBtn).toBeVisible();
  await sizeLBtn.click();
  await app.screenshot('03-interactive-zoom-pip-size-large');

  // Test Portrait Aspect Ratio button (3:4 - Anti Muka Kepotong)
  const portraitBtn = browser.locator('.btn-pip-aspect[data-aspect="3:4"]').first();
  await expect(portraitBtn).toBeVisible();
  await portraitBtn.click();
  await app.screenshot('03b-interactive-zoom-portrait-aspect');

  // Test Dynamic Size Mode button (🎯 Dinamis mengikuti bounding box objek)
  const dynamicBtn = browser.locator('.btn-pip-size[data-size="dynamic"]').first();
  await expect(dynamicBtn).toBeVisible();
  await dynamicBtn.click();
  await app.screenshot('03c-interactive-zoom-dynamic-size-mode');

  // Test Zoom Scale button (🔍 1.0x Full View Anti Muka Kepotong)
  const zoom1xBtn = browser.locator('.btn-pip-zoom[data-zoom="1.0"]').first();
  await expect(zoom1xBtn).toBeVisible();
  await zoom1xBtn.click();
  await app.screenshot('03d-interactive-zoom-full-view-headroom');

  // Test Headroom buttons (+48% Aman & +65% Lega for person / anti muka kepotong)
  const headroom48Btn = browser.locator('.btn-pip-headroom[data-headroom="48"]').first();
  await expect(headroom48Btn).toBeVisible();
  await headroom48Btn.click();
  await app.screenshot('03e-interactive-zoom-headroom-48-safe');

  const headroom65Btn = browser.locator('.btn-pip-headroom[data-headroom="65"]').first();
  await expect(headroom65Btn).toBeVisible();
  await headroom65Btn.click();
  await app.screenshot('03f-interactive-zoom-headroom-65-spacious');

  // Test hiding Download button, Class Name, and Confidence via Inspector checkboxes
  await browser.evaluate(() => {
    const checks = Array.from(document.querySelectorAll('#inspectorBody input[type="checkbox"]')) as HTMLInputElement[];
    checks.forEach(cb => {
      if (cb.checked) {
        cb.click();
      }
    });
  });

  await browser.evaluate(async () => {
    const node = (window as any).state?.workflow?.nodes?.find((n: any) => n.type === 'interactive_zoom') || { id: 'interactive_zoom', type: 'interactive_zoom' };
    const targetState = {
      nodeId: node.id,
      status: 'locked',
      trackId: 108,
      className: 'car',
      confidence: 0.96,
      bbox: [120, 150, 480, 460],
      hasCrop: true,
      showClassName: false,
      showConfidence: false,
      showDownloadButton: false,
    };
    const zoomNode = {
      id: node.id,
      type: 'interactive_zoom',
      config: {
        showClassName: false,
        showConfidence: false,
        showDownloadButton: false,
      },
    };
    (window as any).renderInteractiveZoomPopup?.(zoomNode, targetState);
  });

  // Verify Download button is now hidden and class/confidence are omitted
  await expect(browser.locator('#zoomDownloadBtn')).not.toBeVisible();
  await expect(zoomCard).not.toContainText('CAR (96%)');
  await app.screenshot('04-interactive-zoom-hidden-metadata-no-download');

  // Assert that settings reflect the unchecked state in the inspector
  await agent.assert('The Interactive Object Zoom node is configured with class, confidence, and download options unchecked in the inspector.');

  // 7. Click Unlock button to clear target
  await browser.locator('#zoomUnlockBtn').click();
  await expect(zoomCard).not.toBeVisible();
  await app.screenshot('05-interactive-zoom-unlocked');
});
