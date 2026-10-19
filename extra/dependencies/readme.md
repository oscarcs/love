# Dependencies

## Select a provider

Set `LOVE_DEPENDENCIES` when configuring CMake:

| Provider | Requirements |
| --- | --- |
| `SYSTEM` (default) | Installed SDL3, LuaJIT, FreeType, HarfBuzz, OpenAL, ModPlug, Ogg, Vorbis, Theora, and zlib development packages |
| `BUNDLED` | Python 3.9+, Git, internet access for downloads, and `make` for Unix LuaJIT builds |

Both providers require CMake 3.21+ and the platform's compiler and SDK. The
`system` and `bundled` [presets](../../CMakePresets.json) select the provider and
use separate build directories. See the [build instructions](../../readme.md)
for platform commands. Set `LOVE_JIT=OFF` to use Lua 5.1 instead of LuaJIT.

## Download and cache sources

[sources.json](sources.json) specifies source URLs, versions, SHA-256 hashes,
and platform variants. Bundled configuration downloads and verifies these
sources automatically. To fetch them separately:

```sh
python3 extra/dependencies/fetch.py --profile linux --directory .deps/linux
```

Profiles are `linux`, `windows`, `macos`, `ios`, and `android`. Downloads and
extracted sources are cached under `.deps/<profile>`. To discard source edits
and rebuild from scratch, remove that profile directory and its CMake build
directory, then configure again.

## Update a dependency

1. Update the source URL, version, and SHA-256 in `sources.json`, including any
   affected platform variants. LuaJIT also requires the commit timestamp in
   `release_timestamp`.
2. If a patch changes, update its file and hash in the source lock. Build recipes
   are in [Bundled.cmake](Bundled.cmake), [Codecs.cmake](Codecs.cmake), and
   [LuaJIT.cmake](LuaJIT.cmake).
3. Run the source-fetch tests from the repository root:

   ```sh
   python3 -m unittest discover -s extra/dependencies/tests -v
   ```

4. Run CI and the relevant manual [packaging workflows](../packaging/readme.md).
   Check API tests, package architectures, runtime libraries, and debug symbols.

Use fixed source archives or revisions with verified hashes. Packages include
original dependency license notices; keep these available when changing sources.
