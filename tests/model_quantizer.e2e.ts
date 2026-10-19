import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Model Quantizer and Optimizer modal, precision options, and UI workflow', async ({ app, browser }) => {
  // 1. Open application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // If on Projects Hub, enter studio via first template or open workflow button
  const hubView = browser.locator('#viewProjectsHub');
  if (await hubView.isVisible()) {
    const openBtn = browser.locator('.hub-open-workflow-btn, .hub-template-btn').first();
    if (await openBtn.isVisible()) {
      await openBtn.click();
    }
  }

  await expect(browser.locator('#viewStudio')).toBeVisible();

  // 2. Switch to Models tab via Left Rail navigation
  const railTabModels = browser.locator('#railTabModels');
  await expect(railTabModels).toBeVisible();
  await railTabModels.click();

  // 3. Verify Models Manager panel is displayed
  const modelManager = browser.locator('#viewModelManager');
  await expect(modelManager).toBeVisible();

  // 4. Verify Quantize & Optimize button is present on toolbar
  const quantizeBtn = browser.locator('#modelsQuantizeBtn');
  await expect(quantizeBtn).toBeVisible();
  await expect(quantizeBtn).toContainText('Quantize / Optimize Model');

  // 5. Click Quantize & Optimize button to open modal
  await quantizeBtn.click();

  // 6. Verify Quantize Modal opens
  const quantizeModal = browser.locator('#quantizeModelModal');
  await expect(quantizeModal).toBeVisible();
  await expect(browser.locator('#quantizeModelModal h2')).toContainText('Model Quantizer & Optimizer');

  // 7. Verify all quantization options are rendered properly
  const sourceSelect = browser.locator('#quantizeSourceSelect');
  await expect(sourceSelect).toBeVisible();

  const int8Radio = browser.locator('input[name="quantizeTargetFormat"][value="tflite_int8"]');
  const fp16Radio = browser.locator('input[name="quantizeTargetFormat"][value="tflite_fp16"]');
  const onnxInt8Radio = browser.locator('input[name="quantizeTargetFormat"][value="onnx_int8"]');

  await expect(int8Radio).toBeVisible();
  await expect(fp16Radio).toBeVisible();
  await expect(onnxInt8Radio).toBeVisible();

  // Verify resolution selector
  const imageSizeSelect = browser.locator('#quantizeImageSize');
  await expect(imageSizeSelect).toBeVisible();

  // Take Screenshot 1: Model Quantizer modal open with full options
  await app.screenshot('01-model-quantizer-modal-open');

  // 8. Select TFLite FP16 option
  await fp16Radio.check();
  await expect(fp16Radio).toBeChecked();

  // Select 480x480 resolution
  await imageSizeSelect.selectOption({ value: '480' });

  // Take Screenshot 2: Options selected
  await app.screenshot('02-model-quantizer-options-selected');

  // 9. Close modal via cancel button
  const cancelBtn = browser.locator('#cancelQuantizeBtn');
  await cancelBtn.click();

  // 10. Switch back to Workflow canvas
  const railTabWorkflow = browser.locator('#railTabWorkflow');
  await railTabWorkflow.click();
  await expect(browser.locator('#studioWorkflowArea')).toBeVisible();
});
