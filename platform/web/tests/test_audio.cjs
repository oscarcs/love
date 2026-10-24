const assert = require('node:assert/strict');
const {test} = require('node:test');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

function fixture() {
  let library, errors = 0;
  const element = new EventTarget();
  const ctx = new EventTarget();
  ctx.state = 'suspended';
  ctx.calls = 0;
  ctx.resume = async () => { ctx.calls++; ctx.state = 'running'; };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../audio.js'), 'utf8'), {
    addToLibrary: value => { library = value; },
    Module: {onAudioResumeError: () => { errors++; }},
  });
  library.$autoResumeAudioContext(ctx, [element]);
  return {ctx, gesture: () => element.dispatchEvent(new Event('mousedown')), errors: () => errors};
}

test('closing a suspended context removes gesture handlers before its state changes', () => {
  const {ctx, gesture} = fixture();
  ctx.loveDisposeAutoResume();
  gesture();
  assert.equal(ctx.calls, 0);
});

test('a rejected resume can be retried; successful resume removes handlers', async () => {
  const {ctx, gesture, errors} = fixture();
  const resume = ctx.resume;
  ctx.resume = () => Promise.reject(new Error('Gesture required'));
  gesture();
  await new Promise(setImmediate);
  assert.equal(errors(), 1);
  ctx.resume = resume;
  gesture();
  await new Promise(setImmediate);
  assert.equal(ctx.calls, 1);
  ctx.state = 'suspended';
  gesture();
  assert.equal(ctx.calls, 1);
});

test('a resume rejected during teardown is handled without reporting a live audio error', async () => {
  const {ctx, gesture, errors} = fixture();
  let reject;
  ctx.resume = () => new Promise((resolve, fail) => { reject = fail; });
  gesture();
  ctx.loveDisposeAutoResume();
  reject(new Error('Context closed'));
  await new Promise(setImmediate);
  assert.equal(errors(), 0);
});
