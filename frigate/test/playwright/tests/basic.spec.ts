import { test, expect } from '@playwright/test';

test('basic', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('.grid')).toBeVisible();
  await page.getByRole('link', { name: 'Birdseye' }).click();
  await expect(page.locator('#video')).toBeVisible();
  await page.getByRole('link', { name: 'Events' }).click();
  await expect(page.getByRole('heading', { name: 'Past Events' })).toBeVisible();
  await page.getByRole('link', { name: 'Storage' }).click();
  await page.getByRole('cell', { name: 'Recordings & Snapshots' }).click();
  await expect(page.getByRole('cell', { name: 'Recordings & Snapshots' })).toBeVisible();
  await page.getByRole('link', { name: 'System' }).click();
  await expect(page.locator('div').filter({ hasText: /^P-IDInference SpeedCPU %Memory/ })).toBeVisible();
  await page.getByRole('link', { name: 'Config' }).click();
  await expect(page.locator('canvas').nth(2)).toBeVisible();
  await page.getByRole('link', { name: 'Logs' }).click();
  await expect(page.getByRole('button', { name: 'Frigate' })).toBeVisible();
  await page.getByLabel('More options').click();
  await expect(page.getByRole('option', { name: 'Restart Frigate' })).toBeVisible();
});