"""Build the locked LuaJIT source with its native make/MSVC build system."""

import argparse
import json
import os
import platform
from pathlib import Path
import shutil
import subprocess


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'directory', 'profile', 'architecture', 'compiler'):
        p.add_argument('--' + name, required=True)
    p.add_argument('--sdk', default='')
    p.add_argument('--deployment-target', default='')
    p.add_argument('--android-api', default='23')
    a = p.parse_args()
    source, directory = Path(a.source), Path(a.directory)
    work = directory / 'source'
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(source, work)
    # A source archive has no Git metadata. Never derive the rolling version from
    # the enclosing fork's unrelated Git history.
    entry = json.loads((source / '.love-source.json').read_text())
    (work / '.relver').write_text(str(entry['release_timestamp']) + '\n')
    directory.mkdir(parents=True, exist_ok=True)
    if a.profile == 'windows':
        vswhere = Path(os.environ['ProgramFiles(x86)']) / 'Microsoft Visual Studio/Installer/vswhere.exe'
        installation = subprocess.check_output([str(vswhere), '-latest', '-products', '*', '-requires',
                                                'Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
                                                '-property', 'installationPath'], text=True).strip()
        devcmd = Path(installation) / 'Common7/Tools/VsDevCmd.bat'
        script = directory / 'build.cmd'
        script.write_text('@echo off\ncall "' + str(devcmd) + '" -arch=' + a.architecture + '\n'
                          'if errorlevel 1 exit /b %errorlevel%\ncd /d "' + str(work / 'src') +
                          '"\ncall msvcbuild.bat amalg\nexit /b %errorlevel%\n')
        subprocess.run(['cmd', '/c', str(script)], check=True)
        for name in ('lua51.dll', 'lua51.lib', 'lua51.pdb'):
            shutil.copy2(work / 'src' / name, directory / name)
    else:
        command = ['make', '-j2', 'amalg', 'CCDEBUG=-g', 'BUILDMODE=' + ('static' if a.profile == 'ios' else 'dynamic')]
        if a.profile == 'android':
            triples = {'arm64-v8a': 'aarch64-linux-android', 'armeabi-v7a': 'armv7a-linux-androideabi',
                       'x86_64': 'x86_64-linux-android', 'x86': 'i686-linux-android'}
            toolchain = Path(a.compiler).parent
            cc = str(toolchain / (triples[a.architecture] + a.android_api + '-clang'))
            host_cc = 'cc -m32' if a.architecture in ('armeabi-v7a', 'x86') else 'cc'
            command += ['HOST_CC=' + host_cc, 'CROSS=' + str(toolchain / 'llvm-'), 'STATIC_CC=' + cc,
                        'DYNAMIC_CC=' + cc + ' -fPIC', 'TARGET_LD=' + cc, 'TARGET_SYS=Linux',
                        'TARGET_AR=' + str(toolchain / 'llvm-ar') + ' rcus',
                        'TARGET_STRIP=' + str(toolchain / 'llvm-strip'),
                        'TARGET_XSHLDFLAGS=-shared -Wl,-soname,libluajit.so -Wl,-z,max-page-size=16384']
        elif a.profile in ('macos', 'ios'):
            flags = '-arch ' + a.architecture + ' -isysroot ' + a.sdk
            if a.profile == 'ios':
                minimum = '-mios-simulator-version-min=' if 'simulator' in a.sdk.lower() else '-mios-version-min='
                flags += ' ' + minimum + (a.deployment_target or '18.0')
                command += ['TARGET_SYS=iOS']
            else:
                flags += ' -mmacosx-version-min=' + (a.deployment_target or '15.0')
            host_sdk = subprocess.check_output(['xcrun', '--sdk', 'macosx', '--show-sdk-path'], text=True).strip()
            host_cc = (a.compiler + ' -isysroot ' + host_sdk + ' -target '
                       + platform.machine() + '-apple-macos15.0')
            # Xcode exports the target SDKROOT, including into host-tool builds.
            os.environ['SDKROOT'] = host_sdk
            command += ['CC=' + a.compiler, 'HOST_CC=' + host_cc, 'TARGET_FLAGS=' + flags]
            os.environ.pop('IPHONEOS_DEPLOYMENT_TARGET', None)
            os.environ['MACOSX_DEPLOYMENT_TARGET'] = (a.deployment_target or '15.0') if a.profile == 'macos' else '15.0'
        subprocess.run(command, cwd=work, check=True)
        built = work / 'src' / ('libluajit.a' if a.profile == 'ios' else 'libluajit.so')
        output = {'linux': 'libluajit-5.1.so.2', 'macos': 'libluajit-5.1.2.dylib',
                  'ios': 'libluajit.a', 'android': 'libluajit.so'}[a.profile]
        shutil.copy2(built, directory / output)
        if a.profile == 'macos':
            subprocess.run(['install_name_tool', '-id', '@rpath/' + output, str(directory / output)], check=True)
    for header in ('lua.h', 'lauxlib.h', 'lualib.h', 'luaconf.h', 'lua.hpp', 'luajit.h'):
        shutil.copy2(work / 'src' / header, directory / header)
    shutil.copytree(work / 'src/jit', directory / 'jit', dirs_exist_ok=True)


if __name__ == '__main__':
    main()
