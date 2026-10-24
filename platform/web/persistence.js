// Adapted from rozenmad/love-web's EmscriptenPersistence.js.
// Report automatic writes too: IDBFS autoPersist otherwise discards their errors.
Module['preRun'] = Module['preRun'] || [];
Module['preRun'].push(function () {
  const directory = '/home/web_user/love';
  let loaded = false, writable = false, pending = 0;
  let tail = Promise.resolve();
  const report = (state, message) => {
    Module['saveStatus'] = {state, message: message || ''};
    Module['onSaveStatus']?.(Module['saveStatus']);
  };
  const originalSync = IDBFS.syncfs;
  IDBFS.syncfs = function (mount, populate, callback) {
    ++pending;
    if (!populate && loaded && writable) report('saving', 'Saving…');
    tail = tail.then(() => new Promise(resolve => {
      let settled = false;
      const done = error => {
        if (settled) return;
        settled = true;
        --pending;
        if (populate) {
          loaded = !error;
          if (error) report('unavailable', 'Saved data could not be loaded. Existing browser saves will not be overwritten. Export a backup before closing.');
          else if (!writable) report('unavailable', 'Another tab is using these saves. Changes in this tab will not be saved. Close it and reload, or export a backup.');
          else report('saved');
        } else if (loaded && writable) {
          if (error) report('error', 'Saving failed. Browser storage may be full or unavailable. Export a backup before closing.');
          else if (!pending) report('saved');
        }
        try { callback(error); } finally { resolve(); }
      };
      if (!populate && (!loaded || !writable)) {
        done(new Error('Persistent saves are unavailable in this tab.'));
        return;
      }
      try { originalSync.call(IDBFS, mount, populate, done); } catch (error) { done(error); }
    }));
  };
  const originalQueue = IDBFS.queuePersist;
  IDBFS.queuePersist = function (mount) {
    if (loaded && writable) report('saving', 'Saving…');
    originalQueue.call(IDBFS, mount);
  };
  Module['flushSaves'] = () => new Promise((resolve, reject) => {
    FS.syncfs(false, error => error ? reject(error) : resolve());
  });
  FS.mkdirTree(directory);
  FS.mount(IDBFS, {autoPersist: true}, directory);
  addRunDependency('love-saves');
  function load(canWrite) {
    writable = canWrite;
    FS.syncfs(true, () => removeRunDependency('love-saves'));
  }
  if (typeof navigator !== 'undefined' && navigator.locks) {
    // Hold the lock for this document's lifetime, including back/forward cache.
    // Loading a second tab is allowed, but its save store is read-only.
    navigator.locks.request('love-saves:' + directory, {ifAvailable: true}, lock => {
      load(!!lock);
      if (lock) return new Promise(() => {});
    }).catch(() => load(false));
  } else {
    // Saves remain usable on older hosts; concurrent-tab protection is unavailable.
    Module['saveLockUnavailable'] = true;
    load(true);
  }
});
