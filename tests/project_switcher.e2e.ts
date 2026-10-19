import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify project switcher dropdown in topbar and seamless switching between projects', async ({ app, browser, agent }) => {
  // 1. Open the application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // 2. Open any workflow into Studio view
  const openWorkflowBtn = browser.locator('.hub-open-workflow-btn').first();
  if (await openWorkflowBtn.isVisible()) {
    await openWorkflowBtn.click();
  }
  await expect(browser.locator('#canvas')).toBeVisible();

  // 3. Verify Project Switcher Button exists in Topbar
  const switcherBtn = browser.locator('#projectSwitcherBtn');
  await expect(switcherBtn).toBeVisible();

  // 4. Click Project ▾ button to open project switcher dropdown
  await switcherBtn.click();
  const dropdown = browser.locator('#projectSwitcherDropdown');
  await expect(dropdown).toBeVisible();

  // 5. Verify dropdown contents (heading, search input, list of projects)
  await expect(browser.locator('.project-switcher-heading')).toBeVisible();
  await expect(browser.locator('#projectSwitcherSearch')).toBeVisible();
  const projectItems = browser.locator('.project-switcher-item');
  const count = await projectItems.count();
  expect(count).toBeGreaterThan(0);

  // Take screenshot of open dropdown with list of projects
  await app.screenshot('01-project-switcher-dropdown-open');

  // 6. Test search filter functionality
  const searchInput = browser.locator('#projectSwitcherSearch');
  await searchInput.fill('Integration');
  await expect(browser.locator('.project-switcher-item:has-text("Integration")')).toBeVisible();

  // Clear search filter
  await searchInput.fill('');

  // 7. Click Integration project item in the dropdown
  const targetItem = browser.locator('.project-switcher-item:has-text("Integration")');
  await targetItem.click();

  // 8. Verify dropdown closes and projectName updates to Integration
  await expect(dropdown).toBeHidden();
  await expect(browser.locator('#projectName')).toContainText('Integration');

  // 9. Re-open dropdown to verify active status badge updated
  await switcherBtn.click();
  await expect(dropdown).toBeVisible();
  const activeItem = browser.locator('.project-switcher-item.is-active');
  await expect(activeItem).toBeVisible();
  await expect(activeItem).toContainText('Integration');
  await expect(browser.locator('.project-switcher-item.is-active .project-switcher-item-badge')).toContainText('AKTIF');

  // Take screenshot after switching with updated active badge
  await app.screenshot('02-switcher-active-badge-updated');

  await agent.assert('The project switcher dropdown is open from the topbar Project button, displaying the project list with an AKTIF badge on the selected project, search input, and action buttons.');

  // Close dropdown by pressing Escape
  await browser.keyboard.press('Escape');
  await expect(dropdown).toBeHidden();
});
