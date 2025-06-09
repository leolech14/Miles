// Playwright web automation demonstration
const { test, expect } = require('@playwright/test');

test('Miles bot web automation demo', async ({ page }) => {
  console.log('🌐 Starting web automation demo...');

  // Navigate to a mileage website (example)
  await page.goto('https://www.melhoresdestinos.com.br');

  // Take a screenshot
  await page.screenshot({
    path: 'screenshots/melhores-destinos.png',
    fullPage: false
  });

  console.log('📸 Screenshot saved to screenshots/melhores-destinos.png');

  // Get page title
  const title = await page.title();
  console.log(`📄 Page title: ${title}`);

  // Extract some text content
  const content = await page.textContent('body');
  const hasPromo = content.toLowerCase().includes('promo') ||
                   content.toLowerCase().includes('bônus') ||
                   content.toLowerCase().includes('transferência');

  console.log(`🎯 Promotion keywords found: ${hasPromo ? 'YES' : 'NO'}`);

  console.log('✅ Web automation demo complete!');
});
