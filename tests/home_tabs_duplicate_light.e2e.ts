import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('home tabs duplicate a saved project and dashboard opens light', async ({ app, browser }) => {
  const base = process.env.APP_URL ?? 'http://127.0.0.1:8765';
  const name = `E2E Duplicate ${Date.now()}`;
  const created = await (await fetch(`${base}/api/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })).json();
  const sourceId = created.project.id;
  let duplicateId = '';

  try {
    await app.open('/');
    await expect(browser.locator('#hubTemplatesSection')).toBeVisible();
    await browser.locator('#hubProjectsTab').click();
    await expect(browser.locator('#hubRecentProjectsSection')).toBeVisible();
    const tabState = await browser.evaluate(() => ({
      templatesHidden: document.getElementById('hubTemplatesSection')?.hidden,
      projectsSelected: document.getElementById('hubProjectsTab')?.getAttribute('aria-selected'),
    }));
    expect(tabState.templatesHidden).toBe(true);
    expect(tabState.projectsSelected).toBe('true');

    const sourceRow = browser.locator('.hub-project-card').filter({ hasText: name }).first();
    await expect(sourceRow).toBeVisible();
    await browser.locator(`.hub-project-card:has-text("${name}") .hub-duplicate-project-btn`).first().click();
    const copyRow = browser.locator('.hub-project-card').filter({ hasText: `${name} (Salinan)` }).first();
    await expect(copyRow).toBeVisible();
    await app.screenshot('home-project-tab-duplicate');
    await browser.evaluate(() => document.getElementById('hubRecentProjectsSection')?.scrollIntoView());
    await app.screenshot('home-project-duplicate-row');

    const projects = (await (await fetch(`${base}/api/projects`)).json()).projects;
    duplicateId = projects.find((project: { name: string }) => project.name === `${name} (Salinan)`)?.id || '';
    expect(duplicateId).not.toBe('');
    expect(duplicateId).not.toBe(sourceId);
    const source = await (await fetch(`${base}/api/projects/${sourceId}`)).json();
    const copy = await (await fetch(`${base}/api/projects/${duplicateId}`)).json();
    expect(copy.workflow).toEqual(source.workflow);

    await browser.locator('#hubTemplatesTab').click();
    await expect(browser.locator('#hubTemplatesSection')).toBeVisible();
    await browser.locator('#tabDashboardBuilder').click();
    await expect(browser.locator('#viewDashboardBuilder')).toBeVisible();
    await expect(browser.locator('#builderThemeText')).toContainText('Terang');
    expect(await browser.evaluate(() => document.getElementById('viewDashboardBuilder')?.classList.contains('builder-light-mode'))).toBe(true);
    await app.screenshot('dashboard-designer-default-light');
  } finally {
    if (duplicateId) await fetch(`${base}/api/projects/${duplicateId}`, { method: 'DELETE' });
    await fetch(`${base}/api/projects/${sourceId}`, { method: 'DELETE' });
  }
});
