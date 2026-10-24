"""Package a game with this fork's compiled browser runtime; never edit the input."""
import argparse
from pathlib import Path
import shutil
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--runtime', type=Path, default=Path('build/web'))
    parser.add_argument('--include', action='append', help='Game-relative file/directory to include (repeatable)')
    args = parser.parse_args()
    game, output = args.game.resolve(), args.output.resolve()
    if output == game or game in output.parents:
        parser.error('Output must be outside the input game directory')
    for name in ('love.js', 'love.wasm'):
        if not (args.runtime / name).is_file():
            parser.error('Build the web runtime first: missing ' + str(args.runtime / name))
    if game.is_dir() and not (game / 'main.lua').is_file():
        parser.error('Game directory must contain main.lua')
    if not game.exists():
        parser.error('Game does not exist')
    output.mkdir(parents=True, exist_ok=True)
    for name in ('love.js', 'love.wasm'):
        shutil.copy2(args.runtime / name, output / name)
    shutil.copytree(args.runtime / 'licenses', output / 'licenses', dirs_exist_ok=True)
    for name in ('index.html', 'player.js', 'saves.js'):
        shutil.copy2(Path(__file__).with_name(name), output / name)
    if game.is_file():
        shutil.copy2(game, output / 'game.love')
    else:
        roots = [game / name for name in args.include] if args.include else [game]
        files = set()
        for root in roots:
            if not root.resolve().is_relative_to(game):
                parser.error('--include must stay inside the game directory')
            if not root.exists():
                parser.error('Missing game path: ' + str(root))
            for path in ([root] if root.is_file() else root.rglob('*')):
                if path.is_file() and not any(part.startswith('.') for part in path.relative_to(game).parts):
                    if not path.resolve().is_relative_to(game):
                        parser.error('Game symlink points outside the game: ' + str(path))
                    files.add(path)
        if game / 'main.lua' not in files:
            parser.error('Selected files must include main.lua')
        with zipfile.ZipFile(output / 'game.love', 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(files):
                archive.write(path, path.relative_to(game))
    print('Packaged browser game at', output)


if __name__ == '__main__':
    main()
