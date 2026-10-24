/* Portable backups of the browser save tree. Imports merge before game launch. */
(() => {
  'use strict';
  const root = '/home/web_user/love';
  const maxBytes = 32 * 1024 * 1024;
  function validate(backup) {
    if (backup?.format !== 'love-web-saves' || backup.version !== 1 || !Array.isArray(backup.files))
      throw new Error('This is not a LÖVE save backup.');
    if (backup.files.length > 10000) throw new Error('Too many files in backup.');
    const seen = new Set();
    let size = 0;
    return backup.files.map(file => {
      if (typeof file.path !== 'string' || !file.path || file.path.includes('\\') || file.path.includes('\0') ||
          file.path.split('/').some(part => !part || part === '.' || part === '..') || seen.has(file.path))
        throw new Error('Invalid or duplicate backup path.');
      seen.add(file.path);
      if (typeof file.data !== 'string' || file.data.length > maxBytes * 1.4) throw new Error('Invalid backup data.');
      const binary = atob(file.data);
      size += binary.length;
      if (size > maxBytes) throw new Error('Backup exceeds the 32 MiB limit.');
      return {path: file.path, bytes: Uint8Array.from(binary, c => c.charCodeAt(0))};
    });
  }
  window.loveSaveBackups = {
    export(FS) {
      const files = [];
      let size = 0;
      function walk(path) {
        for (const name of FS.readdir(path).sort()) {
          if (name === '.' || name === '..') continue;
          const full = path + '/' + name, mode = FS.lstat(full).mode;
          if (FS.isDir(mode)) walk(full);
          else if (FS.isFile(mode)) {
            const bytes = FS.readFile(full);
            size += bytes.length;
            if (size > maxBytes || files.length >= 10000) throw new Error('Save backup exceeds the export limit.');
            let binary = '';
            for (let i = 0; i < bytes.length; i += 8192) binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
            files.push({path: full.slice(root.length + 1), data: btoa(binary)});
          }
        }
      }
      walk(root);
      return JSON.stringify({format: 'love-web-saves', version: 1, files});
    },
    async import(runtime, text) {
      if (text.length > maxBytes * 1.5) throw new Error('Backup file is too large.');
      const files = validate(JSON.parse(text));
      // Reject file/directory conflicts and symlink traversal before any writes.
      const filePaths = new Set(files.map(file => file.path));
      for (const file of files) {
        const parts = file.path.split('/');
        for (let i = 1; i <= parts.length; ++i) {
          const relative = parts.slice(0, i).join('/'), full = root + '/' + relative;
          if (i < parts.length && filePaths.has(relative)) throw new Error('Conflicting backup paths.');
          let stat;
          try { stat = runtime.FS.lstat(full); } catch (error) {
            if (!runtime.FS.analyzePath(full).exists) continue;
            throw error;
          }
          if (i < parts.length ? !runtime.FS.isDir(stat.mode) : !runtime.FS.isFile(stat.mode))
            throw new Error('Backup conflicts with an existing save path.');
        }
      }
      for (const file of files) {
        const path = root + '/' + file.path;
        runtime.FS.mkdirTree(path.slice(0, path.lastIndexOf('/')));
        runtime.FS.writeFile(path, file.bytes);
      }
      await runtime.flushSaves();
    }
  };
})();
