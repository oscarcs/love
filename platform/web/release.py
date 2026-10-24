"""Create a reusable web runtime distribution from a completed build."""
import argparse
import json
from pathlib import Path
from package import runtime_files, manifest, write_zip


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, default=Path('build/web'))
    parser.add_argument('--output', type=Path, default=Path('dist/love-web-runtime.zip'))
    parser.add_argument('--revision', help='Source revision recorded by CI')
    args = parser.parse_args()
    try:
        if args.output.resolve().is_relative_to(args.runtime.resolve()):
            raise ValueError('Release archive must be outside the runtime directory')
        files = runtime_files(args.runtime)
        for name in ('index.html', 'player.js', 'saves.js', 'package.py', 'serve.py', 'readme.md', 'hosting.md'):
            files[name] = Path(__file__).with_name(name).read_bytes()
        metadata = manifest(files)
        if args.revision:
            metadata['sourceRevision'] = args.revision
        files['runtime-manifest.json'] = (json.dumps(metadata, sort_keys=True, indent=2) + '\n').encode()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_zip(args.output, files)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print('Packaged web runtime at', args.output.resolve())


if __name__ == '__main__':
    main()
