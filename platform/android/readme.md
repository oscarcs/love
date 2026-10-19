# Android application

The Android application shell was imported from love2d/love-android at
`4c65fff4f8b38693aca5d91bc06f254f86a97adf` and adapted for this fork.
Original copyright notices and `license.txt` are retained.

First run `python3 extra/dependencies/fetch.py --profile android --directory .deps/android`
from the repository root to prepare SDL Java sources as well as native dependencies.
Then build from this directory with `./gradlew assembleNormalRecordRelease`.
Set `sdk.dir` in an untracked `local.properties`, or set `ANDROID_HOME`.
The native build uses the fork root and its pinned dependency sources.

The full ABI set includes 32-bit ARM and requires a Linux x64 host with
`gcc-multilib` to build LuaJIT's matching host tools. To build only the 64-bit
ABIs (including on Apple Silicon), pass
`-Papp.abis=arm64-v8a,x86_64` to Gradle.
