# Shipping a browser build

Build with the pinned Emscripten SDK and `LOVE_WEB_PROFILING=OFF` for release.
From the source checkout:

```sh
python3 platform/web/release.py --runtime build/web --output dist/love-web-runtime.zip
python3 platform/web/package.py /path/to/game dist/game --compress --archive dist/game.zip
python3 platform/web/serve.py dist/game --port 8123
```

The runtime ZIP contains the engine, license notices, player and packaging tools.
It does not contain a game. After extracting it into a separate directory:

```sh
python3 package.py /path/to/game /path/to/output --runtime . --compress --archive /path/to/game.zip
python3 serve.py /path/to/output
```

Game-directory packaging normalizes archive ordering, timestamps and permissions.
Given identical input bytes and the same Python/zlib toolchain, the generated game
archive, deployment ZIP, manifests and gzip sidecars are reproducible. This does
not claim that independently compiled Emscripten runtime binaries are identical.
Supplied `.love` archives are preserved byte-for-byte. SHA-256 manifests identify
all original packaged files; the runtime release can record a CI source revision.
Generated archives contain only managed package files, not arbitrary output files.

## HTTP hosting

Deploy the complete game directory together. The Python server is a local preview
and reference for headers, not a production service. Use an HTTPS static host/CDN
for deployment. No COOP/COEP isolation headers are needed by this single-threaded
build. Preserve license notices in the deployment.

- Serve `.wasm` as `Content-Type: application/wasm`.
- If serving a precompressed `.gz` sidecar in response to its original URL, send
  `Content-Encoding: gzip`, the original asset's content type, and
  `Vary: Accept-Encoding`. Do not send gzip bytes without the encoding header.
- The gzip files are optional. Hosts without sidecar negotiation can serve the
  original files, or compress them themselves. Do not double-compress responses.
- Revalidate `index.html` and `manifest.json` (`Cache-Control: no-cache`). The
  player explicitly bypasses cached manifest responses. Scripts, game and Wasm
  URLs include content hashes in their query strings. The CDN must retain query
  strings in its cache key. The conservative default is revalidation for all
  files, as used by `serve.py`.
- For long immutable caching, deploy each release into a new versioned directory
  and retain older releases. Do not overwrite files behind an immutable URL.
- Upload to a new deployment and switch it atomically; clients should never see
  half of a release. Test the deployed URL, including compressed Wasm loading,
  saves, reload and quit, before distributing it.

Storage belongs to the exact origin (scheme, hostname and port) and LÖVE game
identity, not the deployment folder. A domain or identity change needs explicit
save migration; players can use Export/Import saves. Two games on the same origin
currently share the save-tree lock, so only one tab can persist at a time.

## CI artifacts and validation

The Web workflow builds the engine, runs Python packaging/HTTP tests and browser
rendering, host-failure and storage tests in Chromium, Firefox and WebKit, then
uploads `love-web-runtime.zip` and `love-web-smoke.zip` as workflow artifacts.
These are testable build artifacts, not an automatically published public release.
WebKit coverage does not replace checking the shipping Safari application.
