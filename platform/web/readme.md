# WebGL 2 / WebAssembly

Experimental, single-threaded browser target built from this checkout. Requires
WebGL 2 and JavaScript/WebAssembly; no cross-origin isolation headers are needed.

## Build

Install and activate Emscripten **4.0.10** with emsdk, then in the repository root:

```sh
source /path/to/emsdk/emsdk_env.sh
cmake --preset web
cmake --build --preset web
```

The SDK must be active (`EMSDK` set) when configuring. CMake and Python 3.9+ are
also required. Dependencies are downloaded with the same checksums as native
builds. The web target uses plain Lua 5.1, static SDL3, and Emscripten's OpenAL
implementation. Output: `build/web/love.js` and `build/web/love.wasm`.

## Package and play

```sh
python3 platform/web/package.py /path/to/game build/web-game
python3 -m http.server 8123 --bind 127.0.0.1 --directory build/web-game
```

Open http://localhost:8123 and click Play (audio requires a user gesture). The
output is a standalone static website. Serve it over HTTP, not `file://`.
A `.love` archive can be supplied instead of a directory. The packager only reads
the game; output must be outside it. Hidden files are excluded. Use repeated
`--include` options to avoid packaging source artwork, exports, and development
files. For example, without modifying Tiny Strategy:

```sh
python3 platform/web/package.py ~/Dev/tiny-strategy build/web-tiny-strategy \
  --include main.lua --include conf.lua --include src --include assets
```

Save data is stored in IndexedDB, isolated by origin and LÖVE identity. Writes
are persisted during play. Browser storage can be cleared or unavailable in
private browsing. The player warns when initial save loading fails.

## Scope

- WebGL 2 only; no WebGPU, compute shaders, or native-only graphics features.
- No LuaJIT or FFI/native Lua modules. The browser runtime supplies LuaJIT-style
  `load(string_or_reader, name, mode, environment)` compatibility for Lua saves.
- No worker threads in this build (`love.thread` cannot start threads).
- Native HTTPS is disabled. LuaSocket/ENet are not a browser networking solution.
- OpenAL effects and device selection are limited by Emscripten's implementation.
- Browser permissions and user gestures govern audio, fullscreen, and pointer lock.
- Custom blocking `love.run` loops must yield to the browser.
- Browser frames use `requestAnimationFrame`: vsync 0 and -1 are treated as 1.
  The standard loop skips its native 1 ms sleep on web. Higher positive swap
  intervals still deliberately skip display refreshes.
- Rendering uses WebGL 2 buffer objects without Emscripten's FULL_ES2/FULL_ES3
  emulation. Buffer readback uses `getBufferSubData`; asynchronous readbacks
  should be polled across frames so the browser can complete GPU work. Their
  `wait()` method cannot block the browser and may return before completion.

## Regression check

```sh
python3 platform/web/package.py platform/web/tests/game build/web-smoke
python3 -m http.server 8124 --bind 127.0.0.1 --directory build/web-smoke
# In another terminal, with Playwright installed:
node platform/web/tests/browser.cjs http://127.0.0.1:8124
BROWSER=firefox node platform/web/tests/browser.cjs http://127.0.0.1:8124
```

The fixture checks browser pacing, canvas pixels, partial buffer and asynchronous
buffer/texture readback, a custom shader, font drawing, audio creation, restart
data, saves across reload, and quit. `.github/workflows/web.yml` builds
and runs this in Chromium and Firefox. Tiny Strategy is an external manual integration
fixture and is not needed by CI.

## Browser profiling

Configure with `-DLOVE_WEB_PROFILING=ON` to retain Wasm function names in browser
profiles (the default is OFF). Rebuild and repackage after changing this option.
In Firefox, use the Performance panel to record active play; select a preset
which includes JavaScript and graphics. Compare the same game archive and scene,
allow shader compilation and runtime warmup, and keep the tab visible.

Measure both game frame times and browser refresh intervals: a zero-delay timer
can report high FPS while submitting multiple frames between screen refreshes.
The runtime changes do not reduce game draw calls or shader switches, which can
still dominate rendering-heavy scenes.

## Provenance

The platform adaptations were imported and revised from
[rozenmad/love-web](https://github.com/rozenmad/love-web), branch
`12.0-development`, commit `1e47faea19369911d47b6b6983e4f3a70562eac4`, relative
to its upstream LÖVE base `cdf68b3`. That work builds on David Khachaturov's
[Davidobot/love.js](https://github.com/Davidobot/love.js) and Tanner Rogalsky's
[original love.js](https://github.com/TannerRogalsky/love.js).
The original LÖVE source license headers are retained (see root `license.txt`).
The original build recipes were consulted in
[rozenmad/love-web-builder](https://github.com/rozenmad/love-web-builder) and
[rozenmad/megasource-web](https://github.com/rozenmad/megasource-web).

This integration uses our pinned dependency recipes, a new packaging/player
shell, explicit WebGL buffer/font restrictions, and a revised browser lifecycle
with Lua-state cleanup and restart support. It does not vendor a second engine
checkout or prebuilt engine binaries.
