import contextlib
import io
from pathlib import Path
import tempfile
import unittest
import breadcrumbs


class BreadcrumbTests(unittest.TestCase):
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
