/* Browser host for the LÖVE runtime. Keep engine details out of the game. */
(() => {
  'use strict';
  const status = document.getElementById('status');
  const start = document.getElementById('start');
  const reload = document.getElementById('reload');
  const canvas = document.getElementById('canvas');
  const resumeAudio = document.getElementById('resume-audio');
  resumeAudio.onclick = () => runtime?._love_web_set_hidden(0);
  const saveStatus = document.getElementById('save-status');
  const backupStatus = document.getElementById('backup-status');
  const importer = document.getElementById('import-saves');
  let runtime, assets, stopped = false, started = false, suspended = false;
  const asset = name => name + "?v=" + assets[name].sha256;
  const lockWarning = 'Use one game tab at a time: this browser cannot lock saves across tabs.';
  const showSaveStatus = value => { saveStatus.textContent = value.message || (runtime?.saveLockUnavailable ? lockWarning : ''); };
  function setHidden(hidden) {
    if (!started || stopped || suspended === hidden) return;
    suspended = hidden;
    runtime._love_web_set_hidden(hidden ? 1 : 0);
    if (hidden) runtime.pauseMainLoop();
    else runtime.resumeMainLoop();
  }
  document.addEventListener('visibilitychange', () => setHidden(document.hidden));
  window.addEventListener('pagehide', () => setHidden(true));
  window.addEventListener('pageshow', () => setHidden(document.hidden));
  window.addEventListener('beforeunload', event => {
    if (['saving', 'error'].includes(runtime?.saveStatus?.state)) { event.preventDefault(); event.returnValue = ''; }
  });
  const fail = error => {
    stopped = true;
    resumeAudio.hidden = true;
    runtime?._love_web_set_hidden?.(1);
    runtime?.pauseMainLoop?.();
    status.textContent = String(error.message || error);
    start.hidden = true;
    reload.hidden = false;
  };
  reload.onclick = () => location.reload();
  canvas.addEventListener('webglcontextlost', event => {
    // LÖVE resources cannot currently be reconstructed after WebGL context loss.
    // Stop rendering and provide an explicit recovery path instead of a frozen canvas.
    event.preventDefault();
    fail(new Error('Graphics were interrupted. Reload to continue from your last save.'));
  });
  function loadRuntime() {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = asset('love.js');
      script.onload = resolve;
      script.onerror = () => reject(new Error('Could not load the game engine. Check your connection and reload.'));
      document.head.appendChild(script);
    });
  }
  async function downloadGame() {
    const response = await fetch(asset('game.love'));
    if (!response.ok) throw new Error('Could not download the game (HTTP ' + response.status + ').');
    if (!response.body) return new Uint8Array(await response.arrayBuffer());
    const reader = response.body.getReader(), chunks = [];
    let size = 0;
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      chunks.push(value);
      size += value.length;
      status.textContent = 'Downloading game… ' + Math.ceil(size / 1024) + ' KiB';
    }
    const result = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) { result.set(chunk, offset); offset += chunk.length; }
    return result;
  }
  async function boot() {
    if (typeof WebAssembly !== 'object') throw new Error('This browser does not support WebAssembly. Try an updated desktop browser.');
    const probe = document.createElement('canvas').getContext('webgl2');
    if (!probe) throw new Error('WebGL 2 is unavailable. Check browser graphics settings or try another browser.');
    probe.getExtension('WEBGL_lose_context')?.loseContext();
    status.textContent = 'Loading game engine…';
    const metadata = await fetch('manifest.json', {cache: 'no-store'});
    if (!metadata.ok) throw new Error('Could not load the game manifest (HTTP ' + metadata.status + ').');
    const manifest = await metadata.json();
    assets = manifest.assets;
    if (manifest.version !== 1 || !assets || ['love.js', 'love.wasm', 'game.love'].some(name => !/^[a-f0-9]{64}$/.test(assets[name]?.sha256)))
      throw new Error('The game package manifest is invalid. Rebuild or redeploy the complete package.');
    await loadRuntime();
    const bytes = await downloadGame();
    status.textContent = 'Starting game engine…';
    runtime = await Love({canvas, locateFile: path => asset(path), print: console.log, printErr: console.error, onAbort: fail, onSaveStatus: showSaveStatus,
      onAudioResumeError: () => { if (!stopped && !document.hidden) resumeAudio.hidden = false; },
      onAudioResumed: () => { resumeAudio.hidden = true; },
      onLoveQuit: code => {
        stopped = true;
        resumeAudio.hidden = true;
        status.textContent = code === 0 ? 'Game closed.' : 'The game exited with an error (' + code + ').';
        reload.hidden = false;
        window.dispatchEvent(new CustomEvent('lovequit', {detail: code}));
      }});
    window.loveRuntime = runtime;
    document.getElementById('save-tools').hidden = false;
    if (runtime.saveLockUnavailable) saveStatus.textContent = lockWarning;
    document.getElementById('export-saves').onclick = () => {
      try {
        const url = URL.createObjectURL(new Blob([loveSaveBackups.export(runtime.FS)], {type: 'application/json'}));
        const link = document.createElement('a');
        link.href = url; link.download = 'love-saves.json'; link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      } catch (error) { backupStatus.textContent = 'Export failed: ' + error.message; }
    };
    importer.onchange = async () => {
      const file = importer.files[0];
      if (!file) return;
      importer.disabled = true;
      start.disabled = true;
      try {
        if (file.size > 48 * 1024 * 1024) throw new Error('Backup file is too large.');
        if (runtime.saveStatus.state === 'unavailable') throw new Error('Storage is unavailable. Resolve the save warning and reload first.');
        await loveSaveBackups.import(runtime, await file.text());
        backupStatus.textContent = 'Backup imported. Matching save files were replaced; other files were kept.';
      } catch (error) { backupStatus.textContent = 'Import failed: ' + error.message; }
      finally { importer.disabled = false; start.disabled = false; importer.value = ''; }
    };
    if (stopped) return;
    runtime.FS.writeFile('/game.love', bytes);
    status.textContent = '';
    start.disabled = false;
    start.textContent = 'Play';
    start.onclick = () => {
      start.hidden = true;
      importer.disabled = true;
      canvas.focus();
      try {
        runtime.callMain(['/game.love']);
        started = true;
        setHidden(document.hidden);
      } catch (error) { fail(error); }
    };
  }
  boot().catch(fail);
})();
