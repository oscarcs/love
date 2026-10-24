// Adapted from rozenmad/love-web's EmscriptenPersistence.js.
// Load saves before Lua starts; persist writes during play, not just page unload.
Module['preRun'] = Module['preRun'] || [];
Module['preRun'].push(function () {
  const directory = '/home/web_user/love';
  FS.mkdirTree(directory);
  FS.mount(IDBFS, {autoPersist: true}, directory);
  addRunDependency('love-saves');
  FS.syncfs(true, function (error) {
    if (error) {
      console.warn('Could not load persistent saves; saves may only last this session.', error);
    }
    removeRunDependency('love-saves');
  });
});
