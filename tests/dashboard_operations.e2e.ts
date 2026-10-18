import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('verify operational dashboard: multi-camera matrix, workshop sessions, warehouse events, and tab navigation', async ({ app, browser, agent }) => {
  // 1. Open Studio application
  await app.open('/');
  await expect(browser.locator('.brand')).toBeVisible();
  await expect(browser.locator('#tabStudio')).toBeVisible();
  await expect(browser.locator('#tabLiveCameras')).toBeVisible();
  await expect(browser.locator('#tabSessions')).toBeVisible();
  await expect(browser.locator('#tabWarehouse')).toBeVisible();

  // 2. Test Live Cameras Dashboard (8 CCTV feeds)
  await browser.locator('#tabLiveCameras').click();
  await expect(browser.locator('#viewLiveCameras')).toBeVisible();
  await expect(browser.locator('#viewStudio')).toBeHidden();
  await expect(browser.locator('.camera-card').first()).toBeVisible();
  await app.screenshot('01-dashboard-live-cameras-matrix');

  // Test Camera Grid Mode Switcher (1-focus, 4-grid, 9-matrix)
  await browser.locator('#gridFocusBtn').click();
  await expect(browser.locator('#cameraGridContainer.grid-focus-1')).toBeVisible();
  await browser.locator('#grid4Btn').click();
  await expect(browser.locator('#cameraGridContainer.grid-quad-2x2')).toBeVisible();
  await browser.locator('#grid9Btn').click();
  await expect(browser.locator('#cameraGridContainer.grid-matrix-3x3')).toBeVisible();

  // Test Camera Filter (e.g. filter by warehouse)
  await browser.locator('#filterCamWH').click();
  await expect(browser.locator('.camera-card:has-text("Warehouse Gate 1")').first()).toBeVisible();
  await browser.locator('#filterCamAll').click();

  // 3. Test Workshop Sessions Summary & Shift Timeline
  await browser.locator('#tabSessions').click();
  await expect(browser.locator('#viewWorkshopSessions')).toBeVisible();
  await expect(browser.locator('#kpiTotalSessions')).toBeVisible();
  await expect(browser.locator('#kpiTotalWorkHours')).toBeVisible();
  await expect(browser.locator('#sessionsTableBody tr').first()).toBeVisible();
  await app.screenshot('02-dashboard-workshop-sessions');

  // Test Sessions Shift filter & search
  await browser.locator('#shiftFilterSelect').selectOption({ value: 'Pagi' });
  await browser.locator('#sessionsSearchInput').fill('Bay 1');
  await expect(browser.locator('#sessionsTableBody tr').first()).toBeVisible();
  await browser.locator('#sessionsSearchInput').fill('');
  await browser.locator('#shiftFilterSelect').selectOption({ value: 'all' });

  // 4. Test Warehouse Events & ERP Delivery Logs
  await browser.locator('#tabWarehouse').click();
  await expect(browser.locator('#viewWarehouseEvents')).toBeVisible();
  await expect(browser.locator('#kpiWarehouseEvents')).toBeVisible();
  await expect(browser.locator('#kpiErpDelivery')).toBeVisible();
  await expect(browser.locator('#warehouseTableBody tr').first()).toBeVisible();
  await app.screenshot('03-dashboard-warehouse-events');

  // Test Gate filter
  await browser.locator('#gateFilterSelect').selectOption({ value: 'WH-01' });
  await expect(browser.locator('#warehouseTableBody tr').first()).toBeVisible();
  await browser.locator('#gateFilterSelect').selectOption({ value: 'all' });

  // 5. Switch back to Workflow Studio
  await browser.locator('#tabStudio').click();
  await expect(browser.locator('#viewStudio')).toBeVisible();
  await expect(browser.locator('#viewLiveCameras')).toBeHidden();
  await app.screenshot('04-dashboard-back-to-studio');

  // 6. Agent visual & operational assertion
  await agent.assert('The topbar displays the navigation tabs (Workflow Studio, Live Cameras, Workshop Sessions, Warehouse Events) and the Workflow Studio canvas is actively displayed.');
});
