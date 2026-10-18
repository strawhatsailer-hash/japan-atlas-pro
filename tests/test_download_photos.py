import importlib.util
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'download_photos.py'
spec = importlib.util.spec_from_file_location('download_photos', SCRIPT)
downloader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(downloader)

SEED_SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'seed_published_photos.py'
seed_spec = importlib.util.spec_from_file_location('seed_published_photos', SEED_SCRIPT)
seed_script = importlib.util.module_from_spec(seed_spec)
seed_spec.loader.exec_module(seed_script)

class PhotoBundlerTests(unittest.TestCase):
    def test_mugiwara_has_japanese_and_english_searches(self):
        queries = downloader.queries_for({'id':'t9','name':'ONE PIECE Mugiwara Store','area':'Tokyo'})
        self.assertGreaterEqual(len(queries), 2)
        self.assertIn('麦わらストア', queries[0])
        self.assertTrue(any('Mugiwara Store' in q for q in queries))

    def test_cached_local_asset_is_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'assets' / 'photos').mkdir(parents=True)
            asset = root / 'assets' / 'photos' / 't1-1.jpg'
            asset.write_bytes(b'x' * 2000)
            old_dist = downloader.DIST
            try:
                downloader.DIST = root
                self.assertTrue(downloader.local_asset_exists({'thumb':'./assets/photos/t1-1.jpg'}))
                self.assertFalse(downloader.local_asset_exists({'thumb':'./assets/photos/missing.jpg'}))
                self.assertFalse(downloader.local_asset_exists({'thumb':'https://example.invalid/image.jpg'}))
                self.assertFalse(downloader.local_asset_exists({'thumb':'./assets/photos/../../outside.jpg'}))
            finally:
                downloader.DIST = old_dist

    def test_unknown_place_has_safe_default_query(self):
        self.assertEqual(downloader.queries_for({'id':'custom1','name':'Test Place','area':'Kyoto'}), ['Test Place Kyoto Japan'])

    def test_seed_script_only_accepts_safe_photo_paths(self):
        self.assertEqual(seed_script.safe_rel('./assets/photos/t1-1.jpg'), 'assets/photos/t1-1.jpg')
        self.assertIsNone(seed_script.safe_rel('https://example.invalid/photo.jpg'))
        self.assertIsNone(seed_script.safe_rel('./assets/photos/../../secret.txt'))
        self.assertIsNone(seed_script.safe_rel('./other/file.jpg'))

    def test_build_reuses_existing_bundle_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            photo_dir = root / 'assets' / 'photos'
            photo_dir.mkdir(parents=True)
            asset = photo_dir / 't1-1.jpg'
            asset.write_bytes(b'x' * 2500)
            manifest_path = photo_dir / 'manifest.json'
            manifest_path.write_text(__import__('json').dumps({'t1':[{'title':'Temple','thumb':'./assets/photos/t1-1.jpg','page':'https://commons.wikimedia.org/wiki/File:Temple.jpg','author':'A','license':'CC BY-SA'}], '_meta':{'lastAttempt':{}}}), encoding='utf-8')
            with patch.object(downloader, 'DIST', root), patch.object(downloader, 'PHOTO_DIR', photo_dir), patch.object(downloader, 'MANIFEST_PATH', manifest_path), patch.object(downloader, 'PLACES', [{'id':'t1','name':'Temple','area':'Kyoto'}]), patch.object(downloader, 'search_images', side_effect=AssertionError('should not query Commons')):
                result = downloader.build()
            self.assertEqual(result, 0)
            data = __import__('json').loads(manifest_path.read_text(encoding='utf-8'))
            self.assertEqual(len(data['t1']), 1)

    def test_recent_missing_search_is_in_cooldown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            photo_dir = root / 'assets' / 'photos'
            photo_dir.mkdir(parents=True)
            manifest_path = photo_dir / 'manifest.json'
            now = datetime.now(timezone.utc).isoformat()
            manifest_path.write_text(__import__('json').dumps({'t9':[], '_meta':{'lastAttempt':{'t9':now}}}), encoding='utf-8')
            with patch.object(downloader, 'DIST', root), patch.object(downloader, 'PHOTO_DIR', photo_dir), patch.object(downloader, 'MANIFEST_PATH', manifest_path), patch.object(downloader, 'PLACES', [{'id':'t9','name':'Mugiwara Store','area':'Tokyo'}]), patch.object(downloader, 'FORCE_MISSING_REFRESH', False), patch.object(downloader, 'search_images', side_effect=AssertionError('cooldown should skip Commons')):
                result = downloader.build()
            self.assertEqual(result, 0)
            data = __import__('json').loads(manifest_path.read_text(encoding='utf-8'))
            self.assertEqual(data['t9'], [])

if __name__ == '__main__':
    unittest.main()
