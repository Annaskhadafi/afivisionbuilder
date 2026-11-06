import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('Object Tracking can enable and persist Roboflow ReID settings', async ({ app, browser }) => {
  const projectName = 'ReID Tracker E2E';
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  const created = await browser.evaluate(async (name) => {
    const workflow = {
      nodes: [
        { id: 'input', type: 'input', title: 'Input', x: 50, y: 100, enabled: true,
          config: { sourceType: 'image', filePath: 'static/logo.png', loop: true } },
        { id: 'tracker', type: 'tracker', title: 'Object Tracking', x: 330, y: 100, enabled: true,
          config: { algorithm: 'bytetrack', enableReid: false } },
        { id: 'preview', type: 'preview', title: 'Live Preview', x: 600, y: 100, enabled: true,
          config: {} },
      ],
      edges: [['input', 'tracker'], ['tracker', 'preview']],
    };
    const response = await fetch('/api/projects', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, workflow }),
    });
    return { ok: response.ok, body: await response.json() };
  }, projectName);
  expect(created.ok).toBe(true);

  await app.open('/');
  await browser.locator('#hubProjectsTab').click();
  const project = browser.locator(`.hub-project-card:has-text("${projectName}") .hub-open-workflow-btn`).first();
  await expect(project).toBeVisible({ timeout: 10000 });
  await project.click();
  await expect(browser.locator('#viewStudio')).toBeVisible({ timeout: 15000 });
  await browser.locator('.node-card:has-text("Object Tracking") .node-head').click();

  const enable = browser.locator('[data-field-key="enableReid"] input[type="checkbox"]');
  await expect(enable).toBeVisible();
  await enable.check();
  const model = browser.locator('[data-field-key="reidModel"] select');
  const device = browser.locator('[data-field-key="reidDevice"] select');
  await expect(model).toBeVisible();
  await model.selectOption({ value: 'osnet_x1_0_msmt17_combineall' });
  await device.selectOption({ value: 'cpu' });
  await expect(browser.locator('[data-field-key="reidAppearanceThreshold"] input[type="range"]')).toBeVisible();
  await app.screenshot('reid-enabled-tracker-inspector');

  await browser.locator('#saveBtn').click();
  await expect(browser.locator('.toast')).toBeVisible({ timeout: 5000 });

  await app.open('/');
  await browser.locator('#hubProjectsTab').click();
  await browser.locator(`.hub-project-card:has-text("${projectName}") .hub-open-workflow-btn`).first().click();
  await expect(browser.locator('#viewStudio')).toBeVisible({ timeout: 15000 });
  await browser.locator('.node-card:has-text("Object Tracking") .node-head').click();
  await expect(browser.locator('[data-field-key="enableReid"] input[type="checkbox"]')).toBeChecked();
  await expect(browser.locator('[data-field-key="reidModel"] select')).toHaveValue('osnet_x1_0_msmt17_combineall');
  await expect(browser.locator('[data-field-key="reidDevice"] select')).toHaveValue('cpu');
  await app.screenshot('reid-tracker-settings-after-reload');
});
