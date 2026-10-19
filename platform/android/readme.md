# Android application

## Build

Install Java 17 and the Android SDK. Set `ANDROID_HOME`, or set `sdk.dir` in
`platform/android/local.properties`. From the repository root:

```sh
python3 extra/dependencies/fetch.py --profile android --directory .deps/android
cd platform/android
./gradlew assembleNormalRecordRelease
```

Use `assembleNormalRecordDebug` for a debug APK. Outputs are under
`app/build/outputs/`. Release APKs require signing before installation.

The default ABIs are `armeabi-v7a`, `arm64-v8a`, and `x86_64`. Building all three
requires a Linux x64 host with `gcc-multilib` for LuaJIT's host tools. On Apple
Silicon, or to build only the 64-bit ABIs:

```sh
./gradlew assembleNormalRecordRelease -Papp.abis=arm64-v8a,x86_64
```

## Configure the app

Set the display name, application ID, orientation, and version in
[gradle.properties](gradle.properties).

For automated builds and release bundles, see the
[packaging guide](../../extra/packaging/readme.md).

Android application code is based on [LÖVE for Android](https://github.com/love2d/love-android);
see [license.txt](license.txt) for licensing.
