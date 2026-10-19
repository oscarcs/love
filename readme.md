This is a fork of the 2D game framework, LÖVE.

Test Suite
----------

The test suite in `testing/` covers all the LÖVE APIs, and tests them the same way developers use them.

You can run the suite locally like you would run a normal LÖVE project, e.g.:  
`love testing`

The suite exits with status `0` when no tests fail, or `1` if any test fails. Skipped tests do not count as failures.

See the [test suite README](testing/readme.md) for more info.

[CI](.github/workflows/ci.yml) builds and tests Linux x64 on pull requests and pushes to `main`.
[Desktop packages](.github/workflows/main.yml) run manually through GitHub Actions, with independent selections for:

- Linux x64 and ARM64 AppImages
- Windows x64 ZIP (executables, DLLs, and LuaJIT tooling)
- macOS ARM64 app ZIP

Packages include debug symbols and a manifest with source/dependency revisions and SHA-256 hashes.
The packaged executables are tested before upload; artifacts are retained for 14 days and are not published as releases.
Linux x64 packages build on Ubuntu 22.04; ARM64 packages build on Ubuntu 24.04.
Debian packages and Windows installers are not built.

[Mobile builds](.github/workflows/mobile.yml) run separately on demand: Android Debug/Release APKs and release bundles, or an iOS simulator build check.
See [packaging maintenance](extra/packaging/readme.md) for dependency pins and validation details.

Compilation
-----------

All platforms build from this checkout. Dependency sources, versions, hashes, and
recipes are owned here; no sibling LÖVE build repository is needed.
Use CMake 3.21+, Python 3.9+, Git, and the platform's compiler/SDK. Bundled Unix builds
also need `make` for LuaJIT.

### Windows

With Visual Studio's C++ build tools installed:

```powershell
cmake -S . -B build/windows -A x64 -DLOVE_DEPENDENCIES=BUNDLED
cmake --build build/windows --config Release --parallel 2
cpack --config build/windows/CPackConfig.cmake -C Release -G ZIP
```

### Linux

Install a C/C++ toolchain, CMake, Python, make, pkg-config, and the development
packages for your system's windowing, audio, and graphics APIs. The complete
Ubuntu package list is in the [Linux packaging workflow](.github/workflows/package-linux.yml).
Then build the engine and its pinned libraries:

```sh
cmake --preset bundled
cmake --build --preset bundled
./build/bundled/love testing --all
```

To use already-installed SDL3, LuaJIT, FreeType, HarfBuzz, OpenAL, ModPlug, Ogg,
Vorbis, Theora, and zlib development packages, use the `system` preset instead.
Ordinary CMake installation is available with `cmake --install build/bundled --prefix "$PWD/prefix"`.

### macOS ARM64

With Xcode and its command-line tools installed:

```sh
cmake -S . -B build/macos -DLOVE_DEPENDENCIES=BUNDLED \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_OSX_ARCHITECTURES=arm64 \
  -DCMAKE_OSX_DEPLOYMENT_TARGET=15.0
cmake --build build/macos --target love --parallel 2
python3 extra/packaging/macos.py --build build/macos --output build/dist
```

The packaging command bundles runtime libraries, retains dSYMs, and signs the
app ad hoc. For an editable Xcode project, configure with `-G Xcode` in a separate
build directory, then build the `love` target with `--config RelWithDebInfo`.

### iOS

With Xcode and the iOS SDK installed:

```sh
cmake -S . -B build/ios -G Xcode -DLOVE_DEPENDENCIES=BUNDLED \
  -DCMAKE_SYSTEM_NAME=iOS -DCMAKE_OSX_SYSROOT=iphonesimulator \
  -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=18.0 \
  -DCMAKE_XCODE_ATTRIBUTE_CODE_SIGNING_ALLOWED=NO
cmake --build build/ios --target love --config Release -- CODE_SIGNING_ALLOWED=NO
```

The minimum supported iOS version is 18. Simulator builds are unsigned compilation checks. Device builds
require the device SDK and your signing configuration.

### Android

The application project lives in [platform/android](platform/android/readme.md).
Install Java 17 and the Android SDK, set `ANDROID_HOME`, then:

```sh
python3 extra/dependencies/fetch.py --profile android --directory .deps/android
cd platform/android
./gradlew assembleNormalRecordRelease
```

See [dependency maintenance](extra/dependencies/readme.md) for source pins,
platform differences, and updating instructions.

Dependencies
------------

- SDL3
- OpenGL 3.3+ / OpenGL ES 3.0+ / Vulkan / Metal
- OpenAL
- LuaJIT / Lua 5.1
- FreeType
- harfbuzz
- ModPlug
- Vorbisfile
- Theora
