import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify YOLO-World zero-shot text prompting and Roboflow Universe inference engine', async ({ app, browser }) => {
  // 1. Open Studio
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // Switch to studio if on projects hub
  const hubView = browser.locator('#viewProjectsHub');
  if (await hubView.isVisible()) {
    // Select the first template to enter studio
    await browser.locator('.hub-template-card .hub-template-btn').first().click();
  }

  await expect(browser.locator('#viewStudio')).toBeVisible();

  // 2. Click on Object Detection node
  const detNode = browser.locator('.node-card:has-text("Object Detection")').first();
  await expect(detNode).toBeVisible();
  await detNode.click();

  // 3. Verify Inspector panel opens
  await expect(browser.locator('.inspector h2')).toContainText('Object Detection');

  // Find Engine dropdown in Inspector using data-field-key="engine"
  const engineSelect = browser.locator('.inspector .field[data-field-key="engine"] select');
  await expect(engineSelect).toBeVisible();

  // 4. Select YOLO-World (Zero-Shot Text Prompt)
  await engineSelect.selectOption({ value: 'yolo_world' });

  // Verify YOLO-World specific field for prompt classes is visible
  const customClassesWrap = browser.locator('.inspector .field[data-field-key="customClasses"]');
  await expect(customClassesWrap).toBeVisible();

  const customClassesInput = browser.locator('.inspector .field[data-field-key="customClasses"] input').first();
  await customClassesInput.fill('forklift, safety vest, pallet, helmet');

  // Take Screenshot 1: YOLO-World Zero-Shot text prompting in inspector
  await app.screenshot('01-yolo-world-zero-shot-inspector');

  // 5. Select Roboflow Universe (Model ID)
  await engineSelect.selectOption({ value: 'roboflow_universe' });

  // Verify Roboflow Model ID and API Key fields are visible
  const modelIdWrap = browser.locator('.inspector .field[data-field-key="modelPath"]');
  await expect(modelIdWrap).toBeVisible();
  await expect(browser.locator('.inspector .field[data-field-key="modelPath"] .field-label-text')).toHaveText('Roboflow Universe Model ID');
  // Upload button and registry dropdown must be hidden for Roboflow Universe
  await expect(browser.locator('.inspector .field[data-field-key="modelPath"] button')).toHaveCount(0);
  await expect(browser.locator('.inspector .field[data-field-key="modelPath"] select')).toHaveCount(0);

  const modelIdInput = browser.locator('.inspector .field[data-field-key="modelPath"] input').first();
  await modelIdInput.fill('warehouse-safety/3');

  const apiKeyWrap = browser.locator('.inspector .field[data-field-key="roboflowApiKey"]');
  await expect(apiKeyWrap).toBeVisible();
  const apiKeyInput = browser.locator('.inspector .field[data-field-key="roboflowApiKey"] input').first();
  await apiKeyInput.fill('rf_mock_api_key_test');

  // Verify NO error toast appeared (specifically no "Model tidak dapat dimuat")
  const errorToast = browser.locator('.toast.error, .toast:has-text("tidak dapat dimuat")');
  await expect(errorToast).toHaveCount(0);

  // Take Screenshot 2: Roboflow Universe inference configuration
  await app.screenshot('02-roboflow-universe-model-inspector');

  // 6. Verify Save button works
  const saveBtn = browser.locator('#saveBtn');
  if (await saveBtn.isVisible()) {
    await saveBtn.click();
  }

  // 7. Verify canvas state retains node
  await expect(browser.locator('.node-card:has-text("Object Detection")')).toBeVisible();
});
