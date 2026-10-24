import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('web_package', Path(__file__).parents[1] / 'package.py')
pack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pack)


class PackageTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / 'game'
        self.game.mkdir()
        (self.game / 'main.lua').write_text('function love.draw() end')
        (self.game / '.private').write_text('not for shipping')
        self.runtime = self.root / 'runtime'
        self.runtime.mkdir()
        for name in pack.RUNTIME_FILES:
            (self.runtime / name).write_bytes(b'runtime')
        (self.runtime / 'licenses').mkdir()
        (self.runtime / 'licenses/LOVE.txt').write_text('notice')

    def test_reproducible_complete_package(self):
        first, second = self.root / 'one', self.root / 'two'
        a, b = self.root / 'a.zip', self.root / 'b.zip'
        files = pack.package(self.game, first, self.runtime, compress=True, archive=a)
        (self.game / 'main.lua').touch()
        pack.package(self.game, second, self.runtime, compress=True, archive=b)
        self.assertEqual(a.read_bytes(), b.read_bytes())
        with zipfile.ZipFile(io.BytesIO(files['game.love'])) as game:
            self.assertEqual(game.namelist(), ['main.lua'])
        self.assertEqual(gzip.decompress(files['love.wasm.gz']), files['love.wasm'])
        for name, data in json.loads(files['manifest.json'])['assets'].items():
            self.assertEqual(data['sha256'], hashlib.sha256(files[name]).hexdigest())
            self.assertEqual(data['bytes'], len(files[name]))
        self.assertIn(b'player.js?v=', files['index.html'])
        self.assertIn('licenses/LOVE.txt', files)
        # Turning compression off must not leave stale sidecars behind.
        pack.package(self.game, first, self.runtime)
        self.assertFalse((first / 'love.wasm.gz').exists())

    def test_invalid_inputs_do_not_write_output(self):
        out = self.root / 'out'
        for include in [['missing'], ['../runtime'], ['.private']]:
            with self.assertRaises(ValueError):
                pack.package(self.game, out, self.runtime, includes=include)
            self.assertFalse(out.exists())
        with self.assertRaises(ValueError):
            pack.package(self.game, self.game / 'output', self.runtime)
        with self.assertRaises(ValueError):
            pack.package(self.game, out, self.runtime, archive=self.game / 'release.zip')
        self.assertFalse(out.exists())

    def test_input_and_output_symlink_escape(self):
        (self.game / 'leak').symlink_to(self.runtime / 'love.js')
        with self.assertRaises(ValueError):
            pack.package(self.game, self.root / 'out', self.runtime)
        (self.game / 'leak').unlink()
        out = self.root / 'out'
        out.mkdir()
        (out / 'love.js').symlink_to(self.game / 'main.lua')
        with self.assertRaises(ValueError):
            pack.package(self.game, out, self.runtime)
        self.assertEqual((self.game / 'main.lua').read_text(), 'function love.draw() end')

    def test_love_input_is_preserved(self):
        source = self.root / 'source.love'
        pack.write_zip(source, {'main.lua': b'print(1)'})
        files = pack.package(source, self.root / 'out', self.runtime)
        self.assertEqual(files['game.love'], source.read_bytes())
        self.assertEqual(source.read_bytes(), files['game.love'])


if __name__ == '__main__':
    unittest.main()
