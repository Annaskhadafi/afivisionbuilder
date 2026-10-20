import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('Export Code checks and downloads a standalone workflow package', async ({ app, browser }) => {
  const base = process.env.APP_URL || 'http://127.0.0.1:8765';
  const created = await fetch(`${base}/api/projects`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      name: 'Export Code E2E',
      workflow: {
        nodes: [
          { id: 'input', type: 'input', enabled: true, config: { sourceType: 'camera', source: 0 } },
          { id: 'preview', type: 'preview', enabled: true, config: {} },
        ],
        edges: [['input', 'preview']],
      },
    }),
  });
  expect(created.ok).toBe(true);
  const projectId = (await created.json()).project.id;
  await app.open('/');
  await browser.locator('.hub-project-card .hub-open-workflow-btn').first().click();
  await browser.locator('#nodeSearch').fill('Export Code');
  await browser.locator('.library-item').filter({ hasText: 'Export Code' }).click();
  await expect(browser.locator('#inspectorTitle')).toContainText('Export Code');
  await app.screenshot('export-code-inspector');
  await browser.locator('#inspectorBody button').filter({ hasText: 'Periksa Paket' }).click();
  await expect(browser.locator('#exportCodeResult')).toContainText('Siap dibangun');
  const saved = await (await fetch(`${base}/api/projects/${projectId}`)).json();
  const exportNode = saved.workflow.nodes.find((node: { type: string }) => node.type === 'export_code');
  expect(exportNode).toBeTruthy();
  expect(saved.workflow.edges.some((edge: string[]) => edge.includes(exportNode.id))).toBe(false);
  await app.screenshot('export-code-preflight');
  await browser.locator('#inspectorBody button').filter({ hasText: 'Build & Download ZIP' }).click();
  await expect(browser.locator('#exportCodeResult')).toContainText('ZIP berhasil diunduh');
  await app.screenshot('export-code-download');
  const packageResponse = await fetch(`${base}/api/projects/${projectId}/export-code`, { method: 'POST' });
  expect(packageResponse.ok).toBe(true);
  const bytes = new Uint8Array(await packageResponse.arrayBuffer());
  expect(String.fromCharCode(bytes[0], bytes[1])).toBe('PK');
});
