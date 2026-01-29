#!/usr/bin/env python3
"""
Path translator for VSP pipeline EC2 ↔ Linux container synchronization.

Translates paths between environments:
- EC2: /home/ubuntu, ~/
- Container: /workspace

Usage:
    python path_translator.py ec2-to-container input.sh output.sh
    python path_translator.py ec2-to-container input_dir/ output_dir/ --recursive
    python path_translator.py container-to-ec2 input.sh output.sh --dry-run
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

# Path mapping rules
# NOTE: Container $HOME is /root, EC2 $HOME is /home/ubuntu
# We only translate HARDCODED paths, not $HOME variable references
# The pipeline scripts use EXPORT_ROOT which auto-detects environment
EC2_TO_CONTAINER = {
    '/home/ubuntu': '/workspace',
    '~/': '/workspace/',
    # Do NOT translate $HOME - it's environment-specific:
    # EC2: $HOME = /home/ubuntu, Container: $HOME = /root
}

CONTAINER_TO_EC2 = {
    '/workspace': '/home/ubuntu',
    # Do NOT translate $HOME - it's environment-specific
}


def translate_file(
    input_path: Path,
    output_path: Path,
    mappings: Dict[str, str],
    dry_run: bool = False
) -> Tuple[int, List[str]]:
    """
    Translate paths in a file according to mapping rules.

    Args:
        input_path: Source file to translate
        output_path: Destination file path
        mappings: Dictionary of old_path -> new_path mappings
        dry_run: If True, don't write output file (just show changes)

    Returns:
        Tuple of (num_changes, list_of_changed_lines)
    """
    with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    changes = []
    new_lines = []

    for i, line in enumerate(lines, 1):
        new_line = line
        for old, new in mappings.items():
            if old in line:
                # Avoid replacing paths inside quotes if they're in comments
                # This is a simple heuristic - we replace all occurrences
                new_line = new_line.replace(old, new)
                changes.append(f"Line {i}: {old} → {new}")
        new_lines.append(new_line)

    if not dry_run and changes:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return len(changes), changes


def translate_directory_tree(
    src_dir: Path,
    dst_dir: Path,
    mappings: Dict[str, str],
    patterns: List[str] = None,
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Recursively translate all files matching patterns in a directory tree.

    Args:
        src_dir: Source directory root
        dst_dir: Destination directory root
        mappings: Path translation mappings
        patterns: Glob patterns to match files (default: ['*.sh', '*.py', '*.md'])
        dry_run: If True, don't write files

    Returns:
        Dictionary mapping relative file paths to number of changes
    """
    if patterns is None:
        patterns = ['*.sh', '*.py', '*.md']

    results = {}

    for pattern in patterns:
        for src_file in src_dir.rglob(pattern):
            # Skip if file is in .git directory
            if '.git' in src_file.parts:
                continue

            rel_path = src_file.relative_to(src_dir)
            dst_file = dst_dir / rel_path

            try:
                num_changes, _ = translate_file(src_file, dst_file, mappings, dry_run)
                if num_changes > 0:
                    results[str(rel_path)] = num_changes
            except Exception as e:
                print(f"Warning: Failed to translate {rel_path}: {e}", file=sys.stderr)

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Translate paths for VSP pipeline EC2 ↔ container sync',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Translate single file EC2 → container
  python path_translator.py ec2-to-container pipeline.sh /workspace/pipeline.sh

  # Translate directory recursively (dry-run to preview)
  python path_translator.py ec2-to-container src/ dst/ --recursive --dry-run

  # Reverse translation container → EC2
  python path_translator.py container-to-ec2 /workspace/script.sh /home/ubuntu/script.sh
"""
    )

    parser.add_argument(
        'direction',
        choices=['ec2-to-container', 'container-to-ec2'],
        help='Translation direction'
    )
    parser.add_argument(
        'input_path',
        type=Path,
        help='Source file or directory'
    )
    parser.add_argument(
        'output_path',
        type=Path,
        help='Destination file or directory'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show changes without writing files'
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Process directory recursively (for directories only)'
    )
    parser.add_argument(
        '--patterns',
        nargs='+',
        default=['*.sh', '*.py', '*.md'],
        help='File patterns to match in recursive mode (default: *.sh *.py *.md)'
    )

    args = parser.parse_args()

    # Select mappings based on direction
    mappings = EC2_TO_CONTAINER if args.direction == 'ec2-to-container' else CONTAINER_TO_EC2

    # Validate input path exists
    if not args.input_path.exists():
        print(f"Error: Input path does not exist: {args.input_path}", file=sys.stderr)
        sys.exit(1)

    # Process based on input type
    if args.recursive or args.input_path.is_dir():
        if not args.input_path.is_dir():
            print(f"Error: --recursive requires input to be a directory", file=sys.stderr)
            sys.exit(1)

        print(f"Translating directory tree: {args.input_path} → {args.output_path}")
        print(f"Direction: {args.direction}")
        print(f"Patterns: {args.patterns}")
        print(f"Dry-run: {args.dry_run}")
        print()

        results = translate_directory_tree(
            args.input_path,
            args.output_path,
            mappings,
            args.patterns,
            dry_run=args.dry_run
        )

        if results:
            print(f"Translated {len(results)} files:")
            for file_path, num_changes in sorted(results.items()):
                print(f"  {file_path}: {num_changes} changes")
        else:
            print("No files required translation (no path matches found)")

    else:
        # Single file translation
        print(f"Translating file: {args.input_path} → {args.output_path}")
        print(f"Direction: {args.direction}")
        print(f"Dry-run: {args.dry_run}")
        print()

        num_changes, changes = translate_file(
            args.input_path,
            args.output_path,
            mappings,
            dry_run=args.dry_run
        )

        if num_changes > 0:
            print(f"Translated {num_changes} paths")
            if args.dry_run:
                print("\nChanges preview:")
                for change in changes[:20]:  # Show first 20
                    print(f"  {change}")
                if len(changes) > 20:
                    print(f"  ... and {len(changes) - 20} more")
        else:
            print("No paths required translation")

    print()
    if args.dry_run:
        print("DRY RUN - No files were modified")
    else:
        print(f"Translation complete! Output written to: {args.output_path}")


if __name__ == '__main__':
    main()
