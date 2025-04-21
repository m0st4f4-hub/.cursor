import argparse
import os
import re
import sys
from collections import defaultdict
from typing import Set, List, Optional
from pathlib import Path

# --- Regular Expressions ---

# Find class="..." attributes in PHP/HTML, capture content within quotes
PHP_CLASS_RE = re.compile(r'''class\s*=\s*['"]([^'"]+)['"]''', re.IGNORECASE)

# Find CSS class selectors (simplified: starts with '.', allows _, -, alphanumeric)
# Handles basic pseudo-classes/elements by stripping them
CSS_SELECTOR_RE = re.compile(r'''
    \.                  # Starts with a dot
    ([_a-zA-Z0-9-]+)    # The class name itself (group 1)
    (?:[:\[\(]|$)       # Optionally followed by :, [, (, or end of line/selector part
''', re.VERBOSE)

# Find CSS @import url(...) statements
CSS_IMPORT_RE = re.compile(r'@import\s+url\((["\']?)(?P<url>.*?)\1\)', re.IGNORECASE)

# --- Helper Functions ---

def extract_php_classes(filepath: str, php_classes_set: Set[str]) -> None:
    """Reads a PHP file and extracts potential class names from class attributes."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading PHP file {filepath}: {e}", file=sys.stderr)
        return

    for match in PHP_CLASS_RE.finditer(content):
        attr_value = match.group(1).strip()
        potential_classes = attr_value.split()
        for pc in potential_classes:
            pc = pc.strip()
            # Filter out obvious non-classes (basic heuristic)
            if pc and not any(char in pc for char in '<>{}'):
                # Handle escaped quotes within the attribute
                pc = pc.replace('\\"', '').replace("\\'", '')
                if pc:  # Ensure not empty after stripping/replacing
                    php_classes_set.add(pc)

def extract_css_classes(filepath: str, css_classes_set: Set[str], css_dir: str, processed_files: Set[str]) -> None:
    """
    Reads a CSS file, extracts defined class selectors, and handles @import.
    Avoids infinite recursion by tracking processed_files.
    """
    abs_filepath = os.path.abspath(filepath)
    if abs_filepath in processed_files:
        return  # Already processed, break recursion
    processed_files.add(abs_filepath)

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading CSS file {filepath}: {e}", file=sys.stderr)
        return

    # Handle @import statements first
    for import_match in CSS_IMPORT_RE.finditer(content):
        import_url = import_match.group('url').strip()
        imported_filepath = os.path.normpath(os.path.join(os.path.dirname(filepath), import_url))

        # Check if the imported file is within the original css_dir
        if os.path.abspath(imported_filepath).startswith(os.path.abspath(css_dir)):
            if os.path.isfile(imported_filepath):
                extract_css_classes(imported_filepath, css_classes_set, css_dir, processed_files)
            else:
                print(f"Warning: Imported CSS file not found: {imported_filepath}", file=sys.stderr)

    # Extract class definitions from the current file
    for match in CSS_SELECTOR_RE.finditer(content):
        class_name = match.group(1)
        if class_name:
            css_classes_set.add(class_name)

def scan_directory(directory: str, file_extension: str, exclude_dirs: List[str], 
                  process_func: callable, *args) -> None:
    """Helper function to scan a directory and process files with given extension."""
    for root, dirs, files in os.walk(directory, topdown=True):
        # Modify dirs in-place to exclude specified directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith(file_extension):
                filepath = os.path.join(root, file)
                process_func(filepath, *args)

def write_results(filename: str, data: Set[str]) -> None:
    """Write sorted results to a file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(f"{cls}\n" for cls in sorted(data))
        print(f"Results written to {filename}")
    except Exception as e:
        print(f"Error writing to {filename}: {e}", file=sys.stderr)

def main() -> None:
    parser = argparse.ArgumentParser(description='Analyze PHP and CSS files to find used and defined CSS classes.')
    parser.add_argument('--php-dir', required=True, help='Directory containing PHP files to scan.')
    parser.add_argument('--css-dir', required=True, help='Directory containing CSS files to scan (will follow imports within this dir).')
    parser.add_argument('--output-php', default='php_classes_used.txt', help='Output file for classes used in PHP.')
    parser.add_argument('--output-css', default='css_classes_defined.txt', help='Output file for classes defined in CSS.')
    parser.add_argument('--exclude-dirs', nargs='*', 
                       default=['node_modules', '.git', '.svn', '.vscode', '.cursor'],
                       help='Directories to exclude from scanning.')

    args = parser.parse_args()

    # Validate directories
    for dir_name, dir_path in [('PHP', args.php_dir), ('CSS', args.css_dir)]:
        if not os.path.isdir(dir_path):
            print(f"Error: {dir_name} directory not found: {dir_path}", file=sys.stderr)
            sys.exit(1)

    php_classes_found: Set[str] = set()
    css_classes_defined: Set[str] = set()
    processed_css_files: Set[str] = set()

    print(f"Scanning PHP directory: {args.php_dir}")
    scan_directory(args.php_dir, '.php', args.exclude_dirs, extract_php_classes, php_classes_found)

    print(f"Scanning CSS directory: {args.css_dir}")
    scan_directory(args.css_dir, '.css', args.exclude_dirs, extract_css_classes, 
                  css_classes_defined, args.css_dir, processed_css_files)

    print(f"Found {len(php_classes_found)} unique potential classes used in PHP.")
    print(f"Found {len(css_classes_defined)} unique classes defined in CSS.")

    # Write results to files
    write_results(args.output_php, php_classes_found)
    write_results(args.output_css, css_classes_defined)

if __name__ == "__main__":
    main()