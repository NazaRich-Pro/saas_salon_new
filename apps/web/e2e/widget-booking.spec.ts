/**
 * E2E tests for public widget booking flow.
 * This is a critical user journey that must work flawlessly.
 */
import { test, expect } from '@playwright/test';

test.describe('Widget Booking Flow', () => {
  test('complete booking flow from widget', async ({ page }) => {
    // Go to demo tenant page with widget
    await page.goto('/demo');
    
    // Wait for widget to load
    await page.waitForSelector('#booking-widget');
    
    // Step 1: Select service
    await page.click('text=Женская стрижка');
    await expect(page.locator('text=1000 сом')).toBeVisible();
    
    // Step 2: Select staff
    await page.click('text=Анна Иванова');
    
    // Step 3: Select date
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowStr = tomorrow.toLocaleDateString('ru-RU');
    
    await page.click(`text=${tomorrowStr}`);
    
    // Step 4: Select time slot
    await page.click('button:has-text("10:00")');
    
    // Step 5: Fill customer details
    await page.fill('input[name="name"]', 'Тестовый Клиент');
    await page.fill('input[name="phone"]', '+996700111111');
    await page.fill('input[name="email"]', 'test@example.com');
    
    // Step 6: Submit booking
    await page.click('button:has-text("Забронировать")');
    
    // Wait for confirmation
    await expect(page.locator('text=Запись успешно создана')).toBeVisible({
      timeout: 10000
    });
    
    // Verify confirmation email was sent (check UI message)
    await expect(page.locator('text=Подтверждение отправлено на почту')).toBeVisible();
  });
  
  test('widget shows correct available slots', async ({ page }) => {
    await page.goto('/demo');
    await page.waitForSelector('#booking-widget');
    
    // Select service and staff
    await page.click('text=Женская стрижка');
    await page.click('text=Анна Иванова');
    
    // Select tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowStr = tomorrow.toLocaleDateString('ru-RU');
    await page.click(`text=${tomorrowStr}`);
    
    // Check that slots are shown
    const slots = await page.locator('button:has-text(":")').count();
    expect(slots).toBeGreaterThan(0);
    
    // Verify slots are in working hours (9 AM - 6 PM)
    const firstSlot = await page.locator('button:has-text(":")').first().textContent();
    expect(firstSlot).toMatch(/^(09|10|11|12|13|14|15|16|17|18):/);
  });
  
  test('widget validation works', async ({ page }) => {
    await page.goto('/demo');
    await page.waitForSelector('#booking-widget');
    
    // Try to submit without filling required fields
    await page.click('button:has-text("Забронировать")');
    
    // Check for validation errors
    await expect(page.locator('text=Выберите услугу')).toBeVisible();
  });
  
  test('widget supports multiple languages', async ({ page }) => {
    await page.goto('/demo?lang=en');
    await page.waitForSelector('#booking-widget');
    
    // Verify English text
    await expect(page.locator('text=Select Service')).toBeVisible();
    
    // Switch to Kyrgyz
    await page.click('text=🇰🇬');
    await expect(page.locator('text=Кызматты тандаңыз')).toBeVisible();
    
    // Switch to Russian
    await page.click('text=🇷🇺');
    await expect(page.locator('text=Выберите услугу')).toBeVisible();
  });
});

test.describe('Widget Error Handling', () => {
  test('shows error when slot is already booked', async ({ page, context }) => {
    // Open two tabs to simulate race condition
    const page1 = page;
    const page2 = await context.newPage();
    
    // Both select same slot
    await Promise.all([
      page1.goto('/demo'),
      page2.goto('/demo')
    ]);
    
    await Promise.all([
      page1.waitForSelector('#booking-widget'),
      page2.waitForSelector('#booking-widget')
    ]);
    
    // Select same service, staff, date, time on both
    const selectSlot = async (p: any) => {
      await p.click('text=Женская стрижка');
      await p.click('text=Анна Иванова');
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      await p.click(`text=${tomorrow.toLocaleDateString('ru-RU')}`);
      await p.click('button:has-text("10:00")');
      await p.fill('input[name="name"]', 'Test');
      await p.fill('input[name="phone"]', '+996700111111');
    };
    
    await Promise.all([
      selectSlot(page1),
      selectSlot(page2)
    ]);
    
    // Submit both (one should fail)
    await page1.click('button:has-text("Забронировать")');
    await page2.click('button:has-text("Забронировать")');
    
    // One should show error
    const hasError = await Promise.race([
      page1.locator('text=Слот уже занят').isVisible(),
      page2.locator('text=Слот уже занят').isVisible()
    ]);
    
    expect(hasError).toBeTruthy();
  });
});

