# Apple applications

The supported minimums are macOS 15 and iOS 18.

The root CMake build generates macOS and iOS application targets and can generate
an editable Xcode project with `-G Xcode`. See the root README for exact commands.
The former hand-maintained Xcode projects and external framework copies have
been replaced by the same source-built dependency targets used on other platforms.

The plists, icons, launch screen, and entitlements here retain the application
integration from the original Xcode projects. Both application types retain the
`.love` document association. macOS packages are signed ad hoc for local testing;
distribution signing and notarization remain separate release tasks.

For an iOS device build, use `CMAKE_OSX_SYSROOT=iphoneos`, an architecture supported
by the device SDK, and your development team/signing configuration. The manual
workflow checks only the simulator target. Place an embedded game in the app's
Resources as `game.love` (or a `game` directory); `src/common/ios.mm` retains the
existing game-selection and Documents-folder behavior.
