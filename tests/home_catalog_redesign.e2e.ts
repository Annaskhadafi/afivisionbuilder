import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('home catalogue shows artwork and keeps template discovery usable', async ({ app, browser }) => {
  await app.open('/');
  await expect(browser.locator('#viewProjectsHub')).toBeVisible();
  await expect(browser.locator('.hub-hero-title')).toContainText('Computer Vision');
  await expect(browser.locator('.hub-sidebar')).toHaveCount(0);
  await expect(browser.locator('.hub-template-card').first()).toBeVisible();
  await expect(browser.locator('.hub-template-image')).toHaveCount(37);
  const artwork = await browser.evaluate(async () => {
    const images = Array.from(document.querySelectorAll<HTMLImageElement>('.hub-template-image'));
    await Promise.all(images.map(image => { image.loading = 'eager'; return image.decode(); }));
    return { unique: new Set(images.map(image => image.currentSrc)).size, loaded: images.every(image => image.naturalWidth > 0) };
  });
  expect(artwork.unique).toBe(37);
  expect(artwork.loaded).toBe(true);
  const bannerRatio = await browser.evaluate(() => {
    const banner = document.querySelector('.hub-template-banner')!.getBoundingClientRect();
    return banner.width / banner.height;
  });
  expect(bannerRatio).toBeLessThan(1.85);
  await app.screenshot('home-catalogue-desktop');

  await browser.evaluate(() => document.querySelector('.hub-template-card:has(.hub-template-title[title="Custom Python Script Pipeline"])')?.scrollIntoView());
  await app.screenshot('home-template-crop');

  await browser.locator('.hub-hero-search').click();
  await expect(browser.locator('#hubTemplateSearchInput')).toBeVisible();
  await browser.locator('#hubTemplateSearchInput').fill('Bottle');
  await expect(browser.locator('.hub-template-card:has-text("Bottle Visual Inspection")')).toBeVisible();
  await app.screenshot('home-catalogue-filtered');

  await browser.locator('#hubTemplateSearchInput').fill('');
  await browser.locator('#hubProjectsTab').click();
  await browser.evaluate(() => document.getElementById('hubRecentProjectsSection')?.scrollIntoView());
  await expect(browser.locator('#hubRecentProjectsSection')).toBeVisible();
  await expect(browser.locator('.hub-projects-table')).toBeVisible();
  await expect(browser.locator('.hub-projects-table .hub-project-card').first()).toBeVisible();
  await expect(browser.locator('#hubBottomCreateBtn')).toBeVisible();
  await app.screenshot('home-catalogue-projects');
  await browser.locator('.hub-projects-table .hub-open-workflow-btn').first().click();
  await expect(browser.locator('#viewStudio')).toBeVisible();
  await browser.locator('#brandLogoHome').click();
  await expect(browser.locator('#viewProjectsHub')).toBeVisible();
});
