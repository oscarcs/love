"""Package a game with a compiled browser runtime; never edit the input."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import zipfile

SHELL_FILES = ('index.html', 'player.js', 'saves.js')
RUNTIME_FILES = ('love.js', 'love.wasm')


def write_zip(path, files):
    """Stable ordering, timestamps and permissions, independent of input mtimes."""
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def gzip_bytes(data):
    out = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=out, mtime=0, compresslevel=9) as stream:
        stream.write(data)
    return out.getvalue()


def manifest(files):
    return {'version': 1, 'assets': {name: {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
                                   for name, data in sorted(files.items())}}


def runtime_files(runtime):
    files = {name: (runtime / name).read_bytes() for name in RUNTIME_FILES}
    licenses = runtime / 'licenses'
    if not licenses.is_dir():
        raise ValueError('Runtime licenses are missing: ' + str(licenses))
    for path in sorted(licenses.rglob('*')):
        if path.is_file():
            files['licenses/' + path.relative_to(licenses).as_posix()] = path.read_bytes()
    return files


def package(game, output, runtime, includes=None, compress=False, archive=None):
    game, output, runtime = game.resolve(), output.resolve(), runtime.resolve()
    if output == game or game in output.parents:
        raise ValueError('Output must be outside the input game directory')
    if output == runtime or runtime in output.parents:
        raise ValueError('Output must be outside the runtime directory')
    if archive and (archive.resolve() == game or game in archive.resolve().parents):
        raise ValueError('Archive must be outside the input game directory')
    if archive and (archive.resolve() == runtime or runtime in archive.resolve().parents):
        raise ValueError('Archive must be outside the runtime directory')
    files = runtime_files(runtime)
    if game.is_file():
        if includes:
            raise ValueError('--include is only supported for game directories')
        with zipfile.ZipFile(game) as z:
            if 'main.lua' not in z.namelist():
                raise ValueError('Game archive must contain main.lua')
        files['game.love'] = game.read_bytes()
    elif game.is_dir():
        selected = {}
        roots = [game / name for name in includes] if includes else [game]
        for root in roots:
            if not root.resolve().is_relative_to(game):
                raise ValueError('--include must stay inside the game directory')
            if not root.exists():
                raise ValueError('Missing game path: ' + str(root))
            for path in ([root] if root.is_file() else root.rglob('*')):
                if path.is_file() and not any(part.startswith('.') for part in path.relative_to(game).parts):
                    if not path.resolve().is_relative_to(game):
                        raise ValueError('Game symlink points outside the game: ' + str(path))
                    selected[path.relative_to(game).as_posix()] = path.read_bytes()
        if 'main.lua' not in selected:
            raise ValueError('Selected files must include main.lua')
        buffer = io.BytesIO()
        write_zip(buffer, selected)
        files['game.love'] = buffer.getvalue()
    else:
        raise ValueError('Game does not exist')
    shell = Path(__file__).parent
    files.update({name: (shell / name).read_bytes() for name in SHELL_FILES})
    # HTML revalidates; versioned scripts and the manifest prevent mixing releases.
    html = files['index.html'].decode('utf-8')
    for name in ('player.js', 'saves.js'):
        digest = hashlib.sha256(files[name]).hexdigest()
        html = html.replace('src="' + name + '"', 'src="' + name + '?v=' + digest + '"')
    files['index.html'] = html.encode('utf-8')
    files['manifest.json'] = (json.dumps(manifest(files), sort_keys=True, indent=2) + '\n').encode()
    if compress:
        files.update({name + '.gz': gzip_bytes(data) for name, data in list(files.items())
                      if name in (*SHELL_FILES, *RUNTIME_FILES, 'game.love', 'manifest.json')})
    # Validate everything before creating or replacing any output files.
    if archive and archive.resolve() in {(output / name).resolve() for name in files}:
        raise ValueError('Archive path conflicts with a packaged asset')
    output.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        path = output / name
        if path.is_symlink() or not path.resolve().is_relative_to(output):
            raise ValueError('Output path escapes package directory: ' + str(path))
    for name, data in files.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    if not compress:
        for name in (*SHELL_FILES, *RUNTIME_FILES, 'game.love', 'manifest.json'):
            (output / (name + '.gz')).unlink(missing_ok=True)
    if archive:
        archive.parent.mkdir(parents=True, exist_ok=True)
        write_zip(archive, files)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--runtime', type=Path, default=Path('build/web'))
    parser.add_argument('--include', action='append', help='Game-relative file/directory (repeatable)')
    parser.add_argument('--compress', action='store_true', help='Generate gzip sidecars for configured HTTP servers')
    parser.add_argument('--archive', type=Path, help='Also create a reproducible deployment ZIP')
    args = parser.parse_args()
    try:
        package(args.game, args.output, args.runtime, args.include, args.compress, args.archive)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        parser.error(str(error))
    print('Packaged browser game at', args.output.resolve())


if __name__ == '__main__':
    main()
