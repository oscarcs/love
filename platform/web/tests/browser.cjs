// npm install --no-save playwright; node platform/web/tests/browser.cjs URL
const assert = require('node:assert/strict');
const playwright = require('playwright');
(async () => {
  const browserType = process.env.BROWSER || 'chromium';
  const executablePath = process.env.BROWSER_PATH || process.env.CHROMIUM_PATH;
  const browser = await playwright[browserType].launch({headless: !process.env.HEADED,
    ...(executablePath ? {executablePath} : {})});
  try {
    const page = await browser.newPage();
    const messages = [], errors = [];
    page.on('console', message => { messages.push(message.text()); console.log(message.text()); });
    page.on('pageerror', error => errors.push(String(error)));
    for (let count = 1; count <= 2; count++) {
      messages.length = 0;
      await page.goto(process.argv[2] || 'http://127.0.0.1:8124');
      await page.getByRole('button', {name: 'Play', exact: true}).click();
      await expectMessage('LOVE_WEB_SMOKE_OK');
      assert(messages.includes('LOVE_WEB_SAVE_COUNT=' + count), 'Save did not survive page reload');
      assert.equal(await page.locator('#status').innerText(), '');
      await page.evaluate(() => new Promise((resolve, reject) =>
        loveRuntime.FS.syncfs(false, error => error ? reject(error) : resolve())));
    }
    await page.keyboard.press('r');
    await expectMessage('LOVE_WEB_RESIZE_OK');
    if (process.env.SMOKE_SCREENSHOT) await page.screenshot({path: process.env.SMOKE_SCREENSHOT});
    await page.evaluate(() => window.addEventListener('lovequit', event => { window.quitCode = event.detail; }));
    await page.keyboard.press('q');
    await page.waitForFunction(() => window.quitCode === 0);
    assert.equal(await page.locator('#status').innerText(), 'Game closed.');
    assert(await page.getByRole('button', {name: 'Reload', exact: true}).isVisible());
    assert.deepEqual(errors, []);
    assert(!messages.some(m => /Error:|INVALID_ENUM|INVALID_OPERATION/.test(m)), 'Runtime/GL error');
    console.log('Browser smoke passed: pacing, draw, shader, font, buffer/texture readback, audio, restart, save reload, quit');
    async function expectMessage(text) {
      const deadline = Date.now() + 30000;
      while (!messages.includes(text)) {
        if (errors.length) throw new Error(errors.join('\n'));
        if (Date.now() > deadline) throw new Error('Timed out waiting for ' + text + '\n' + messages.join('\n'));
        await page.waitForTimeout(100);
      }
    }
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
