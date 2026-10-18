import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Projects Hub landing page, left rail navigation, and central Models Registry', async ({ app, browser }) => {
  // 1. Open Web Application: Should land on Projects & Templates Hub (Screenshot 1)
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();
  await expect(browser.locator('#viewProjectsHub')).toBeVisible();
  await expect(browser.locator('#viewStudio')).toBeHidden();

  // Verify Hub Hero elements
  await expect(browser.locator('.hub-hero-header h1')).toHaveText('Projects');
  await expect(browser.locator('#hubNewProjectBtn')).toBeVisible();
  await expect(browser.locator('#hubImportBtn')).toBeVisible();
  await expect(browser.locator('#hubBrowseTemplatesBtn')).toBeVisible();

  // Verify Recent Projects & Templates grids
  await expect(browser.locator('.hub-project-card').first()).toBeVisible();
  await expect(browser.locator('.hub-template-card').first()).toBeVisible();
  await expect(browser.locator('.hub-template-card:has-text("Bottle Visual Inspection")')).toBeVisible();

  // Take Screenshot 1: Projects Hub
  await app.screenshot('01-projects-hub-home');

  // 2. Open Workflow from Recent Projects Card
  const openBtn = browser.locator('.hub-open-workflow-btn').first();
  await openBtn.click();

  // Verify transition to Project Studio (Screenshot 2 workflow mode)
  await expect(browser.locator('#viewStudio')).toBeVisible();
  await expect(browser.locator('#viewProjectsHub')).toBeHidden();
  await expect(browser.locator('#projectSwitcherBtn')).toBeVisible();
  await expect(browser.locator('#projectLeftRail')).toBeVisible();
  await expect(browser.locator('#railTabWorkflow')).toBeVisible();
  await expect(browser.locator('#railTabModels')).toBeVisible();

  // Take Screenshot 2: Project Studio Canvas
  await app.screenshot('02-project-workflow-canvas');

  // 3. Switch to Models Tab via Left Rail (Screenshot 2 models mode)
  await browser.locator('#railTabModels').click();
  await expect(browser.locator('#viewModelManager')).toBeVisible();
  await expect(browser.locator('#studioSidebar')).toBeHidden();
  await expect(browser.locator('.models-panel-title h2')).toHaveText('Models');
  await expect(browser.locator('#modelsAddBtn')).toBeVisible();
  await expect(browser.locator('#modelsTableBody tr').first()).toBeVisible();

  // Verify table columns and entries
  await expect(browser.locator('.models-table th:has-text("Name")')).toBeVisible();
  await expect(browser.locator('.models-table th:has-text("Type")')).toBeVisible();
  await expect(browser.locator('.models-table th:has-text("Version")')).toBeVisible();
  await expect(browser.locator('.models-table th:has-text("Size")')).toBeVisible();
  await expect(browser.locator('.models-table th:has-text("Status")')).toBeVisible();
  await expect(browser.locator('.models-table th:has-text("Engine")')).toBeVisible();
  await expect(browser.locator('.models-table th:has-text("Format")')).toBeVisible();
  await expect(browser.locator('.models-table td:has-text("yolov8n.pt")').first()).toBeVisible();

  // Take Screenshot 3: Models Hub Table
  await app.screenshot('03-project-models-table');

  // 4. Test Add Model Modal Dialog
  await browser.locator('#modelsAddBtn').click();
  await expect(browser.locator('#addModelModal')).toBeVisible();
  await expect(browser.locator('#modelDropZone')).toBeVisible();

  // Take Screenshot 4: Add Model Modal
  await app.screenshot('04-add-model-modal');

  await browser.locator('#closeAddModelModal').click();

  // 5. Switch Back to Workflow and Check Inspector Model Dropdown
  await browser.locator('#railTabWorkflow').click();
  await expect(browser.locator('#studioSidebar')).toBeVisible();
  await expect(browser.locator('#viewModelManager')).toBeHidden();

  // 6. Test Back to Projects Hub via [Folder] Project Button
  await browser.locator('#projectSwitcherBtn').click();
  await expect(browser.locator('#viewProjectsHub')).toBeVisible();
  await expect(browser.locator('#viewStudio')).toBeHidden();

  // Take Screenshot 5: Returned to Projects Hub
  await app.screenshot('05-back-to-hub');
});
