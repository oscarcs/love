const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const playwright = require('playwright');
(async () => {
  const browser = await playwright[process.env.BROWSER || 'chromium'].launch({headless: !process.env.HEADED,
    ...((process.env.BROWSER_PATH || process.env.CHROMIUM_PATH) ? {executablePath: process.env.BROWSER_PATH || process.env.CHROMIUM_PATH} : {})});
  const url = process.argv[2] || 'http://127.0.0.1:8124';
  const errors = [];
  function observe(page) {
    page.on('pageerror', error => errors.push(error.stack));
    page.on('dialog', dialog => dialog.accept());
    return page;
  }
  async function ready(page) {
    await page.goto(url);
    await page.getByRole('button', {name: 'Play', exact: true}).waitFor();
  }
  async function play(page) {
    const finished = page.waitForEvent('console', {predicate: message => message.text() === 'LOVE_WEB_SMOKE_OK'});
    await page.getByRole('button', {name: 'Play', exact: true}).click();
    await finished;
  }
  try {
    const context = await browser.newContext();
    let page = observe(await context.newPage());
    await ready(page); await play(page);
    // No manual flush: prove automatic persistence completes and survives reload.
    await page.waitForFunction(() => loveRuntime.saveStatus.state === 'saved');
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', {name: 'Export saves', exact: true}).click();
    const download = await downloadPromise;
    const backup = await fs.readFile(await download.path(), 'utf8');
    assert.equal(JSON.parse(backup).files.find(file => file.path === 'love-web-smoke/counter.txt').data, 'MQ==');
    const second = observe(await context.newPage());
    await ready(second);
    assert.match(await second.locator('#save-status').innerText(), /Another tab/);
    await second.evaluate(() => {
      loveRuntime.FS.writeFile('/home/web_user/love/love-web-smoke/counter.txt', '99');
    });
    await second.waitForTimeout(200);
    assert.equal(await second.evaluate(() => loveRuntime.saveStatus.state), 'unavailable');
    await second.close();
    await page.close();
    page = observe(await context.newPage());
    await ready(page);
    assert.equal(await page.evaluate(() => loveRuntime.FS.readFile('/home/web_user/love/love-web-smoke/counter.txt', {encoding: 'utf8'})), '1');
    // Validate the entire backup before applying any entries.
    const bad = JSON.stringify({format: 'love-web-saves', version: 1, files: [
      {path: 'love-web-smoke/counter.txt', data: 'OTk='}, {path: '../escape', data: 'eA=='}]});
    await page.locator('#import-saves').setInputFiles({name: 'bad.json', mimeType: 'application/json', buffer: Buffer.from(bad)});
    await page.waitForFunction(() => document.querySelector('#backup-status').textContent.startsWith('Import failed:'));
    assert.equal(await page.evaluate(() => loveRuntime.FS.readFile('/home/web_user/love/love-web-smoke/counter.txt', {encoding: 'utf8'})), '1');
    await page.locator('#import-saves').setInputFiles({name: 'saves.json', mimeType: 'application/json', buffer: Buffer.from(backup)});
    await page.waitForFunction(() => document.querySelector('#backup-status').textContent.startsWith('Backup imported.'));
    await play(page);
    await page.waitForFunction(() => loveRuntime.saveStatus.state === 'saved');
    assert.equal(await page.evaluate(() => loveRuntime.FS.readFile('/home/web_user/love/love-web-smoke/counter.txt', {encoding: 'utf8'})), '2');
    await page.close();
    // A read failure must not lead to overwriting the existing persistent tree.
    page = observe(await context.newPage());
    await page.addInitScript(() => { IDBFactory.prototype.open = () => { throw new DOMException('Blocked', 'SecurityError'); }; });
    await ready(page); await play(page);
    assert.match(await page.locator('#save-status').innerText(), /could not be loaded/);
    await page.close();
    page = observe(await context.newPage());
    await ready(page);
    assert.equal(await page.evaluate(() => loveRuntime.FS.readFile('/home/web_user/love/love-web-smoke/counter.txt', {encoding: 'utf8'})), '2');
    // Simulate quota exhaustion during an automatic write, then retry after recovery.
    await page.evaluate(() => {
      window.originalPut = IDBObjectStore.prototype.put;
      IDBObjectStore.prototype.put = () => { throw new DOMException('Full', 'QuotaExceededError'); };
      loveRuntime.FS.writeFile('/home/web_user/love/love-web-smoke/quota.txt', 'backup me');
    });
    await page.waitForFunction(() => loveRuntime.saveStatus.state === 'error');
    assert.match(await page.locator('#save-status').innerText(), /Saving failed/);
    assert(await page.evaluate(() => loveSaveBackups.export(loveRuntime.FS).includes('quota.txt')));
    await page.evaluate(async () => {
      IDBObjectStore.prototype.put = window.originalPut;
      await loveRuntime.flushSaves();
    });
    assert.equal(await page.evaluate(() => loveRuntime.saveStatus.state), 'saved');
    assert.deepEqual(errors, []);
    await context.close();
    console.log('Storage checks passed: auto-save, reload, cross-tab lock, backups, traversal rejection, blocked storage and quota recovery');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
