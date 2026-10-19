"""Check packaged Android ABIs, native library closure, and the audio JNI bridge."""
import argparse
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile

MACHINES = {'armeabi-v7a': 40, 'arm64-v8a': 183, 'x86_64': 62}
REQUIRED = {'libc++_shared.so', 'libSDL3.so', 'liboboe.so', 'libopenal.so',
            'libluajit.so', 'libliblove.so', 'liblove.so'}
SYSTEM = {'libandroid.so', 'libc.so', 'libdl.so', 'liblog.so', 'libm.so',
          'libOpenSLES.so', 'libz.so', 'libEGL.so', 'libGLESv2.so', 'libGLESv3.so',
          'libvulkan.so', 'libaaudio.so', 'libnativewindow.so', 'libmediandk.so',
          'libcamera2ndk.so', 'libOpenMAXAL.so', 'libjnigraphics.so', 'libbinder_ndk.so'}
JNI = 'Java_org_love2d_android_GameActivity_nativeSetDefaultStreamValues'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--readelf', default=shutil.which('llvm-readelf') or shutil.which('readelf'))
    args = parser.parse_args()
    if not args.readelf:
        parser.error('Add readelf or the Android NDK llvm-readelf to PATH')
    packages = sorted(args.directory.glob('*.apk')) + sorted(args.directory.glob('*.aab'))
    if not packages:
        raise RuntimeError('No Android packages found')
    for package in packages:
        with zipfile.ZipFile(package) as archive, tempfile.TemporaryDirectory() as temporary:
            libraries = {}
            for name in archive.namelist():
                match = re.search(r'(?:^|/)lib/([^/]+)/([^/]+\.so)$', name)
                if match:
                    libraries.setdefault(match[1], {})[match[2]] = archive.read(name)
            if set(libraries) != set(MACHINES):
                raise RuntimeError(f'{package.name}: unexpected ABI set {sorted(libraries)}')
            for abi, files in libraries.items():
                if not REQUIRED.issubset(files):
                    raise RuntimeError(f'{package.name}: {abi} missing libraries {REQUIRED - files.keys()}')
                for name, data in files.items():
                    if data[:4] != b'\x7fELF' or struct.unpack_from('<H', data, 18)[0] != MACHINES[abi]:
                        raise RuntimeError(f'{package.name}: wrong architecture in {abi}/{name}')
                    path = Path(temporary) / name
                    path.write_bytes(data)
                    dynamic = subprocess.check_output([args.readelf, '-d', str(path)], text=True)
                    needed = set(re.findall(r'\(NEEDED\).*\[(.+?)\]', dynamic))
                    missing = needed - files.keys() - SYSTEM
                    if missing:
                        raise RuntimeError(f'{package.name}: {abi}/{name} needs absent libraries {missing}')
                    if name == 'libopenal.so':
                        symbols = subprocess.check_output([args.readelf, '--dyn-syms', '--wide', str(path)], text=True)
                        if JNI not in symbols:
                            raise RuntimeError(f'{package.name}: missing audio JNI export for {abi}')
        print(package.name + ': native libraries and audio JNI verified for ' + ', '.join(sorted(libraries)))


if __name__ == '__main__':
    main()
