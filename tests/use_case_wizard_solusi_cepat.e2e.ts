import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Solusi Cepat works and canvas empty state is clean without buka panduan', async ({ app, browser, agent }) => {
  // 1. Open the studio application
  await app.open('/');
  await expect(browser.locator('body')).toBeVisible();

  // 2. Switch to Studio canvas via #tabStudio
  const tabStudio = browser.locator('#tabStudio');
  await expect(tabStudio).toBeVisible();
  await tabStudio.click();

  // 3. Wait for canvas workspace
  await expect(browser.locator('#viewStudio')).toBeVisible();
  await expect(browser.locator('#canvas')).toBeVisible();
  await expect(browser.locator('#openUseCaseWizardBtn')).toBeVisible();

  // 4. Verify that #emptyCanvasWizardBtn does NOT exist on the canvas
  const emptyCanvasBtn = browser.locator('#emptyCanvasWizardBtn');
  await expect(emptyCanvasBtn).toHaveCount(0);

  // 5. Verify no text mentions "Buka Panduan Solusi Siap Pakai" on the canvas
  await expect(browser.locator('#canvas')).not.toContainText('Buka Panduan Solusi Siap Pakai');

  await app.screenshot('01-canvas-clean-without-buka-panduan');

  // 6. Click the "✨ Solusi Cepat" button in the canvas toolbar
  const solusiCepatBtn = browser.locator('#openUseCaseWizardBtn');
  await expect(solusiCepatBtn).toBeVisible();
  await solusiCepatBtn.click();

  // 7. Verify that #useCaseWizardModal opens properly
  const wizardModal = browser.locator('#useCaseWizardModal');
  await expect(wizardModal).toBeVisible();
  await expect(browser.locator('#useCaseWizardModal h2')).toContainText('Pilih Kebutuhan Pemantauan Anda');

  // 8. Verify all 4 use-case solution cards are displayed
  const wizardCards = browser.locator('#useCaseWizardModal .wizard-card');
  await expect(wizardCards).toHaveCount(4);

  await app.screenshot('02-solusi-cepat-wizard-modal-open');

  // 9. Click on the first solution: Traffic Flow & Vehicle Counter
  const trafficCard = browser.locator('.wizard-card[data-wizard-template="traffic_flow_counter"]');
  await expect(trafficCard).toBeVisible();
  await trafficCard.click();

  // 10. Verify modal closes and pipeline nodes are mounted on canvas
  await expect(wizardModal).toBeHidden();
  await expect(browser.locator('#nodes .node-card')).not.toHaveCount(0);

  // 11. Verify toast appears confirming successful solution application
  await expect(browser.locator('#toast')).toContainText('Solusi');

  await app.screenshot('03-pipeline-assembled-on-canvas');

  // 12. Re-open wizard modal and verify close button works
  await solusiCepatBtn.click();
  await expect(wizardModal).toBeVisible();
  await browser.locator('#closeWizardModalBtn').click();
  await expect(wizardModal).toBeHidden();

  await app.screenshot('04-wizard-modal-closed-safely');

  // 13. Verify AI agent judgment
  await agent.assert('the canvas displays the assembled workflow nodes and no unwanted guide banners are present');
});
