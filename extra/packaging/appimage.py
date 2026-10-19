"""Assemble an AppImage from this fork's bundled CMake build."""

import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dependencies'))
from fetch import download

APPIMAGETOOL_VERSION = '1.9.1'
APPIMAGETOOL_SHA256 = {
    'x86_64': 'ed4ce84f0d9caff66f50bcca6ff6f35aae54ce8135408b3fa33abfc3cb384eb0',
    'aarch64': 'f0837e7448a0c1e4e650a93bb3e85802546e60654ef287576f46c71c126a9158',
}


def run(*args, **kwargs):
    subprocess.run([str(arg) for arg in args], check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    build, output = args.build.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    appdir, symbols = build / 'AppDir', build / 'symbols'
    for directory in (appdir, symbols):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir()
    run('cmake', '--install', build, '--prefix', appdir)
    libraries = (appdir / 'lib')
    libraries.mkdir(exist_ok=True)
    for line in (build / 'runtime-RelWithDebInfo.txt').read_text().splitlines():
        source = Path(line)
        if source.is_file():
            # Keep the SONAME as well as the actual filename. ldd below verifies closure.
            shutil.copy2(source, libraries / source.name)
            dynamic = subprocess.check_output(['readelf', '-d', str(source)], text=True)
            import re
            match = re.search(r'\(SONAME\).*\[(.+?)\]', dynamic)
            if match and match[1] != source.name:
                (libraries / match[1]).symlink_to(source.name)
    shutil.copy2(root / 'extra/packaging/AppRun', appdir / 'AppRun')
    (appdir / 'AppRun').chmod(0o755)
    shutil.copy2(build / 'love.desktop', appdir / 'love.desktop')
    shutil.copy2(root / 'platform/unix/love.svg', appdir / 'love.svg')
    shutil.copy2(root / 'license.txt', appdir / 'license.txt')
    jit = appdir / 'share/luajit-2.1/jit'
    jit.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(build / 'dependencies/luajit/jit', jit, dirs_exist_ok=True)
    shutil.copytree(root / '.deps/linux/package-assets/licenses', appdir / 'share/licenses', dirs_exist_ok=True)
    binaries = [appdir / 'bin/love'] + [p for p in libraries.iterdir() if p.is_file() and not p.is_symlink()]
    for binary in binaries:
        symbol = symbols / (binary.name + '.debug')
        run('objcopy', '--only-keep-debug', binary, symbol)
        run('strip', '--strip-unneeded', binary)
        run('objcopy', '--add-gnu-debuglink=' + str(symbol), binary)
        run('patchelf', '--set-rpath', '$ORIGIN/../lib', binary)
    environment = dict(os.environ, LD_LIBRARY_PATH=str(libraries))
    for binary in binaries:
        closure = subprocess.check_output(['ldd', str(binary)], text=True, env=environment)
        if 'not found' in closure or str(build) in closure.replace(str(appdir), '') or str(root / '.deps') in closure:
            raise RuntimeError('Package has an unresolved or build-tree library dependency:\n' + closure)
    arch = platform.machine()
    name = 'love-linux-' + {'x86_64': 'x64', 'aarch64': 'arm64'}[arch]
    with tarfile.open(output / (name + '-debug.tar.gz'), 'w:gz') as archive:
        for symbol in sorted(symbols.iterdir()):
            archive.add(symbol, arcname=symbol.name)
    tool = build / 'appimagetool'
    download(f'https://github.com/AppImage/appimagetool/releases/download/{APPIMAGETOOL_VERSION}/appimagetool-{arch}.AppImage',
             APPIMAGETOOL_SHA256[arch], tool)
    tool.chmod(0o755)
    run(tool, appdir, output / (name + '.AppImage'), env=dict(os.environ, ARCH=arch))


if __name__ == '__main__':
    main()
