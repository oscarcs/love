# Packaging

Desktop packages are manual-only. In GitHub Actions, run **Desktop packages** on the desired branch or tag and select any combination of Linux x64, Linux ARM64, Windows x64, and macOS ARM64. Only selected targets run. Successful jobs upload packages, debug symbols, and `manifest.json` for 14 days; they do not create or publish a release.

The Linux helper workflow is called by the desktop workflow. **Mobile builds** is a separate manual workflow for Android Debug/Release or an iOS simulator compilation check. The iOS job does not produce a device distribution package.

## Build inputs

The existing upstream build systems remain in use:

- AppImage recipe: `love2d/love-appimage-source`, pinned in `.github/workflows/package-linux.yml`.
- Windows/Android dependencies: `love2d/megasource`, pinned in the desktop and mobile workflows.
- Apple dependencies: `love2d/love-apple-dependencies`, pinned in both workflows.
- Android build: `love2d/love-android`, pinned in the mobile workflow.
- Linux Git dependencies and AppImageTool: pinned in `prepare-appimage.py`. The script prefetches exact commits into the directories expected by the pinned Makefile and verifies AppImageTool's SHA-256. The upstream recipe's versioned source archives use HTTPS; their hashes are recorded in the manifest.
- Windows software test driver: fixed Mesa 26.2.4 archive, verified against the checksum in the desktop workflow. Its DLLs are copied only into the extracted test package, after the distributable ZIP has been created.
- GitHub actions: pinned to commit SHAs with major-version comments.

Update repeated pins together. When changing the AppImage recipe, check its dependency directory names and archive versions against `prepare-appimage.py`. Host packages, runner images, and transitive download contents can still change; the manifests describe the inputs used, rather than promising bit-for-bit reproducible builds.

## Validation

All desktop jobs run the existing API test suite from the packaged artifact: Linux runs the AppImage; Windows and macOS extract the ZIP and run that copy. A nonzero test exit fails the job. Linux uses Xvfb and Openbox. Software OpenGL tests use the llvmpipe linear-rasterizer workaround in the test process only; it is not included in distributed packages.

Linux currently tests OpenGL; Windows tests OpenGL and OpenGL ES; macOS tests OpenGL and Metal. Other graphics paths are not validated by these packaging jobs. Failures upload test output and logs for seven days. The smooth-line image test uses its existing Linux 1/255 color tolerance on Windows GLES llvmpipe in CI as well; see `testing/readme.md` for the scoped runner exceptions.

The package workflows retain Linux debug archives, Windows PDBs, and macOS dSYMs. Android retains unstripped native shared libraries rather than the entire native build directory. Windows source indexing, NSIS installers, and Debian packaging have been removed. Ordinary CMake installation rules remain available.
