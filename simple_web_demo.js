// Simple Playwright demo
const { chromium } = require('playwright');

(async () => {
  console.log('🌐 Starting Playwright demo...');

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  try {
    // Navigate to a simple page
    console.log('📍 Navigating to example.com...');
    await page.goto('https://example.com', { timeout: 10000 });

    // Take screenshot
    await page.screenshot({ path: 'screenshots/example.png' });
    console.log('📸 Screenshot saved to screenshots/example.png');

    // Get page info
    const title = await page.title();
    const url = page.url();

    console.log(`📄 Title: ${title}`);
    console.log(`🔗 URL: ${url}`);

    // Extract text content
    const h1 = await page.textContent('h1');
    console.log(`📝 Main heading: ${h1}`);

    console.log('✅ Playwright demo successful!');

  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
  } finally {
    await browser.close();
  }
})();
