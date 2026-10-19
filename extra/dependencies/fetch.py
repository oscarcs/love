"""Fetch verified source archives. No build-repository checkouts or submodules."""

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
LOCK = Path(__file__).with_name('sources.json')
LIBRARIES = ('sdl', 'luajit', 'openal', 'zlib', 'freetype', 'harfbuzz',
             'ogg', 'vorbis', 'theora', 'modplug', 'bzip2', 'lua')
WINDOWS_VERSIONS = {'luajit', 'modplug'}


def entries(profile):
    lock = json.loads(LOCK.read_text())
    selected = {}
    for name in LIBRARIES:
        use_windows = profile in ('windows', 'android') and name in WINDOWS_VERSIONS
        key = name + '-windows' if use_windows else name
        if profile == 'android' and name == 'openal':
            key = 'openal-android'
        selected[name] = lock[key]
    return selected



def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def download(url, expected, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and digest(destination) == expected:
        return
    for attempt in range(3):
        temporary = destination.with_suffix(destination.suffix + '.part')
        try:
            with urllib.request.urlopen(url, timeout=120) as response, temporary.open('wb') as output:
                shutil.copyfileobj(response, output)
            if digest(temporary) != expected:
                raise ValueError('SHA-256 mismatch: ' + url)
            temporary.replace(destination)
            return
        except (OSError, ValueError):
            temporary.unlink(missing_ok=True)
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))


def extract(archive, destination):
    # Archives are pinned, but still reject paths/links escaping the extraction root.
    with tarfile.open(archive) as contents:
        members = contents.getmembers()
        roots = {Path(member.name).parts[0] for member in members if member.name not in ('.', '')}
        if len(roots) != 1:
            raise ValueError('Expected a single source directory: ' + str(archive))
        for member in members:
            path = Path(member.name)
            if path.is_absolute() or '..' in path.parts or member.isdev() or member.isfifo():
                raise ValueError('Unsafe archive member: ' + member.name)
            if member.issym() or member.islnk():
                target = Path(member.linkname)
                if target.is_absolute() or '..' in target.parts:
                    raise ValueError('Unsafe archive link: ' + member.name)
        contents.extractall(destination)
    return destination / roots.pop()


def fetch(name, entry, directory):
    destination = directory / name
    marker = destination / '.love-source.json'
    if marker.exists() and json.loads(marker.read_text()) == entry:
        return
    archives = directory / 'downloads'
    archive = archives / (name + '-' + entry['sha256'] + '.tar.gz')
    download(entry['url'], entry['sha256'], archive)
    with tempfile.TemporaryDirectory(prefix=name + '-', dir=directory) as temp:
        source = extract(archive, Path(temp))
        # Fresh source inputs must invalidate existing object files even when the
        # upstream archive contains historical timestamps.
        for path in source.rglob('*'):
            if path.is_file() and not path.is_symlink():
                os.utime(path, None)
        for patch in entry.get('patches', []):
            patch_file = LOCK.parent / patch['file']
            if digest(patch_file) != patch['sha256']:
                raise ValueError('Patch checksum mismatch: ' + str(patch_file))
            subprocess.run(['git', 'apply', '--no-index', str(patch_file.resolve())], cwd=source, check=True)
        if destination.exists():
            shutil.rmtree(destination)
        source.rename(destination)
    marker.write_text(json.dumps(entry, indent=2) + '\n')
    print('Prepared ' + name + ' ' + entry['version'], flush=True)


def collect_notices(directory, sources):
    notices = directory / 'package-assets/licenses'
    notices.mkdir(parents=True, exist_ok=True)
    for name in sources:
        source = directory / name
        for pattern in ('COPYING*', 'LICENSE*', 'COPYRIGHT*', 'docs/FTL.TXT',
                        'docs/GPLv2.TXT', 'fmt-*/LICENSE*'):
            for notice in source.glob(pattern):
                if notice.is_file():
                    target = notices / name / notice.relative_to(source)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(notice, target)
    (notices / 'sources.json').write_text(json.dumps(sources, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('linux', 'windows', 'macos', 'ios', 'android'), required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--only', choices=LIBRARIES, action='append')
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    sources = entries(args.profile)
    if args.only:
        sources = {name: sources[name] for name in args.only}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(fetch, name, entry, args.directory) for name, entry in sources.items()]
        for future in futures:
            future.result()
    collect_notices(args.directory, sources)
    (args.directory / 'sources.json').write_text(json.dumps(sources, indent=2) + '\n')


if __name__ == '__main__':
    main()
