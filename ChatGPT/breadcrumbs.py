"""Record a folder, then see what changed. Python 3.10+, no dependencies."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

SKIP = {'.git', '__pycache__', '.venv', 'node_modules'}


def inventory(root, excluded=()):
    root = Path(root).absolute()
    if root.is_symlink() or (hasattr(root, 'is_junction') and root.is_junction()):
        raise ValueError('Choose a real folder rather than a link or junction.')
    if not root.is_dir():
        raise ValueError('The target must be a folder.')
    excluded = {Path(p).absolute() for p in excluded}
    files, links = {}, []

    def visit(folder):
        for path in sorted(folder.iterdir()):
            # Never follow links: the inventory stays inside the chosen tree.
            relative = path.relative_to(root).as_posix()
            if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                links.append(relative)
            elif path.name in SKIP or path.absolute() in excluded:
                continue
            elif path.is_dir():
                visit(path)
            elif path.is_file():
                before = path.stat()
                digest = hashlib.sha256()
                with path.open('rb') as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                        digest.update(chunk)
                after = path.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    raise ValueError(f'File changed during reading: {relative}; retry when the folder is idle.')
                files[relative] = {'bytes': after.st_size, 'sha256': digest.hexdigest()}
    visit(root)
    return {'format': 1, 'root': str(root), 'files': files, 'skipped_links': links}


def changes(before, after):
    old, new = before['files'], after['files']
    return {
        'added': sorted(new.keys() - old.keys()),
        'removed': sorted(old.keys() - new.keys()),
        'changed': sorted(name for name in old.keys() & new.keys() if old[name] != new[name]),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    record = commands.add_parser('record', help='Save hashes; refuses to overwrite an existing receipt')
    record.add_argument('folder', type=Path)
    record.add_argument('receipt', type=Path)
    check = commands.add_parser('check', help='Compare with a saved receipt; exit 1 if changed')
    check.add_argument('receipt', type=Path)
    check.add_argument('--folder', type=Path, help='Compare a copy in a different folder')
    args = parser.parse_args(argv)
    try:
        receipt = args.receipt.absolute()
        if args.command == 'record':
            data = inventory(args.folder, [receipt])
            # Exclusive creation protects previous evidence from accidental overwrite.
            with receipt.open('x', encoding='utf-8') as stream:
                json.dump(data, stream, indent=2, ensure_ascii=False)
                stream.write('\n')
            print(f'Recorded {len(data["files"])} files. Skipped {len(data["skipped_links"])} links.')
            return 0
        before = json.loads(receipt.read_text(encoding='utf-8'))
        if before.get('format') != 1 or not isinstance(before.get('files'), dict):
            raise ValueError('Unsupported or invalid receipt.')
        after = inventory(args.folder or before['root'], [receipt])
        result = changes(before, after)
        for kind, names in result.items():
            for name in names:
                print(f'{kind.upper():7} {name}')
        if after['skipped_links']:
            print('Skipped links (contents were not checked): ' + ', '.join(after['skipped_links']))
        different = any(result.values()) or before.get('skipped_links', []) != after['skipped_links']
        if not different:
            print(f'No changes in {len(after["files"])} recorded files.')
        elif not any(result.values()):
            print('The list of skipped links changed.')
        return int(different)
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        print(f'Breadcrumbs: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
