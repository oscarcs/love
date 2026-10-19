"""Exercise source verification and extraction without network access."""
import hashlib
import io
import time
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
        windows, android = fetch.entries('windows'), fetch.entries('android')
        self.assertEqual({k: v for k, v in windows.items() if k != 'openal'},
                         {k: v for k, v in android.items() if k != 'openal'})
        self.assertEqual(windows['openal']['sha256'], android['openal']['sha256'])
        self.assertEqual(android['openal']['patches'][0]['file'], 'patches/openal-android.patch')

    def test_patch_hashes_match_lock(self):
        for profile in ('linux', 'windows', 'macos', 'ios', 'android'):
            for entry in fetch.entries(profile).values():
                for patch in entry.get('patches', []):
                    self.assertEqual(fetch.digest(fetch.LOCK.parent / patch['file']), patch['sha256'])

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

    def test_new_sources_invalidate_old_object_timestamps(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / 'upstream.tar.gz'
            with tarfile.open(archive, 'w:gz') as contents:
                member = tarfile.TarInfo('source/library.c')
                member.size, member.mtime = 3, 1
                contents.addfile(member, io.BytesIO(b'new'))
            before = time.time() - 1
            entry = {'version': 'test', 'url': archive.as_uri(), 'sha256': fetch.digest(archive)}
            fetch.fetch('library', entry, root)
            self.assertGreater((root / 'library/library.c').stat().st_mtime, before)
            self.assertEqual((root / 'library/library.c').read_bytes(), b'new')

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
