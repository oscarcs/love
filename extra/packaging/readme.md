# Packaging

## GitHub Actions

Run [Desktop packages](../../.github/workflows/main.yml) manually on the desired
branch or tag, selecting the targets to build:

| Target | Package | Debug symbols |
| --- | --- | --- |
| Linux x64 / ARM64 | AppImage | Debug archive |
| Windows x64 | Portable ZIP | PDBs |
| macOS ARM64 | App ZIP | dSYMs |

Download the results from the workflow run's artifacts. Packages, symbols, and
`manifest.json` are kept for 14 days. Each manifest records the engine commit,
dependency source versions and hashes, and artifact SHA-256 hashes. The workflow
does not publish GitHub releases.

Run [Mobile builds](../../.github/workflows/mobile.yml) separately. Choose Android
Debug or Release for APKs; Release also produces app bundles. Android artifacts
include unstripped native libraries. The iOS option checks simulator compilation
and uploads build metadata.

## Package locally

First follow the [build instructions](../../readme.md). Run these commands from
the repository root.

For a Linux bundled `RelWithDebInfo` build, install `patchelf` and binutils, then:

```sh
python3 extra/packaging/appimage.py --build build/bundled --output build/dist
```

The script downloads a checksummed AppImageTool and bundles runtime libraries,
LuaJIT tooling, license notices, and separate debug symbols.

For Windows:

```powershell
cpack --config build/windows/CPackConfig.cmake -C Release -G ZIP
```

For macOS, use the [Apple packaging instructions](../../platform/apple/readme.md).
For Android, use the [Gradle build instructions](../../platform/android/readme.md).

## Package checks

Desktop jobs run the API suite using the packaged executable. Linux tests OpenGL,
Windows tests OpenGL and OpenGL ES, and macOS tests OpenGL and Metal. Failed jobs
upload reports and logs for seven days.

Android checks package ABIs, ELF architectures, required native libraries,
shared-library dependencies, and the audio initialization JNI export. Mobile
jobs do not run the API suite on a device or emulator.

See the [test guide](../../testing/readme.md) for runner settings and the
[dependency guide](../dependencies/readme.md) for updating package inputs.
