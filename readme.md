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

### Windows
Follow the instructions at the upstream [Megasource](https://github.com/love2d/megasource) repository page, using this fork as the LÖVE source checkout.

### *nix
Because in-tree builds are not allowed, the Makefiles needs to be generated in a separate build directory. In this example, folder named `build` is used:

	$ cmake -B build -S. --install-prefix $PWD/prefix # this will create the directory `build/`.
	$ cmake --build build --target install -j$(nproc) # this will build with all cores and put the files in `prefix/`.

> [!NOTE]  
> CMake 3.15 and earlier doesn't support `--install-prefix`. In that case, use `-DCMAKE_INSTALL_PREFIX=` instead.

### macOS
Download or clone the upstream [Apple dependencies repository](https://github.com/love2d/love-apple-dependencies) and copy, move, or symlink the `macOS/Frameworks` subfolder into love's `platform/xcode/macosx` folder and the `shared` subfolder into love's `platform/xcode` folder.

Then use the Xcode project found at `platform/xcode/love.xcodeproj` to build the `love-macosx` target.

### iOS
Building for iOS requires macOS and Xcode.

Download the Apple dependency archive corresponding to the LÖVE version being used from the [upstream LÖVE releases](https://github.com/love2d/love/releases),
unzip it, and place the `iOS/libraries` subfolder into love's `platform/xcode/ios` folder and the `shared` subfolder into love's `platform/xcode` folder.

Or, download or clone the upstream [Apple dependencies repository](https://github.com/love2d/love-apple-dependencies) and copy, move, or symlink the `iOS/libraries` subfolder into love's `platform/xcode/ios` folder and the `shared` subfolder into love's `platform/xcode` folder.

Then use the Xcode project found at `platform/xcode/love.xcodeproj` to build the `love-ios` target.

See the [iOS README](readme-iOS.rtf) for more information.

### Android
Visit the upstream [Android build repository](https://github.com/love2d/love-android) for build instructions, using this fork as the LÖVE source checkout.

Dependencies
------------

- SDL3
- OpenGL 3.3+ / OpenGL ES 3.0+ / Vulkan / Metal
- OpenAL
- Lua / LuaJIT / LLVM-lua
- FreeType
- harfbuzz
- ModPlug
- Vorbisfile
- Theora
