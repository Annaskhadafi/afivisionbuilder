import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify redesigned header, functional settings modal, and project 3-dots menu', async ({ app, browser }) => {
  // 1. Open the application (Projects Hub)
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // 2. Verify topbar header structure and take screenshot of Hub header
  await expect(browser.locator('.topbar')).toBeVisible();
  await expect(browser.locator('.hub-header-actions')).toBeVisible();
  await app.screenshot('01-redesigned-header-hub');

  // 3. Test Settings button functionality
  const settingsBtn = browser.locator('#hubSettingsBtn');
  await expect(settingsBtn).toBeVisible();
  await settingsBtn.click();

  // 4. Verify System Settings Modal is opened
  const settingsModal = browser.locator('#systemSettingsModal');
  await expect(settingsModal).toBeVisible();
  await app.screenshot('02-system-settings-modal');

  // Switch tab in settings modal
  const vlmTabBtn = browser.locator('.settings-nav-tab[data-tab="vlm"]');
  if (await vlmTabBtn.isVisible()) {
    await vlmTabBtn.click();
    await app.screenshot('02b-system-settings-api-keys');
  }

  // Close Settings Modal
  const closeSettingsBtn = browser.locator('#closeSystemSettingsModal');
  await closeSettingsBtn.click();
  await expect(settingsModal).toBeHidden();

  // 5. Test 3-Dots Project Card Action Menu
  const cardMenuBtn = browser.locator('.hub-card-menu-btn').first();
  await expect(cardMenuBtn).toBeVisible();
  await cardMenuBtn.click();
  const contextMenu = browser.locator('.hub-project-dropdown-menu');
  await expect(contextMenu).toBeVisible();
  await app.screenshot('03-project-card-3dots-menu');

  // 6. Enter Studio via the "Open" menu action and verify topbar header in Studio
  const openOpt = browser.locator('.hub-project-dropdown-menu .open-opt');
  await expect(openOpt).toBeVisible();
  await openOpt.click();
  await expect(browser.locator('#canvas')).toBeVisible();
  await expect(browser.locator('.topbar')).toBeVisible();
  await expect(browser.locator('.top-actions')).toBeVisible();
  await app.screenshot('04-studio-header-clean');
});
