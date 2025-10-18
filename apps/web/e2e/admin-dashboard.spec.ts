/**
 * E2E tests for admin dashboard functionality.
 */
import { test, expect } from '@playwright/test';

test.describe('Admin Login', () => {
  test('admin can login successfully', async ({ page }) => {
    await page.goto('/auth/login');
    
    // Fill login form
    await page.fill('input[name="email"]', 'admin@demo.com');
    await page.fill('input[name="password"]', 'demo123');
    
    // Submit
    await page.click('button[type="submit"]');
    
    // Should redirect to dashboard
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('text=Главная')).toBeVisible();
  });
  
  test('shows error on invalid credentials', async ({ page }) => {
    await page.goto('/auth/login');
    
    await page.fill('input[name="email"]', 'admin@demo.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=Неверный email или пароль')).toBeVisible();
  });
  
  test('rate limiting works after multiple failed attempts', async ({ page }) => {
    await page.goto('/auth/login');
    
    // Try 6 times with wrong password
    for (let i = 0; i < 6; i++) {
      await page.fill('input[name="email"]', 'admin@demo.com');
      await page.fill('input[name="password"]', 'wrong');
      await page.click('button[type="submit"]');
      await page.waitForTimeout(500);
    }
    
    // Should show rate limit error
    await expect(page.locator('text=Слишком много попыток')).toBeVisible();
  });
});

test.describe('Dashboard Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/auth/login');
    await page.fill('input[name="email"]', 'admin@demo.com');
    await page.fill('input[name="password"]', 'demo123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/.*dashboard/);
  });
  
  test('can navigate to all main sections', async ({ page }) => {
    // Navigate to Appointments
    await page.click('text=Записи');
    await expect(page).toHaveURL(/.*appointments/);
    
    // Navigate to Customers
    await page.click('text=Клиенты');
    await expect(page).toHaveURL(/.*customers/);
    
    // Navigate to Services
    await page.click('text=Услуги');
    await expect(page).toHaveURL(/.*services/);
    
    // Navigate to Reports
    await page.click('text=Отчеты');
    await expect(page).toHaveURL(/.*reports/);
  });
  
  test('sidebar collapses on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Sidebar should be hidden on mobile
    const sidebar = page.locator('[data-testid="sidebar"]');
    await expect(sidebar).not.toBeVisible();
    
    // Click hamburger to open
    await page.click('[data-testid="hamburger-menu"]');
    await expect(sidebar).toBeVisible();
    
    // Click outside to close
    await page.click('main');
    await expect(sidebar).not.toBeVisible();
  });
});

test.describe('Appointment Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
    await page.fill('input[name="email"]', 'admin@demo.com');
    await page.fill('input[name="password"]', 'demo123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/.*dashboard/);
  });
  
  test('can create new appointment', async ({ page }) => {
    await page.goto('/dashboard/appointments');
    
    // Click new appointment button
    await page.click('text=+ Новая запись');
    
    // Fill form
    await page.selectOption('select[name="customer"]', { index: 1 });
    await page.selectOption('select[name="service"]', { index: 1 });
    await page.selectOption('select[name="staff"]', { index: 1 });
    
    // Select tomorrow's date
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    await page.fill('input[name="date"]', tomorrow.toISOString().split('T')[0]);
    
    // Select time
    await page.fill('input[name="time"]', '14:00');
    
    // Submit
    await page.click('button:has-text("Создать")');
    
    // Should show success message
    await expect(page.locator('text=Запись создана')).toBeVisible();
  });
  
  test('can mark appointment as completed', async ({ page }) => {
    await page.goto('/dashboard/appointments');
    
    // Find first pending appointment
    const firstAppointment = page.locator('[data-status="PENDING"]').first();
    
    // Click actions menu
    await firstAppointment.locator('[data-testid="actions-menu"]').click();
    
    // Click complete
    await page.click('text=Завершить');
    
    // Confirm
    await page.click('button:has-text("Подтвердить")');
    
    // Status should change
    await expect(firstAppointment).toHaveAttribute('data-status', 'COMPLETED');
  });
  
  test('can mark payment as cash paid', async ({ page }) => {
    await page.goto('/dashboard/appointments');
    
    // Find completed appointment without payment
    const appointment = page.locator('[data-status="COMPLETED"]').first();
    await appointment.locator('[data-testid="mark-paid"]').click();
    
    // Fill amount
    await page.fill('input[name="amount"]', '1000');
    
    // Submit
    await page.click('button:has-text("Оплачено")');
    
    // Should show success
    await expect(page.locator('text=Оплата зафиксирована')).toBeVisible();
  });
});

test.describe('Reports', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
    await page.fill('input[name="email"]', 'admin@demo.com');
    await page.fill('input[name="password"]', 'demo123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/.*dashboard/);
  });
  
  test('can view revenue report', async ({ page }) => {
    await page.goto('/dashboard/reports');
    
    // Select date range
    await page.fill('input[name="from"]', '2025-10-01');
    await page.fill('input[name="to"]', '2025-10-12');
    
    // Submit
    await page.click('button:has-text("Показать")');
    
    // Should display results
    await expect(page.locator('text=Общая выручка')).toBeVisible();
    await expect(page.locator('[data-testid="total-revenue"]')).toBeVisible();
  });
  
  test('can export CSV', async ({ page }) => {
    await page.goto('/dashboard/reports');
    
    // Click export button
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('text=📥 Экспорт CSV')
    ]);
    
    // Verify download
    expect(download.suggestedFilename()).toMatch(/appointments_.*\.csv/);
  });
});

