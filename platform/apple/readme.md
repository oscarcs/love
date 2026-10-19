# Apple applications

Requires macOS 15+ or iOS 18+. See the [build instructions](../../readme.md)
for CMake commands. Add `-G Xcode` to generate an editable Xcode project in a
separate build directory.

## macOS packaging

After building with `RelWithDebInfo`, run from the repository root:

```sh
python3 extra/packaging/macos.py --build build/macos --output build/dist
```

This bundles runtime libraries, creates dSYMs, and signs the app ad hoc for local
use. Distribution requires your own signing and notarization.

## iOS device builds

Configure with `CMAKE_OSX_SYSROOT=iphoneos`, a device architecture, and your
Xcode development team and signing settings. The manual GitHub Actions workflow
checks simulator compilation only.

To embed a game, add a `.love` archive to the application bundle's resources.
Without an embedded archive, the app presents games from its Documents directory.
