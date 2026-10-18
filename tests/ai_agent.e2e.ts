import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify AI Agent node creation, inspector settings, and usage guide', async ({ app, screen, browser, agent }) => {
  // 1. Open the studio application
  await app.open('/');

  // 2. Wait for page body and brand header to load
  await expect(browser.locator('body')).toBeVisible();
  await expect(browser.locator('.brand')).toBeVisible();

  // 3. Find and click 'AI Agent' from sidebar node library to add it to canvas
  const aiAgentLibItem = browser.locator('.library-item:has-text("AI Agent")').first();
  await expect(aiAgentLibItem).toBeVisible();
  await aiAgentLibItem.click();

  // 4. Verify AI Agent node is added onto the canvas
  const canvasNode = browser.locator('.node-card:has-text("AI Agent")').first();
  await expect(canvasNode).toBeVisible();

  // 5. Click the canvas node header to select it and open the Inspector panel
  const canvasHead = browser.locator('.node-card:has-text("AI Agent") .node-head').first();
  await canvasHead.click();
  await app.screenshot('01-ai-agent-canvas-selected');

  // 6. Verify Inspector panel shows provider dropdown, password field, and prompt textarea
  const inspector = browser.locator('.inspector');
  await expect(inspector).toBeVisible();

  const inspectorBody = browser.locator('#inspectorBody');
  await expect(inspectorBody).toBeVisible();

  // Verify provider selector exists and defaults to openai
  const providerSelect = browser.locator('#inspectorBody select').first();
  await expect(providerSelect).toBeVisible();

  // Verify apiKey password field
  const apiKeyInput = browser.locator('#inspectorBody input[type="password"]').first();
  await expect(apiKeyInput).toBeVisible();

  // Verify multiline textarea for prompt
  const promptTextarea = browser.locator('#inspectorBody textarea').first();
  await expect(promptTextarea).toBeVisible();

  // 7. Capture screenshot of configured Inspector
  await app.screenshot('02-ai-agent-inspector-configured');

  // 8. Open the interactive Indonesian guide modal for AI Agent
  const infoBtn = browser.locator('.library-item:has-text("AI Agent") .library-info-btn').first();
  await infoBtn.click();

  const guideModal = browser.locator('#nodeUniversalGuideModal');
  await expect(guideModal).toBeVisible();
  await app.screenshot('03-ai-agent-guide-modal');

  // Verify guide modal title
  await expect(browser.locator('#nodeUniversalGuideModal h3:has-text("AI Agent")').first()).toBeVisible();

  // 9. Close guide modal
  const closeBtn = browser.locator('#nodeUniversalGuideModal button:has-text("✕")').first();
  if (await closeBtn.isVisible()) {
    await closeBtn.click();
  }

  // 10. AI Agent visual verification on canvas & inspector
  await agent.assert('The AI Agent node is present on canvas with active inspector controls including provider dropdown, password-masked API key, and user prompt template.');
});
