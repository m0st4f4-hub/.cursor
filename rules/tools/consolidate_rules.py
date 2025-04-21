import argparse
import os
import glob
from pathlib import Path

def consolidate_rules(rules_dir, output_file, exclude_patterns=None, include_header=True):
    """
    Scans a directory recursively for .mdc files and consolidates their content
    into a single output Markdown file.

    Args:
        rules_dir (str): Path to the directory containing the rule files.
        output_file (str): Path to the output Markdown file.
        exclude_patterns (list[str], optional): List of glob patterns to exclude.
        include_header (bool, optional): Whether to include headers for each file.
    """
    rules_dir_path = Path(rules_dir)
    output_file_path = Path(output_file)
    all_mdc_files = set(rules_dir_path.rglob('*.mdc'))

    # Filter out excluded files
    excluded_files = set()
    if exclude_patterns:
        for pattern in exclude_patterns:
            # Adjust pattern for rglob compatibility if needed
            # Basic implementation: check absolute paths against patterns
            abs_pattern = rules_dir_path.resolve() / pattern
            try:
                # Use glob for potentially complex patterns within the rules_dir
                # This might need refinement depending on pattern complexity
                for excluded_path in rules_dir_path.glob(pattern):
                     excluded_files.add(excluded_path.resolve())
                # Also consider patterns matching files directly found by rglob
                for mdc_file in all_mdc_files:
                    if mdc_file.match(pattern):
                         excluded_files.add(mdc_file.resolve())
            except Exception as e:
                print(f"Warning: Could not process exclude pattern '{pattern}': {e}")


    mdc_files_to_process = sorted([
        f for f in all_mdc_files if f.resolve() not in excluded_files
    ])

    print(f"Found {len(mdc_files_to_process)} .mdc files to consolidate.")
    if excluded_files:
        print(f"Excluded {len(excluded_files)} files based on patterns.")

    try:
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            outfile.write(f"# Consolidated Rules from: {rules_dir_path.resolve()}\n\n")
            for file_path in mdc_files_to_process:
                relative_path = file_path.relative_to(rules_dir_path)
                print(f"Processing: {relative_path}")
                if include_header:
                    outfile.write(f"## Source: `{relative_path}`\n\n")
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                        outfile.write("\n\n---\n\n") # Separator
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
                    outfile.write(f"## Source: `{relative_path}`\n\n")
                    outfile.write(f"*Error reading file: {e}*\n\n")
                    outfile.write("---\n\n")

        print(f"Successfully consolidated rules into: {output_file_path.resolve()}")

    except Exception as e:
        print(f"Error writing to output file {output_file_path}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Consolidate .mdc rule files from a directory into a single Markdown file."
    )
    parser.add_argument(
        "--output_file",
        required=True,
        help="Path to the output Markdown file."
    )
    parser.add_argument(
        "--rules_dir",
        default=".cursor/rules",
        help="Directory containing the .mdc rule files (default: .cursor/rules)."
    )
    parser.add_argument(
        "--exclude_patterns",
        help="Comma-separated list of glob patterns to exclude files/directories.",
        default=None
    )
    parser.add_argument(
        "--include_header",
        type=lambda x: (str(x).lower() == 'true'), # Case-insensitive boolean parsing
        default=True,
        help="Include a header for each source file in the output (default: True)."
    )

    args = parser.parse_args()

    exclude_list = args.exclude_patterns.split(',') if args.exclude_patterns else None

    consolidate_rules(
        rules_dir=args.rules_dir,
        output_file=args.output_file,
        exclude_patterns=exclude_list,
        include_header=args.include_header
    ) 