import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify Restaurant Table Occupancy and Dwell Time template creation and studio canvas', async ({ app, browser, agent }) => {
  // 1. Open Web Application to Projects & Templates Hub
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();
  await expect(browser.locator('#viewProjectsHub')).toBeVisible();

  // 2. Verify Restaurant Template card is prominently featured
  await expect(browser.locator('.hub-template-card:has-text("Restaurant Table Occupancy")')).toBeVisible();
  await expect(browser.locator('.hub-template-card:has-text("Restaurant Table Occupancy") .hub-template-title')).toContainText('Restaurant Table Occupancy');
  await expect(browser.locator('.hub-template-card:has-text("Restaurant Table Occupancy") .hub-template-tags')).toContainText('Restaurant');
  await expect(browser.locator('.hub-template-card:has-text("Restaurant Table Occupancy") .hub-template-tags')).toContainText('Table Tracker');

  // Take Screenshot 1: Hub with Restaurant Template Card
  await app.screenshot('01-restaurant-template-hub-card');

  // 3. Click "Use template ->" on the Restaurant card
  await browser.locator('.hub-template-card:has-text("Restaurant Table Occupancy") .hub-template-btn').click();

  // 4. Verify transition to Studio Canvas with the new project
  await expect(browser.locator('#viewStudio')).toBeVisible();
  await expect(browser.locator('#viewProjectsHub')).toBeHidden();

  // 5. Verify the pipeline nodes exist on canvas
  await expect(browser.locator('.node-card:has-text("Input")')).toBeVisible();
  await expect(browser.locator('.node-card:has-text("Object Detection")')).toBeVisible();
  await expect(browser.locator('.node-card:has-text("Object Tracking")')).toBeVisible();
  await expect(browser.locator('.node-card:has-text("Multi-Zone Occupancy")')).toBeVisible();
  await expect(browser.locator('.node-card:has-text("Overlay / Annotate")')).toBeVisible();
  await expect(browser.locator('.node-card:has-text("Database Output")')).toBeVisible();
  await expect(browser.locator('.node-card:has-text("Live Preview")')).toBeVisible();

  // 6. Select Multi-Zone Occupancy node to view Table Settings Inspector
  const multiZoneNode = browser.locator('.node-card:has-text("Multi-Zone Occupancy")');
  await multiZoneNode.click();

  // Verify inspector elements
  await expect(browser.locator('.inspector h2')).toContainText('Multi-Zone Occupancy');
  await expect(browser.locator('.inspector:has-text("1. Meja 01 (VIP 4-Seat)")')).toBeVisible();
  await expect(browser.locator('.inspector:has-text("2. Meja 02 (4-Seat)")')).toBeVisible();
  await expect(browser.locator('.inspector:has-text("3. Meja 03 (2-Seat)")')).toBeVisible();
  await expect(browser.locator('.inspector:has-text("4. Meja 04 (2-Seat)")')).toBeVisible();

  // Take Screenshot 2: Studio Canvas and Inspector for Restaurant Table Tracker
  await app.screenshot('02-restaurant-workflow-studio-canvas');

  // 7. Verify via AI Agent
  await agent.assert('the restaurant table occupancy template is loaded into the workflow studio canvas with table zones configured');
});
