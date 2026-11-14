import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('topbar groups stay separated at desktop and compact widths', async ({ app, browser }) => {
  await app.open('/');
  const nav = browser.locator('#topbarNavTabs');
  await expect(nav).toBeVisible({ timeout: 15000 });

  for (const width of [1440, 1280]) {
    await browser.setViewport({ width, height: 900 });
    const boxes = await Promise.all([
      browser.locator('.topbar-left').boundingBox(),
      browser.locator('.topbar-center').boundingBox(),
      browser.locator('.topbar-right').boundingBox(),
    ]);
    expect(boxes.every(Boolean), `header groups should have boxes at ${width}px`).toBe(true);
    const [left, center, right] = boxes;
    expect(left!.x + left!.width).toBeLessThanOrEqual(center!.x + 1);
    expect(center!.x + center!.width).toBeLessThanOrEqual(right!.x + 1);
    await app.screenshot(`topbar-no-overlap-${width}px`);
  }
});
