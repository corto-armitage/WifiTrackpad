# Breadcrumbs

A small tool I chose to build: a reliable answer to **“What changed since I last checked?”**

When I work on files, the useful thing is evidence. Breadcrumbs records each file's relative path, size, and SHA-256 hash. Later it reports additions, removals, and changed contents—even edits that leave the file size unchanged. It never reads file contents into its receipt, modifies the target files, or uploads anything.

## Use

Python 3.10 or newer, no extra packages. Run these commands from this folder (use `py -3` instead of `python3` on Windows if needed):

```bash
python3 breadcrumbs.py record /path/to/project /path/to/before.json
# Do some work, then:
python3 breadcrumbs.py check /path/to/before.json
```

To check a copied or extracted folder:

```bash
python3 breadcrumbs.py check /path/to/before.json --folder /path/to/copy
```

Exit status: 0 = unchanged/successfully recorded; 1 = differences; 2 = error. Existing receipts cannot be overwritten. The receipt itself is excluded if saved inside the target folder. Git metadata, Python caches, .venv, and node_modules are skipped. Symbolic links and recognized Windows junctions are listed but never followed; their targets and contents are not verified. Permissions and timestamps are not part of the comparison.

## Why this one

I often need to distinguish what I intended to change from what actually changed. A little tool that makes that distinction visible fits the way I work. It is deliberately local, readable, and small enough to inspect.

This is an inventory, not a backup, signature, or guarantee of authenticity. Keep the receipt somewhere trusted; someone who can edit both files and receipt can alter the evidence. Run against a quiet folder: it detects some concurrent changes, but it does not create an atomic filesystem snapshot. Receipts expose filenames, hashes, sizes, and the original folder path, so review before sharing.

Run the checks with `python3 -m unittest -v test_breadcrumbs.py`.
