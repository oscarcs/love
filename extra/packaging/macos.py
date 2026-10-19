"""Install a relocatable macOS application, sign it ad hoc, and retain symbols."""

import argparse
from pathlib import Path
import shutil
import subprocess


def run(*args):
    subprocess.run([str(arg) for arg in args], check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    root = Path(__file__).resolve().parents[2]
    build, output = a.build.resolve(), a.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    stage = build / 'package'
    if stage.exists():
        shutil.rmtree(stage)
    run('cmake', '--install', build, '--prefix', stage)
    app = stage / 'love.app'
    symbols = stage / 'dSYMs'
    symbols.mkdir()
    for binary in [app / 'Contents/MacOS/love'] + list((app / 'Contents/Frameworks').glob('*.dylib')):
        run('xcrun', 'dsymutil', binary, '-o', symbols / (binary.name + '.dSYM'))
        run('xcrun', 'strip', '-S', binary)
        run('codesign', '--force', '--sign', '-', binary)
    run('codesign', '--force', '--sign', '-', '--entitlements', root / 'platform/apple/love.entitlements', app)
    run('codesign', '--verify', '--deep', '--strict', app)
    run('ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', app, output / 'love-macos-arm64.zip')
    run('ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', symbols, output / 'love-macos-arm64-debug.zip')


if __name__ == '__main__':
    main()
