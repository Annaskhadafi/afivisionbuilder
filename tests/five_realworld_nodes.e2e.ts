import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify 5 Real-World Industrial Nodes: Dominant Color, Class Replacement, Man Down, LPR, and Overstack', async ({ app, browser, agent }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // Open workflow from Projects Hub if visible
  const openProjBtn = browser.locator('button:has-text("Buka Workflow →"), button:has-text("Open workflow →")').first();
  if (await openProjBtn.isVisible()) {
    await openProjBtn.click();
  } else {
    const studioBtn = browser.locator('button:has-text("Studio")').first();
    if (await studioBtn.isVisible()) {
      await studioBtn.click();
    }
  }
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible({ timeout: 10000 });
  const guideModal = browser.locator('#nodeUniversalGuideModal');

  // 2. Test Node 1: Dominant Color Inspector
  const colorLib = browser.locator('.library-item:has-text("Dominant Color Inspector")').first();
  await expect(colorLib).toBeVisible();
  await colorLib.click();

  const colorNode = browser.locator('.node-card:has-text("Dominant Color Inspector")').first();
  await expect(colorNode).toBeVisible();
  await browser.locator('.node-card:has-text("Dominant Color Inspector") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Dominant Color Inspector');
  await app.screenshot('01-dominant-color-inspector');

  const colorInfoBtn = browser.locator('.library-item:has-text("Dominant Color Inspector") .library-info-btn').first();
  await colorInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('02-dominant-color-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 3. Test Node 2: Class Replacement
  const classLib = browser.locator('.library-item:has-text("Class Replacement")').first();
  await expect(classLib).toBeVisible();
  await classLib.click();

  const classNode = browser.locator('.node-card:has-text("Class Replacement")').first();
  await expect(classNode).toBeVisible();
  await browser.locator('.node-card:has-text("Class Replacement") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Class Replacement');
  await app.screenshot('03-class-replacement-inspector');

  const classInfoBtn = browser.locator('.library-item:has-text("Class Replacement") .library-info-btn').first();
  await classInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('04-class-replacement-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 4. Test Node 3: Man Down & Fall Detector
  const manDownLib = browser.locator('.library-item:has-text("Man Down & Fall Detector")').first();
  await expect(manDownLib).toBeVisible();
  await manDownLib.click();

  const manDownNode = browser.locator('.node-card:has-text("Man Down & Fall Detector")').first();
  await expect(manDownNode).toBeVisible();
  await browser.locator('.node-card:has-text("Man Down & Fall Detector") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Man Down & Fall Detector');
  await app.screenshot('05-man-down-inspector');

  const manDownInfoBtn = browser.locator('.library-item:has-text("Man Down & Fall Detector") .library-info-btn').first();
  await manDownInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('06-man-down-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 5. Test Node 4: License Plate Reader (LPR)
  const lprLib = browser.locator('.library-item:has-text("License Plate Reader (LPR)")').first();
  await expect(lprLib).toBeVisible();
  await lprLib.click();

  const lprNode = browser.locator('.node-card:has-text("License Plate Reader (LPR)")').first();
  await expect(lprNode).toBeVisible();
  await browser.locator('.node-card:has-text("License Plate Reader (LPR)") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('License Plate Reader (LPR)');
  await app.screenshot('07-lpr-license-plate-inspector');

  const lprInfoBtn = browser.locator('.library-item:has-text("License Plate Reader (LPR)") .library-info-btn').first();
  await lprInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('08-lpr-license-plate-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 6. Test Node 5: Overstack Clearance Detector
  const overstackLib = browser.locator('.library-item:has-text("Overstack Clearance Detector")').first();
  await expect(overstackLib).toBeVisible();
  await overstackLib.click();

  const overstackNode = browser.locator('.node-card:has-text("Overstack Clearance Detector")').first();
  await expect(overstackNode).toBeVisible();
  await browser.locator('.node-card:has-text("Overstack Clearance Detector") .node-head').first().click();

  await expect(browser.locator('#inspectorBody')).toBeVisible();
  await expect(browser.locator('#inspectorTitle')).toContainText('Overstack Clearance Detector');
  await app.screenshot('09-overstack-detector-inspector');

  const overstackInfoBtn = browser.locator('.library-item:has-text("Overstack Clearance Detector") .library-info-btn').first();
  await overstackInfoBtn.click();
  await expect(guideModal).toBeVisible();
  await app.screenshot('10-overstack-detector-guide');
  await browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first().click();

  // 7. Capture full canvas with all 5 nodes present
  await app.screenshot('11-canvas-all-five-nodes');
});
