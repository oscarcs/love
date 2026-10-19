# Dependency builds

The fork owns the download lock and build recipes. No build requires a checkout of
Megasource, love-appimage-source, love-apple-dependencies, or love-android.
Libraries are downloaded directly from their original upstream projects.

`SYSTEM` uses installed dependencies and is the default for ordinary CMake builds.
`BUNDLED` verifies every source archive against `sources.json` and builds the
libraries alongside the engine. Choose explicitly with `LOVE_DEPENDENCIES`, or
use the `system` and `bundled` CMake presets. CMake 3.21+, a C/C++ compiler,
Python 3.9+, Git, and platform SDK/build tools are required. Unix LuaJIT builds also
require make. Downloads and extracted sources live in `.deps/<profile>`; build
outputs live under `build/`. Neither is committed.

## Versions and platform differences

Linux keeps the previous AppImage library versions and locked Git revisions.
Windows and Android keep the previous Megasource versions, including LuaJIT's
actual `2460b3f` source revision (the old top-level version label was stale).
All bundled profiles select HarfBuzz 10.1.0 and SDL 3.4.10.

Apple previously used prebuilt binaries without a complete source lock. Apple
now uses the Linux source pins, with zlib 1.3.1 to support current Apple SDKs.
This replaces, among other binaries, the macOS OpenAL Soft 1.19.1 and HarfBuzz
6.0.0 frameworks. The iOS build keeps the SDK OpenAL framework. Both Apple
platforms use LuaJIT, as the former Xcode projects did. These changes are checked
by packaged macOS OpenGL/Metal tests and iOS compilation, rather than a claim
that the old binary inputs can be reproduced exactly.

Small Ogg, Vorbis, Theora decoder, and ModPlug source recipes in `Codecs.cmake`
derive from the libraries' source lists and Megasource at
`5118c13ca1dea1890e298c0ce5e410846913a5a8`. They build portable C/C++ code, retaining Theora's x86-64 SIMD decoder on Linux.
Theora encoding is not used by the engine. LuaJIT uses its native build system
through `build-luajit.py`, including Android cross compilation. Native Android
LuaJIT binaries are built from source, not copied from Megasource.

The `patches` directory preserves Megasource's ModPlug portability fixes and
Vorbis architecture check for Windows/Android. Patch hashes are included in the
source lock and package manifests. `android/opensl_latency.cpp` retains the JNI
bridge used by the application to set Oboe's device stream defaults; it was
imported from the same Megasource revision and is added to the OpenAL target.
The Android OpenAL version-script patch retains its JNI export as well as the
function implementation.

## Updating

1. Change the original source URL/version and verified SHA-256 in `sources.json`.
   For LuaJIT, also record the commit timestamp as `release_timestamp`.
2. Keep platform variants only where there is an intentional version difference.
3. Run `python3 -m unittest discover -s extra/dependencies/tests -v`.
4. Run ordinary CI plus the manual desktop and mobile workflows on the branch.
   Confirm package architecture, runtime-library closure, symbols, and API tests.

A dependency upgrade must not rely on an unpinned branch/tag lookup at build time.
Downloaded archives are cached by hash and checked again before extraction.
To start over, remove the corresponding `.deps/<profile>` and build directories.
The extracted source directories are working copies; delete them to discard
local edits. No automatic system-library fallback is used in bundled builds.

The original third-party licenses remain in each source archive. The engine's
aggregate `license.txt` and collected original dependency notices are included
in desktop packages and Android assets. The Android platform import retains
its own license and provenance in `platform/android/readme.md`.

Host packages, compilers, SDKs, and runner images can still change. Source locking
and manifests do not promise bit-for-bit reproducibility.
