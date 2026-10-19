import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify AI Studio Copilot drawer, OpenAI settings, and Enhanced Python Script Inspector with 1-frame visual preview', async ({ app, browser }) => {
  // 1. Open application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();

  // If on Projects Hub, enter studio via open workflow / template
  const hubView = browser.locator('#viewProjectsHub');
  if (await hubView.isVisible()) {
    const openBtn = browser.locator('.hub-open-workflow-btn, .hub-template-btn').first();
    if (await openBtn.isVisible()) {
      await openBtn.click();
    }
  }

  await expect(browser.locator('#viewStudio')).toBeVisible();

  // 2. Verify AI Copilot button on canvas toolbar and capture unified toolbar buttons
  const autoAssembleBtn = browser.locator('#autoAssembleBtn');
  const copilotToggleBtn = browser.locator('#toggleAiCopilotBtn');
  await expect(autoAssembleBtn).toBeVisible();
  await expect(copilotToggleBtn).toBeVisible();
  await expect(copilotToggleBtn).toContainText('AI Copilot');

  // Take Screenshot 0: Unified and High Contrast Toolbar Action Buttons
  await app.screenshot('00-toolbar-buttons-uniform-contrast');

  // 3. Open Floating AI Studio Copilot Drawer
  await copilotToggleBtn.click();
  const copilotDrawer = browser.locator('#studioAiCopilotDrawer');
  await expect(copilotDrawer).toBeVisible();
  await expect(browser.locator('.copilot-name')).toContainText('Studio Copilot');
  await expect(browser.locator('#copilotActiveModel')).toBeVisible();

  // Verify suggestion chips are present
  const quickChips = browser.locator('#copilotQuickChips button');
  await expect(quickChips.first()).toBeVisible();

  // Test Turn 1: AI Prompt to Generate Initial Workflow
  const promptInput = browser.locator('#copilotPromptInput');
  const sendBtn = browser.locator('#copilotSendBtn');
  await promptInput.fill('Buat alur deteksi kendaraan mobil dan motor dengan filter confidence 0.65');
  await sendBtn.click();

  // Wait for Turn 1 response card
  const applyBtnTurn1 = browser.locator('.copilot-apply-btn').first();
  await expect(applyBtnTurn1).toBeVisible({ timeout: 35000 });
  await applyBtnTurn1.click();
  await expect(applyBtnTurn1).toContainText('Telah Diterapkan');

  // Test Turn 2: Multi-turn Context Revision (Modify classes and confidence threshold)
  await promptInput.fill('Ganti kelasnya jadi mobil dan bus saja, dan ubah confidence detector ke 0.8');
  await sendBtn.click();

  // Wait for Turn 2 revision card with parameter diff
  const applyBtnTurn2 = browser.locator('.copilot-apply-btn').nth(1);
  await expect(applyBtnTurn2).toBeVisible({ timeout: 35000 });
  await expect(browser.locator('#studioAiCopilotDrawer .copilot-msg.assistant').last()).toContainText('Perubahan Parameter');
  await applyBtnTurn2.click();

  // Take Screenshot 1: AI Studio Copilot Drawer with multi-turn history and parameter revision diff
  await app.screenshot('01-ai-copilot-multiturn-revision');

  // Close drawer so it doesn't overlap the right-hand inspector
  await browser.locator('#copilotCloseDrawerBtn').click();
  await expect(copilotDrawer).toBeHidden();

  // 4. Test Settings Modal: AI Model field
  const settingsBtn = browser.locator('#hubSettingsBtn, .header-settings-btn').first();
  await settingsBtn.click();
  const settingsModal = browser.locator('#systemSettingsModal');
  await expect(settingsModal).toBeVisible();

  // Switch to Tab 2: AI & VLM Keys
  const vlmTabBtn = browser.locator('.settings-nav-tab[data-tab="vlm"]');
  await vlmTabBtn.click();

  const settingAiModel = browser.locator('#settingAiModel');
  await expect(settingAiModel).toBeVisible();

  // Take Screenshot 2: System Settings AI Model Field
  await app.screenshot('02-system-settings-ai-model-field');

  // Close Settings modal
  await browser.locator('#closeSystemSettingsModal').click();

  // 5. Add or Select a Custom Python Script node
  const searchInput = browser.locator('#nodeSearch');
  await searchInput.fill('Python');
  const pythonScriptItem = browser.locator('.library-item:has-text("Custom Python")').first();
  await expect(pythonScriptItem).toBeVisible();
  await pythonScriptItem.click();

  // Click node-head to focus inspector
  const pythonNode = browser.locator('.node-card:has-text("Custom Python") .node-head').first();
  await expect(pythonNode).toBeVisible();
  await pythonNode.click();

  // Verify inspector body opened
  const inspector = browser.locator('#inspectorBody');
  await expect(inspector).toBeVisible();

  // 6. Verify Enhanced Python Script Inspector components
  const presetSelect = browser.locator('.script-preset-select');
  await expect(presetSelect).toBeVisible();

  const aiPromptBtn = browser.locator('.script-ai-prompt-btn');
  await expect(aiPromptBtn).toBeVisible();

  const codeEditor = browser.locator('.script-code-editor');
  await expect(codeEditor).toBeVisible();

  const syntaxBadge = browser.locator('.script-syntax-badge');
  await expect(syntaxBadge).toBeVisible();
  await expect(syntaxBadge).toContainText('Valid Python AST');

  // 7. Test Preset Selection (e.g. Preset 1: Watermark & Timestamp)
  await presetSelect.selectOption({ index: 1 });
  await expect(codeEditor).toHaveValue(/AFI VISION BUILDER/);

  // 8. Test 1-Frame Sandbox Execution
  const runTestBtn = browser.locator('#runScriptTestBtn');
  await expect(runTestBtn).toBeVisible();
  await runTestBtn.click();

  // Verify preview grid with input and output images appears
  const previewGrid = browser.locator('#scriptTestPreviewGrid');
  await expect(previewGrid).toBeVisible({ timeout: 15000 });

  const inputImg = browser.locator('#scriptTestInputImg');
  const outputImg = browser.locator('#scriptTestOutputImg');
  await expect(inputImg).toBeVisible();
  await expect(outputImg).toBeVisible();

  const testStatus = browser.locator('.script-test-status');
  await expect(testStatus).toContainText('Sukses');

  // Take Screenshot 3: Enhanced Python Script Inspector with Side-by-Side Visual Preview
  await app.screenshot('03-python-script-enhanced-inspector-preview');

  // 9. Verify New Project starts with a completely Blank Canvas
  await browser.evaluate(async () => {
    window.confirm = () => true;
    window.prompt = () => 'Blank Canvas Project';
    if (window.newProject) {
      await window.newProject();
    }
  });

  // Verify project name updated
  await expect(browser.locator('#projectName')).toContainText('Blank Canvas Project');

  // Verify canvas has 0 nodes (completely blank canvas)
  const canvasNodes = browser.locator('#canvas .node-card');
  await expect(canvasNodes).toHaveCount(0);

  // Take Screenshot 4: Blank Canvas on New Project
  await app.screenshot('04-new-project-blank-canvas');
});

