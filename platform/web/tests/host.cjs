// Failure paths are deliberately injected; no external sites or user profiles.
const assert = require('node:assert/strict');
const playwright = require('playwright');
(async () => {
  const browser = await playwright[process.env.BROWSER || 'chromium'].launch({
    headless: !process.env.HEADED,
    ...((process.env.BROWSER_PATH || process.env.CHROMIUM_PATH) ? {executablePath: process.env.BROWSER_PATH || process.env.CHROMIUM_PATH} : {})});
  const url = process.argv[2] || 'http://127.0.0.1:8124';
  try {
    for (const scenario of ['wasm', 'webgl', 'engine', 'game']) {
      const page = await browser.newPage();
      if (scenario === 'wasm') await page.addInitScript(() => { window.WebAssembly = undefined; });
      if (scenario === 'webgl') await page.addInitScript(() => {
        const original = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, ...args) {
          return type === 'webgl2' ? null : original.call(this, type, ...args);
        };
      });
      if (scenario === 'engine') await page.route('**/love.js', route => route.abort());
      if (scenario === 'game') await page.route('**/game.love', route => route.fulfill({status: 503, body: 'Unavailable'}));
      await page.goto(url);
      await page.getByRole('button', {name: 'Reload', exact: true}).waitFor();
      const message = await page.locator('#status').innerText();
      assert.match(message, {wasm: /WebAssembly/, webgl: /WebGL 2/, engine: /load the game engine/, game: /HTTP 503/}[scenario]);
      await page.close();
    }
    const page = await browser.newPage();
    const errors = [], messages = [];
    page.on('pageerror', error => errors.push(error.stack));
    page.on('console', message => messages.push(message.text()));
    await page.goto(url);
    await page.getByRole('button', {name: 'Play', exact: true}).click();
    await page.waitForFunction(() => window.loveRuntime && document.querySelector('#start').hidden);
    const deadline = Date.now() + 30000;
    while (!messages.includes('LOVE_WEB_SMOKE_OK')) {
      if (errors.length || Date.now() > deadline) throw new Error(errors.join('\n') || messages.join('\n'));
      await page.waitForTimeout(100);
    }
    await page.evaluate(() => {
      const gl = document.querySelector('canvas').getContext('webgl2');
      const extension = gl.getExtension('WEBGL_lose_context');
      if (!extension) throw new Error('Context-loss injection is unavailable');
      extension.loseContext();
    });
    await page.getByRole('button', {name: 'Reload', exact: true}).waitFor();
    assert.match(await page.locator('#status').innerText(), /Graphics were interrupted/);
    await page.getByRole('button', {name: 'Reload', exact: true}).click();
    await page.getByRole('button', {name: 'Play', exact: true}).waitFor();
    assert.deepEqual(errors, []);
    console.log('Host checks passed: unsupported browser, download failures, context loss and reload');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
