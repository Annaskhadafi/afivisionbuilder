import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify wire line perfectly connects to node port circles without offset', async ({ app, browser }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // Open workflow from Projects Hub if visible
  const openWorkflowBtn = browser.locator('.hub-open-workflow-btn, button:has-text("Buka Workflow"), button:has-text("Open workflow")').first();
  if (await openWorkflowBtn.isVisible()) {
    await openWorkflowBtn.click();
  }
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 10000 });
  await expect(browser.locator('.node-card').first()).toBeVisible({ timeout: 10000 });

  // 2. Measure port centers vs SVG path endpoints on canvas
  const alignmentCheck = await browser.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.node-card'));
    const ports = {};
    cards.forEach(c => {
      const inPort = c.querySelector('.port.input');
      const outPort = c.querySelector('.port.output');
      const cRect = c.getBoundingClientRect();
      const inRect = inPort ? inPort.getBoundingClientRect() : null;
      const outRect = outPort ? outPort.getBoundingClientRect() : null;
      const nx = parseFloat(c.style.left) || 0;
      const ny = parseFloat(c.style.top) || 0;
      ports[c.dataset.id] = {
        inCenter: inRect ? {
          x: nx + (inRect.left + inRect.width / 2 - cRect.left),
          y: ny + (inRect.top + inRect.height / 2 - cRect.top)
        } : null,
        outCenter: outRect ? {
          x: nx + (outRect.left + outRect.width / 2 - cRect.left),
          y: ny + (outRect.top + outRect.height / 2 - cRect.top)
        } : null
      };
    });

    const edgePaths = Array.from(document.querySelectorAll('#edges .edge-visible-path')).map(p => p.getAttribute('d'));
    return { ports, edgePaths };
  });

  expect(alignmentCheck.edgePaths.length).toBeGreaterThan(0);

  // Parse path start and end
  for (const d of alignmentCheck.edgePaths) {
    const match = d.match(/M\s+([\d.]+)\s+([\d.]+)\s+C.*,\s+([\d.]+)\s+([\d.]+)$/);
    if (match) {
      const [, x1, y1, x2, y2] = match.map(Number);
      // Verify x1, y1 matches an output port center within 1px
      const sourceMatch = Object.values(alignmentCheck.ports).some(
        (p: any) => p.outCenter && Math.abs(p.outCenter.x - x1) <= 1.5 && Math.abs(p.outCenter.y - y1) <= 1.5
      );
      // Verify x2, y2 matches an input port center within 1px
      const targetMatch = Object.values(alignmentCheck.ports).some(
        (p: any) => p.inCenter && Math.abs(p.inCenter.x - x2) <= 1.5 && Math.abs(p.inCenter.y - y2) <= 1.5
      );
      expect(sourceMatch).toBe(true);
      expect(targetMatch).toBe(true);
    }
  }

  // 3. Take screenshot of canvas with aligned wires
  await app.screenshot('01-wire-port-aligned-canvas');

  // 4. Test interactive wire pulling from output port
  const firstOutPort = browser.locator('.node-card .port.output').first();
  await firstOutPort.click();
  await browser.mouse.move(500, 300);
  await expect(browser.locator('.edge-preview-wire')).toBeAttached();

  await app.screenshot('02-interactive-wire-pulling');

  // Cancel connecting by hitting Esc
  await browser.keyboard.press('Escape');
  await expect(browser.locator('.edge-preview-wire')).toHaveCount(0);
});
