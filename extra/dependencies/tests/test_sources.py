"""Exercise source verification and extraction without network access."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fetch


class SourcesTest(unittest.TestCase):
    def test_all_profiles_are_pinned(self):
        for profile in ('linux', 'windows', 'macos', 'ios', 'android'):
            for entry in fetch.entries(profile).values():
                self.assertTrue(entry['url'].startswith('https://'))
                self.assertRegex(entry['sha256'], r'^[0-9a-f]{64}$')
        self.assertEqual(fetch.entries('windows')['luajit']['release_timestamp'], 1784580905)
        self.assertEqual(fetch.entries('windows'), fetch.entries('android'))

    def test_bad_download_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            source.write_bytes(b'unexpected archive')
            with patch.object(fetch.time, 'sleep'):
                with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                    fetch.download(source.as_uri(), '0' * 64, root / 'download')
            self.assertFalse((root / 'download').exists())
            self.assertFalse((root / 'download.part').exists())

    def test_corrupt_cache_is_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, cache = root / 'source', root / 'cache'
            source.write_bytes(b'correct archive')
            cache.write_bytes(b'corrupt cached archive')
            fetch.download(source.as_uri(), hashlib.sha256(source.read_bytes()).hexdigest(), cache)
            self.assertEqual(source.read_bytes(), cache.read_bytes())

    def test_archive_cannot_escape_directory(self):
        for path, link in [('source/../../escape', None), ('source/link', '../../escape')]:
            with self.subTest(path=path), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                archive = root / 'source.tar.gz'
                with tarfile.open(archive, 'w:gz') as contents:
                    member = tarfile.TarInfo(path)
                    if link:
                        member.type = tarfile.SYMTYPE
                        member.linkname = link
                    contents.addfile(member)
                with self.assertRaisesRegex(ValueError, 'Unsafe archive'):
                    fetch.extract(archive, root / 'extracted')


if __name__ == '__main__':
    unittest.main()
