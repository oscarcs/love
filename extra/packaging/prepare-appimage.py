"""Prepare pinned inputs for the upstream AppImage recipe (run in its checkout)."""

import hashlib
from pathlib import Path
import subprocess
import time
import urllib.request


SOURCES = [
    ("SDL3-release-3.4.10", "libsdl-org/SDL", "8e37db5e797b6167f3a00d697d816a684bd259c7"),
    ("LuaJIT-v2.1", "LuaJIT/LuaJIT", "dd3b24369ddfaa83c78cd6fdd91d157c8968ec8d"),
    ("openal-soft-1.24.3", "kcat/openal-soft", "dc7d7054a5b4f3bec1dc23a42fd616a0847af948"),
    ("zlib-v1.3", "madler/zlib", "09155eaa2f9270dc4ed1fa13e2b4b2613e6e4851"),
    ("harfbuzz-10.1.0", "harfbuzz/harfbuzz", "9ef44a2d67ac870c1f7f671f6dc98d08a2579865"),
]
APPIMAGETOOL_VERSION = "1.9.1"
APPIMAGETOOL_SHA256 = {
    "x86_64": "ed4ce84f0d9caff66f50bcca6ff6f35aae54ce8135408b3fa33abfc3cb384eb0",
    "aarch64": "f0837e7448a0c1e4e650a93bb3e85802546e60654ef287576f46c71c126a9158",
}


def retry(operation):
    for attempt in range(3):
        try:
            return operation()
        except (OSError, subprocess.CalledProcessError):
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))


def main():
    for directory, repository, revision in SOURCES:
        subprocess.run(["git", "init", directory], check=True)
        retry(lambda: subprocess.run(
            ["git", "-C", directory, "fetch", "--depth=1",
             f"https://github.com/{repository}.git", revision], check=True))
        subprocess.run(["git", "-C", directory, "checkout", "--detach", revision], check=True)

    architecture = subprocess.check_output(["uname", "-m"], text=True).strip()
    expected = APPIMAGETOOL_SHA256[architecture]
    url = ("https://github.com/AppImage/appimagetool/releases/download/"
           f"{APPIMAGETOOL_VERSION}/appimagetool-{architecture}.AppImage")

    def download_tool():
        with urllib.request.urlopen(url, timeout=120) as response:
            contents = response.read()
        if hashlib.sha256(contents).hexdigest() != expected:
            raise OSError("AppImageTool checksum mismatch")
        Path("appimagetool").write_bytes(contents)

    retry(download_tool)
    Path("appimagetool").chmod(0o755)

    # Keep the upstream build recipe; use HTTPS for its versioned source archives.
    makefile = Path("Makefile")
    makefile.write_text(makefile.read_text().replace("http://", "https://"))


if __name__ == "__main__":
    main()
