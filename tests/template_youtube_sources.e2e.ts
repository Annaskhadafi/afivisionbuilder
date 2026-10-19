import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify 5 real-world production templates and YouTube stream input configuration', async ({ app, browser, agent }) => {
  // 1. Open Projects & Templates Hub
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();
  await expect(browser.locator('#viewProjectsHub')).toBeVisible();

  // 2. Verify all 5 production templates exist in the Hub
  await expect(browser.locator('.hub-template-card:has-text("Smart Traffic Flow & Vehicle Counter")')).toBeVisible();
  await expect(browser.locator('.hub-template-card:has-text("Restaurant Table Occupancy")')).toBeVisible();
  await expect(browser.locator('.hub-template-card:has-text("Assembly Line & Workshop Cycle Timer")')).toBeVisible();
  await expect(browser.locator('.hub-template-card:has-text("Warehouse Dock & Forklift Safety Guard")')).toBeVisible();
  await expect(browser.locator('.hub-template-card:has-text("Retail Checkout Queue & Hotspot Analyzer")')).toBeVisible();

  // 3. Test Category Filter Pill for Trafik & Smart City
  const trafikPill = browser.locator('#hubCatPillTrafik');
  await expect(trafikPill).toBeVisible();
  await trafikPill.click();

  // Verify only Traffic template is visible in filtered state
  await expect(browser.locator('.hub-template-card:has-text("Smart Traffic Flow & Vehicle Counter")')).toBeVisible();
  await expect(browser.locator('.hub-template-card:has-text("Assembly Line & Workshop Cycle Timer")')).toBeHidden();

  // Reset to All Solutions
  await browser.locator('#hubCatPillAll').click();
  await expect(browser.locator('.hub-template-card:has-text("Smart Traffic Flow & Vehicle Counter")')).toBeVisible();

  // Take Screenshot 1: Hub with 5 Production Templates & Category Pills
  await app.screenshot('01-hub-production-templates-with-youtube');

  // 4. Click "Gunakan Template" on Smart Traffic Flow & Vehicle Counter
  await browser.locator('.hub-template-card:has-text("Smart Traffic Flow & Vehicle Counter") .hub-template-btn').click();

  // 5. Verify transition to Studio Canvas with loaded workflow
  await expect(browser.locator('#viewStudio')).toBeVisible();
  await expect(browser.locator('#viewProjectsHub')).toBeHidden();

  // 6. Verify pipeline nodes on canvas
  await expect(browser.locator('.node-card:has-text("Input")')).toBeVisible();
  await expect(browser.locator('.node-card:has-text("Object Detection")')).toBeVisible();
  await expect(browser.locator('.node-card:has-text("Object Tracking")')).toBeVisible();
  await expect(browser.locator('.node-card:has-text("Multi-Zone Occupancy")')).toBeVisible();
  await expect(browser.locator('.node-card:has-text("Overlay / Annotate")')).toBeVisible();
  await expect(browser.locator('.node-card:has-text("Alert Output")')).toBeVisible();
  await expect(browser.locator('.node-card:has-text("Database Output")')).toBeVisible();
  await expect(browser.locator('.node-card:has-text("Live Preview")')).toBeVisible();

  // Take Screenshot 2: Studio Canvas with Complete Traffic Pipeline
  await app.screenshot('02-traffic-template-studio-canvas');

  // 7. Select Input node to inspect YouTube settings
  const inputNode = browser.locator('.node-card:has-text("Input")');
  await inputNode.click();

  // 8. Verify Inspector shows YouTube configuration
  await expect(browser.locator('.inspector h2')).toContainText('Input');
  await expect(browser.locator('.inspector label:has-text("Jenis Sumber Video/Kamera")')).toBeVisible();
  
  // Verify YouTube Source Type option is selected
  const sourceTypeSelect = browser.locator('.inspector select').first();
  await expect(sourceTypeSelect).toHaveValue('youtube');

  // Verify YouTube URL field contains pre-configured public demo URL
  const youtubeUrlInput = browser.locator('.inspector input[name="youtubeUrl"]');
  await expect(youtubeUrlInput).toBeVisible();
  const urlValue = await youtubeUrlInput.inputValue();
  expect(urlValue).toContain('youtube.com');

  // Take Screenshot 3: Input Node Inspector with YouTube Stream configuration
  await app.screenshot('03-youtube-input-inspector');

  // 9. AI Agent Verification
  await agent.assert('the visual builder displays the smart traffic flow workflow with youtube stream input and pipeline nodes configured');
});
