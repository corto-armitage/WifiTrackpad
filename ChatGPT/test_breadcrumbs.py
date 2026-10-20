import contextlib
import io
import os
import json
from pathlib import Path
import tempfile
import unittest
import breadcrumbs


class BreadcrumbTests(unittest.TestCase):
    def test_default_persistent_receipt_and_printed_checksums(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'example.txt').write_bytes(b'abc')
            saved = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
            updated = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
            original = os.getcwd()
            try:
                os.chdir(root)
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(breadcrumbs.main(['record', '.']), 0)
                receipt = root / 'receipt.json'
                self.assertTrue(receipt.exists())
                self.assertIn(str(receipt), output.getvalue())
                self.assertIn(saved, output.getvalue())
                data = json.loads(receipt.read_text())
                self.assertEqual(data['files']['example.txt']['sha256'], saved)
                self.assertNotIn('receipt.json', data['files'])
                receipt_bytes = receipt.read_bytes()
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(breadcrumbs.main(['check']), 0)
                self.assertIn('MATCH example.txt', output.getvalue())
                self.assertIn(f'Current SHA-256: {saved}', output.getvalue())
                (root / 'example.txt').write_bytes(b'')
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(breadcrumbs.main(['check']), 1)
                self.assertIn(f'Saved SHA-256: {saved}', output.getvalue())
                self.assertIn(f'Current SHA-256: {updated}', output.getvalue())
                self.assertEqual(receipt.read_bytes(), receipt_bytes)
            finally:
                os.chdir(original)

    def test_detects_changes_even_when_size_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'edit.txt').write_text('cat')
            (root / 'remove.txt').write_text('gone')
            before = breadcrumbs.inventory(root)
            (root / 'edit.txt').write_text('dog')
            (root / 'remove.txt').unlink()
            (root / 'new.txt').write_text('hello')
            self.assertEqual(breadcrumbs.changes(before, breadcrumbs.inventory(root)),
                             {'added': ['new.txt'], 'removed': ['remove.txt'], 'changed': ['edit.txt']})

    def test_receipt_excludes_itself_and_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            root = Path(directory)
            (root / 'hello.txt').write_text('hello')
            receipt = root / 'receipt.json'
            self.assertEqual(breadcrumbs.main(['record', str(root), str(receipt)]), 0)
            self.assertEqual(breadcrumbs.main(['check', str(receipt)]), 0)
            self.assertEqual(breadcrumbs.main(['record', str(root), str(receipt)]), 2)
            (root / 'hello.txt').write_text('changed')
            self.assertEqual(breadcrumbs.main(['check', str(receipt)]), 1)

    def test_skips_dependency_folders(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.venv').mkdir()
            (root / '.venv' / 'hidden').write_text('skip')
            self.assertEqual(breadcrumbs.inventory(root)['files'], {})

    def test_compares_copy(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            for folder in (first, second):
                (Path(folder) / 'same.txt').write_text('same')
            self.assertFalse(any(breadcrumbs.changes(breadcrumbs.inventory(first), breadcrumbs.inventory(second)).values()))


if __name__ == '__main__':
    unittest.main()
