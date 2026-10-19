# Packaging

Desktop packages are manual-only. In GitHub Actions, run **Desktop packages** on the desired branch or tag and select any combination of Linux x64, Linux ARM64, Windows x64, and macOS ARM64. Only selected targets run. Successful jobs upload packages, debug symbols, and `manifest.json` for 14 days; they do not create or publish a release.

The Linux helper workflow is called by the desktop workflow. **Mobile builds** is a separate manual workflow for Android Debug/Release or an iOS simulator compilation check. The iOS job does not produce a device distribution package.

## Build inputs

Dependency sources and build recipes live in `extra/dependencies`; see its
[maintenance guide](../dependencies/readme.md). Desktop and mobile workflows
check out only this fork. The Android application project is in `platform/android`.
Apple builds use CMake-generated application targets instead of prebuilt frameworks.

The Linux `appimage.py` script assembles the CMake install tree, adds its runtime
libraries and LuaJIT tooling, separates debug symbols, checks for missing/build-tree
library dependencies, and invokes AppImageTool 1.9.1 with a verified checksum.
Windows uses the root CPack ZIP configuration. `macos.py` installs and relocates the
app's libraries, creates dSYMs, strips symbols, signs the app ad hoc, and creates ZIPs.

Windows software tests use the fixed Mesa 26.2.4 archive and checksum in the
workflow. Those DLLs are copied only to the extracted test package. GitHub actions
remain pinned to commit SHAs. Android's Gradle wrapper has a fixed distribution
version and SHA-256.

Each package manifest includes the engine commit, selected dependency source
URLs/versions/hashes, and final artifact hashes. Host tools and packages remain
external inputs; the builds are not claimed to be bit reproducible.

## Validation

All desktop jobs run the existing API test suite from the packaged artifact: Linux runs the AppImage; Windows and macOS extract the ZIP and run that copy. A nonzero test exit fails the job. Linux uses Xvfb and Openbox. Software OpenGL tests use the llvmpipe linear-rasterizer workaround in the test process only; it is not included in distributed packages.

Linux currently tests OpenGL; Windows tests OpenGL and OpenGL ES; macOS tests OpenGL and Metal. Other graphics paths are not validated by these packaging jobs. Failures upload test output and logs for seven days. The smooth-line image test uses its existing Linux 1/255 color tolerance on Windows GLES llvmpipe in CI as well; see `testing/readme.md` for the scoped runner exceptions.

The package workflows retain Linux debug archives, Windows PDBs, and macOS dSYMs. Android retains unstripped native shared libraries rather than the entire native build directory. Windows source indexing, NSIS installers, and Debian packaging have been removed. Ordinary CMake installation rules remain available.
