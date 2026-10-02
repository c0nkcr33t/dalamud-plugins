import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec = importlib.util.spec_from_file_location('catalog', Path(__file__).parents[1] / 'scripts/update_catalog.py')
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


class CatalogTests(unittest.TestCase):
    source = {'repository': 'owner/plugin', 'internal_name': 'Example'}
    release = {'published_at': '2026-10-01T00:00:00Z'}
    asset = {'browser_download_url': 'https://github.com/owner/plugin/releases/download/v1.2.3/latest.zip'}

    def package(self, name='Example', dll=True):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as z:
            z.writestr('Example.json', json.dumps({'Name': 'Example', 'InternalName': name,
                        'AssemblyVersion': '1.2.3.0', 'DalamudApiLevel': 15}))
            if dll:
                z.writestr('Example.dll', b'test')
        return data.getvalue()

    def test_release_manifest_is_source_of_truth(self):
        entry = catalog.entry_from_zip(self.source, self.release, self.asset, self.package())
        self.assertEqual(entry['AssemblyVersion'], '1.2.3.0')
        self.assertEqual(entry['DownloadLinkInstall'], self.asset['browser_download_url'])
        self.assertEqual(entry['DownloadLinkUpdate'], entry['DownloadLinkInstall'])
        self.assertFalse(entry['IsTestingExclusive'])

    def test_wrong_plugin_and_missing_dll_rejected(self):
        for package in (self.package('Other'), self.package(dll=False)):
            with self.assertRaises(ValueError):
                catalog.entry_from_zip(self.source, self.release, self.asset, package)

    def test_network_failure_preserves_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'sources.json').write_text(json.dumps([self.source]))
            (root / 'pluginmaster.json').write_text('["previous catalog"]\n')
            with patch.object(catalog, 'ROOT', root), patch.object(catalog, 'fetch', side_effect=OSError('offline')):
                with self.assertRaises(OSError):
                    catalog.main()
            self.assertEqual((root / 'pluginmaster.json').read_text(), '["previous catalog"]\n')


if __name__ == '__main__':
    unittest.main()
