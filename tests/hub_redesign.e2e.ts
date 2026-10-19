import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify redesigned projects and templates hub, removal of test words, and clear purpose details', async ({ app, browser, agent }) => {
  // 1. Open the application (starts at Hub)
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // If currently inside studio, navigate to Hub via logo or Hub button
  const brandLogo = browser.locator('#brandLogoHome');
  await brandLogo.click();
  await expect(browser.locator('#viewProjectsHub')).toBeVisible();

  // 2. Verify Modern Hero Banner and Quick Stats Strip
  await expect(browser.locator('.hub-hero-banner')).toBeVisible();
  await expect(browser.locator('.hub-hero-title')).toContainText('Computer Vision Workflows');
  await expect(browser.locator('.hub-stats-strip')).toBeVisible();
  await expect(browser.locator('#hubStatProjectsCount')).toBeVisible();
  await expect(browser.locator('#hubStatTemplatesCount')).toBeVisible();

  // Screenshot 1: Overview of redesigned Hub hero, quick stats, and recent projects
  await app.screenshot('01-hub-hero-and-stats');

  // 3. Verify Industry Solution Templates Section
  const templatesSection = browser.locator('#hubTemplatesSection');
  await expect(templatesSection).toBeVisible();

  // Verify that template names NO LONGER contain "Test" or "YOLOv8 Test"
  const templateTitles = await browser.locator('.hub-template-title').allTextContents();
  console.log('Sample Template Titles:', templateTitles.slice(0, 5));
  for (const title of templateTitles) {
    expect(title).not.toMatch(/YOLOv8 Test/i);
    expect(title).not.toMatch(/\bTest \d+/i);
  }

  // 4. Verify Purpose & Function Box exists on template cards
  const purposeBox = browser.locator('.hub-template-purpose-box').first();
  await expect(purposeBox).toBeVisible();
  await expect(browser.locator('.hub-template-purpose-box .purpose-header').first()).toContainText(/fungsi & kegunaan/i);

  // Screenshot 2: Template cards with clear purpose, tags, and category badges
  await browser.evaluate(() => document.getElementById('hubTemplatesSection')?.scrollIntoView());
  await app.screenshot('02-templates-with-purpose-box');

  // 5. Test Category Filter Pills
  const qcCatPill = browser.locator('#hubCatPillManufaktur');
  if (await qcCatPill.isVisible()) {
    await qcCatPill.click();
    await expect(browser.locator('.hub-template-category-badge').first()).toContainText(/manufaktur/i);
    await app.screenshot('03-templates-filter-manufaktur-qc');
  }

  // Return to all category
  const allCatPill = browser.locator('#hubCatPillAll');
  await allCatPill.click();

  // 6. Test Live Search Filtering
  const searchInput = browser.locator('#hubTemplateSearchInput');
  await searchInput.fill('barcode');
  await expect(browser.locator('.hub-template-title').first()).toContainText(/barcode/i);
  await app.screenshot('04-templates-search-barcode');

  // Clear search
  await searchInput.fill('');

  // 7. Verify AI assertion for visual elegance and organization
  await agent.assert('The initial Hub page is cleanly organized with a modern hero banner, quick stats strip, project search, industry solution template cards clearly explaining practical functions without the word Test, and category filtering pills.');
});
