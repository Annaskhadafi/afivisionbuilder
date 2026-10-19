import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify all 5 header buttons: More options (...), Notifications (Bell), Settings, Help, and User Avatar (AN)', async ({ app, browser }) => {
  // 1. Open application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // If on Projects Hub, enter studio via first template or open workflow button
  const hubView = browser.locator('#viewProjectsHub');
  if (await hubView.isVisible()) {
    const openBtn = browser.locator('.hub-open-workflow-btn, .hub-template-btn').first();
    if (await openBtn.isVisible()) {
      await openBtn.click();
    }
  }

  await expect(browser.locator('#viewStudio')).toBeVisible();

  // ==========================================
  // BUTTON 1: More options (...) #topbarMoreBtn
  // ==========================================
  const moreBtn = browser.locator('#topbarMoreBtn');
  await expect(moreBtn).toBeVisible();
  await moreBtn.click();

  const moreDropdown = browser.locator('#topbarMoreDropdown');
  await expect(moreDropdown).toBeVisible();
  await expect(browser.locator('#importBtn')).toBeVisible();
  await expect(browser.locator('#exportBtn')).toBeVisible();
  await expect(browser.locator('#copyWorkflowJsonBtn')).toBeVisible();
  await expect(browser.locator('#fitCanvasMoreBtn')).toBeVisible();
  await expect(browser.locator('#clearCanvasMoreBtn')).toBeVisible();
  await expect(browser.locator('#docsSwaggerMoreBtn')).toBeVisible();

  await app.screenshot('01-topbar-more-dropdown-open');

  // Test copy workflow JSON
  await browser.locator('#copyWorkflowJsonBtn').click();
  await expect(moreDropdown).toBeHidden();

  // Test fit canvas button inside more options
  await moreBtn.click();
  await expect(moreDropdown).toBeVisible();
  await browser.locator('#fitCanvasMoreBtn').click();
  await expect(moreDropdown).toBeHidden();

  // Test clear canvas button and modal
  await moreBtn.click();
  await expect(moreDropdown).toBeVisible();
  const clearBtn = browser.locator('#clearCanvasMoreBtn');
  await expect(clearBtn).toBeVisible();
  await clearBtn.click();

  const clearModal = browser.locator('#clearCanvasModal');
  await expect(clearModal).toBeVisible();
  await expect(browser.locator('#clearCanvasModal h2')).toContainText('Kosongkan Kanvas Alur Kerja?');
  await app.screenshot('01b-clear-canvas-modal-open');

  // Confirm clear canvas
  await browser.locator('#confirmClearCanvasBtn').click();
  await expect(clearModal).toBeHidden();

  // Verify canvas is now completely empty
  const emptyCanvas = browser.locator('#emptyCanvas');
  await expect(emptyCanvas).toBeVisible();
  await app.screenshot('01c-empty-canvas-verified');

  // ==========================================
  // BUTTON 2: Notification Bell (🔔) #hubBellBtn
  // ==========================================
  const bellBtn = browser.locator('#hubBellBtn');
  await expect(bellBtn).toBeVisible();
  await bellBtn.click();

  const bellDropdown = browser.locator('#hubBellDropdown');
  await expect(bellDropdown).toBeVisible();
  await expect(browser.locator('.bell-head-title')).toContainText('Notifikasi Sistem');
  await expect(browser.locator('#hubBellCountBadge')).toBeVisible();
  await expect(browser.locator('#hubBellList')).toBeVisible();

  // Verify filter pills
  const alertFilterPill = browser.locator('.bell-filter-pill[data-filter="alert"]');
  await expect(alertFilterPill).toBeVisible();
  await alertFilterPill.click();

  const allFilterPill = browser.locator('.bell-filter-pill[data-filter="all"]');
  await allFilterPill.click();

  await app.screenshot('02-notification-bell-dropdown-open');

  // Test mark as read
  const markReadBtn = browser.locator('#hubBellMarkReadBtn');
  await expect(markReadBtn).toBeVisible();
  await markReadBtn.click();
  await expect(browser.locator('#hubBellCountBadge')).toContainText('Semua Dibaca');

  // Close dropdown by clicking bell again
  await bellBtn.click();
  await expect(bellDropdown).toBeHidden();

  // ==========================================
  // BUTTON 3: Settings (⚙️) #hubSettingsBtn
  // ==========================================
  const settingsBtn = browser.locator('#hubSettingsBtn');
  await expect(settingsBtn).toBeVisible();
  await settingsBtn.click();

  const settingsModal = browser.locator('#systemSettingsModal');
  await expect(settingsModal).toBeVisible();
  await expect(browser.locator('#systemSettingsModal h3')).toContainText('Studio & Pipeline Settings');

  // Switch tabs in Settings Modal
  const vlmTab = browser.locator('#systemSettingsModal .settings-nav-tab[data-tab="vlm"]');
  await vlmTab.click();
  await expect(browser.locator('#settingsPanelVlm')).toBeVisible();

  await app.screenshot('03-system-settings-modal-open');

  // Close settings modal
  await browser.locator('#closeSystemSettingsModal').click();
  await expect(settingsModal).toBeHidden();

  // ==========================================
  // BUTTON 4: Help (Help) #hubHelpBtn
  // ==========================================
  const helpBtn = browser.locator('#hubHelpBtn');
  await expect(helpBtn).toBeVisible();
  await helpBtn.click();

  const helpModal = browser.locator('#systemHelpModal');
  await expect(helpModal).toBeVisible();
  await expect(browser.locator('#systemHelpModal h2')).toContainText('Pusat Bantuan AFI Vision Builder');
  await expect(browser.locator('#helpPanelShortcuts')).toBeVisible();

  // Switch tabs in Help Modal
  const quickstartTab = browser.locator('#helpNavTabs .help-nav-tab[data-tab="quickstart"]');
  await quickstartTab.click();
  await expect(browser.locator('#helpPanelQuickstart')).toBeVisible();

  const catalogTab = browser.locator('#helpNavTabs .help-nav-tab[data-tab="catalog"]');
  await catalogTab.click();
  await expect(browser.locator('#helpPanelCatalog')).toBeVisible();

  const aboutTab = browser.locator('#helpNavTabs .help-nav-tab[data-tab="about"]');
  await aboutTab.click();
  await expect(browser.locator('#helpPanelAbout')).toBeVisible();

  await app.screenshot('04-system-help-modal-open');

  // Close help modal
  await browser.locator('#closeHelpFooterBtn').click();
  await expect(helpModal).toBeHidden();

  // ==========================================
  // BUTTON 5: User Avatar (AN) #hubUserAvatarBtn
  // ==========================================
  const userAvatarBtn = browser.locator('#hubUserAvatarBtn');
  await expect(userAvatarBtn).toBeVisible();
  await userAvatarBtn.click();

  const userDropdown = browser.locator('#hubUserDropdown');
  await expect(userDropdown).toBeVisible();
  await expect(browser.locator('.user-dropdown-name')).toContainText('Anas Khadafi');
  await expect(browser.locator('.user-dropdown-role')).toContainText(/lead vision engineer/i);
  await expect(browser.locator('#userMenuSettingsBtn')).toBeVisible();
  await expect(browser.locator('#userMenuQuantizeBtn')).toBeVisible();
  await expect(browser.locator('#userMenuHelpBtn')).toBeVisible();
  await expect(browser.locator('#userMenuDocsBtn')).toBeVisible();
  await expect(browser.locator('#userMenuSyncBtn')).toBeVisible();
  await expect(browser.locator('#userMenuLockBtn')).toBeVisible();

  await app.screenshot('05-user-avatar-dropdown-open');

  // Test 1: clicking Help from user menu opens help modal
  await browser.locator('#userMenuHelpBtn').click();
  await expect(userDropdown).toBeHidden();
  await expect(helpModal).toBeVisible();
  await browser.locator('#closeSystemHelpModal').click();
  await expect(helpModal).toBeHidden();

  // Test 2: clicking Quantizer from user menu opens quantize modal
  await userAvatarBtn.click();
  await expect(userDropdown).toBeVisible();
  await browser.locator('#userMenuQuantizeBtn').click();
  await expect(userDropdown).toBeHidden();
  const quantizeModal = browser.locator('#quantizeModelModal');
  await expect(quantizeModal).toBeVisible();
  await browser.locator('#closeQuantizeModelModal').click();
  await expect(quantizeModal).toBeHidden();

  // Test 3: clicking Sync Status from user menu triggers sync
  await userAvatarBtn.click();
  await expect(userDropdown).toBeVisible();
  await browser.locator('#userMenuSyncBtn').click();
  await expect(userDropdown).toBeHidden();

  // Test 4: clicking Lock / Logout from user menu
  await userAvatarBtn.click();
  await expect(userDropdown).toBeVisible();
  await browser.locator('#userMenuLockBtn').click();
  await expect(userDropdown).toBeHidden();
});
