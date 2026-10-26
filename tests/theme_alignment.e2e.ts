import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('home and light dashboard share Workflow Studio typography and colors', async ({ app, browser }) => {
  await app.open('/');
  await expect(browser.locator('#hubTemplatesSection')).toBeVisible();
  const home = await browser.evaluate(() => ({
    background: getComputedStyle(document.getElementById('viewProjectsHub')!).backgroundColor,
    font: getComputedStyle(document.getElementById('viewProjectsHub')!).fontFamily,
    button: getComputedStyle(document.querySelector('.hub-template-btn')!).backgroundColor,
  }));
  expect(home.background).toBe('rgb(247, 247, 242)');
  expect(home.button).toBe('rgb(25, 76, 75)');
  await app.screenshot('theme-alignment-home');

  await browser.locator('#hubProjectsTab').click();
  await expect(browser.locator('.hub-projects-table .hub-open-workflow-btn').first()).toBeVisible();
  await app.screenshot('theme-alignment-projects');
  await browser.locator('.hub-projects-table .hub-open-workflow-btn').first().click();
  await expect(browser.locator('#viewStudio')).toBeVisible();
  const workflow = await browser.evaluate(() => ({
    font: getComputedStyle(document.querySelector('.app-shell')!).fontFamily,
  }));
  expect(home.font).toBe(workflow.font);
  await app.screenshot('theme-alignment-workflow');

  await browser.locator('#brandLogoHome').click();
  await browser.locator('#tabDashboardBuilder').click();
  await expect(browser.locator('#viewDashboardBuilder.builder-light-mode')).toBeVisible();
  await expect(browser.locator('#builderThemeText')).toContainText('Terang');
  const dashboard = await browser.evaluate(() => ({
    background: getComputedStyle(document.getElementById('viewDashboardBuilder')!).backgroundColor,
    font: getComputedStyle(document.getElementById('viewDashboardBuilder')!).fontFamily,
    save: getComputedStyle(document.getElementById('btnBuilderSaveLayout')!).backgroundColor,
  }));
  expect(dashboard.background).toBe(home.background);
  expect(dashboard.font).toBe(workflow.font);
  expect(dashboard.save).toBe(home.button);
  await app.screenshot('theme-alignment-dashboard');
});
