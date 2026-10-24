const assert = require('node:assert/strict');
const playwright = require('playwright');
(async () => {
  const browser = await playwright[process.env.BROWSER || 'chromium'].launch({headless: !process.env.HEADED,
    ...((process.env.BROWSER_PATH || process.env.CHROMIUM_PATH) ? {executablePath: process.env.BROWSER_PATH || process.env.CHROMIUM_PATH} : {})});
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.stack));
    await page.addInitScript(() => {
      window.testAudioContexts = [];
      const Original = window.AudioContext || window.webkitAudioContext;
      class ObservedAudioContext extends Original {
        constructor(...args) { super(...args); window.testAudioContexts.push(this); }
      }
      window.AudioContext = ObservedAudioContext;
      if (window.webkitAudioContext) window.webkitAudioContext = ObservedAudioContext;
      window.testDraws = 0;
      const draw = WebGL2RenderingContext.prototype.drawElements;
      WebGL2RenderingContext.prototype.drawElements = function(...args) {
        ++window.testDraws;
        return draw.apply(this, args);
      };
    });
    await page.goto(process.argv[2] || 'http://127.0.0.1:8124');
    const initialized = page.waitForEvent('console', {predicate: message => message.text() === 'LOVE_WEB_SMOKE_OK'});
    await page.getByRole('button', {name: 'Play', exact: true}).click();
    await initialized;
    try {
      await page.waitForFunction(() => testAudioContexts.some(context => context.state === 'running'));
    } catch (error) {
      console.error('Audio startup state:', await page.evaluate(() => ({
        contexts: testAudioContexts.map(context => ({state: context.state, sampleRate: context.sampleRate})),
        status: document.querySelector('#status').textContent,
        resumeAudioVisible: !document.querySelector('#resume-audio').hidden,
      })));
      throw error;
    }
    await page.waitForFunction(() => testAudioContexts.filter(context => context.state !== 'closed').length === 1);
    assert(await page.evaluate(() => testAudioContexts.length >= 2), 'Restart did not create a replacement audio context');
    // Inject lifecycle events deterministically. This tests our handling, not OS suspension.
    for (const kind of ['visibility', 'page-cache']) {
      const draws = await page.evaluate(kind => {
        if (kind === 'visibility') {
          Object.defineProperty(document, 'hidden', {configurable: true, value: true});
          document.dispatchEvent(new Event('visibilitychange'));
        } else window.dispatchEvent(new PageTransitionEvent('pagehide', {persisted: true}));
        loveRuntime.FS.writeFile('/home/web_user/love/love-web-smoke/resume-check', '1');
        return window.testDraws;
      }, kind);
      await page.waitForFunction(() => testAudioContexts.filter(context => context.state !== 'closed').every(context => context.state === 'suspended'));
      await page.waitForTimeout(600);
      assert.equal(await page.evaluate(() => window.testDraws), draws, 'Rendering continued while suspended');
      const resumed = page.waitForEvent('console', {predicate: message => message.text() === 'LOVE_WEB_RESUME_OK'});
      await page.evaluate(kind => {
        if (kind === 'visibility') {
          Object.defineProperty(document, 'hidden', {configurable: true, value: false});
          document.dispatchEvent(new Event('visibilitychange'));
        } else window.dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}));
      }, kind);
      await resumed;
      await page.waitForFunction(() => testAudioContexts.some(context => context.state === 'running'));
      assert(await page.evaluate(previous => window.testDraws > previous, draws));
    }
    await page.evaluate(() => {
      loveRuntime._love_web_set_hidden(1);
      window.liveAudio = testAudioContexts.find(context => context.state !== 'closed');
      window.realResume = liveAudio.resume;
      liveAudio.resume = () => Promise.reject(new DOMException('Gesture required', 'NotAllowedError'));
      loveRuntime._love_web_set_hidden(0);
    });
    await page.getByRole('button', {name: 'Resume audio', exact: true}).waitFor();
    await page.evaluate(() => { liveAudio.resume = window.realResume; });
    await page.getByRole('button', {name: 'Resume audio', exact: true}).click();
    await page.waitForFunction(() => document.querySelector('#resume-audio').hidden && liveAudio.state === 'running');
    await page.locator('canvas').click();
    await page.keyboard.press('q');
    await page.waitForFunction(() => testAudioContexts.every(context => context.state === 'closed'));
    assert.deepEqual(errors, []);
    console.log('Lifecycle checks passed: suspend rendering/audio, resume without background delta, page-cache events, audio gesture recovery and context teardown');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
