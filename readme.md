# LÖVE

A fork of the LÖVE 2D game framework.

## Run a game

Pass a game directory containing `main.lua`, or a `.love` archive, to the executable:

```sh
love /path/to/game
love /path/to/game.love
```

## Build

Run the commands below from the repository root. Bundled builds require CMake
3.21+, Python 3.9+, Git, and the platform's C/C++ compiler and SDK. Unix builds
also require `make` for LuaJIT. Dependencies download during configuration.

### Windows

With Visual Studio's C++ build tools installed:

```powershell
cmake -S . -B build/windows -A x64 -DLOVE_DEPENDENCIES=BUNDLED
cmake --build build/windows --config Release --parallel 2
```

### Linux

Install a C/C++ toolchain, CMake, Python, make, pkg-config, and the development
packages for your system's windowing, audio, and graphics APIs. The complete
Ubuntu package list is in the [Linux packaging workflow](.github/workflows/package-linux.yml).
Then build the engine and its pinned libraries:

```sh
cmake --preset bundled
cmake --build --preset bundled
./build/bundled/love /path/to/game
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
./build/macos/love.app/Contents/MacOS/love /path/to/game
```

For an editable Xcode project, configure with `-G Xcode` in a separate build
directory, then build with `--config RelWithDebInfo`. See the
[Apple application guide](platform/apple/readme.md) for signing and embedding games.

### iOS

With Xcode and the iOS SDK installed:

```sh
cmake -S . -B build/ios -G Xcode -DLOVE_DEPENDENCIES=BUNDLED \
  -DCMAKE_SYSTEM_NAME=iOS -DCMAKE_OSX_SYSROOT=iphonesimulator \
  -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=18.0 \
  -DCMAKE_XCODE_ATTRIBUTE_CODE_SIGNING_ALLOWED=NO
cmake --build build/ios --target love --config Release -- CODE_SIGNING_ALLOWED=NO
```

The minimum supported iOS version is 18. This builds an unsigned ARM64 simulator
app. Device builds require the device SDK and your signing configuration.

### Android

The application project lives in [platform/android](platform/android/readme.md).
Install Java 17 and the Android SDK, set `ANDROID_HOME`, then:

```sh
python3 extra/dependencies/fetch.py --profile android --directory .deps/android
cd platform/android
./gradlew assembleNormalRecordRelease
```

## Test

Run the API suite with the executable you built:

```sh
./build/bundled/love testing --all
```

The exit status is `0` when no tests fail and `1` when any test fails. Skipped
tests do not count as failures. See the [test guide](testing/readme.md) for
selecting tests and reading reports.

## Packages and CI

[CI](.github/workflows/ci.yml) builds and tests Linux x64 on pull requests and
pushes to `main`. Desktop and mobile packages are built manually through GitHub
Actions. See the [packaging guide](extra/packaging/readme.md) for targets,
artifacts, and local packaging commands.

For dependency configuration and updates, see the
[dependency guide](extra/dependencies/readme.md).
