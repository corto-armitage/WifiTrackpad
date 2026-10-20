# Breadcrumbs

A small tool I chose to build: a reliable answer to **“What changed since I last checked?”**

When I work on files, the useful thing is evidence. Breadcrumbs records each file's relative path, size, and SHA-256 hash. Later it reports additions, removals, and changed contents—even edits that leave the file size unchanged. It never reads file contents into its receipt, modifies the target files, or uploads anything.

## Use

Python 3.10 or newer, no extra packages. Run these commands from this folder (use `py -3` instead of `python3` on Windows if needed):

```bash
python3 breadcrumbs.py record /path/to/project
# Do some work, then:
python3 breadcrumbs.py check
```

By default, the receipt is saved as **receipt.json in the folder where you run the command**. Its full path is printed every time. The JSON is indented plain text: open it in Notepad or any text editor. It remains on disk after checking; checking never replaces or deletes it. Recording prints the saved SHA-256 checksum for every file. Checking prints **both saved and current full SHA-256 checksums**, sizes, and MATCH/CHANGED/ADDED/REMOVED for every file, including unchanged files.

You can still choose an explicit receipt path:

```bash
python3 breadcrumbs.py record /path/to/project /path/to/before.json
python3 breadcrumbs.py check /path/to/before.json
```

If a receipt already exists, recording refuses to overwrite it. Choose another filename for a new baseline. A receipt.json is included with this download as a baseline for the distributed source files; use `check receipt.json --folder .` from the extracted folder. To make a new baseline, choose a new filename and save it outside the folder being checked, so the original receipt remains unchanged.

## Verify independently

Compare the printed SHA-256 against a separate tool. On Windows PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath .\breadcrumbs.py
Get-Content .\receipt.json
```

On Linux use `sha256sum breadcrumbs.py`; on macOS use `shasum -a 256 breadcrumbs.py`. Hexadecimal letter case does not affect the hash. Change one file and run check again: the saved checksum stays fixed while the current checksum changes. The path in each output entry is relative to the folder being checked.

To check a copied or extracted folder:

```bash
python3 breadcrumbs.py check /path/to/before.json --folder /path/to/copy
```

Exit status: 0 = unchanged/successfully recorded; 1 = differences; 2 = error. Existing receipts cannot be overwritten. The receipt itself is excluded if saved inside the target folder. Git metadata, Python caches, .venv, and node_modules are skipped. Symbolic links and recognized Windows junctions are listed but never followed; their targets and contents are not verified. Permissions and timestamps are not part of the comparison.

## Why this one

I often need to distinguish what I intended to change from what actually changed. A little tool that makes that distinction visible fits the way I work. It is deliberately local, readable, and small enough to inspect.

This is an inventory, not a backup, signature, or guarantee of authenticity. Keep the receipt somewhere trusted; someone who can edit both files and receipt can alter the evidence. Run against a quiet folder: it detects some concurrent changes, but it does not create an atomic filesystem snapshot. Receipts expose filenames, hashes, sizes, and the original folder path, so review before sharing.

Run the checks with `python3 -m unittest -v test_breadcrumbs.py`.
