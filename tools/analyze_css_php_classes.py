import argparse
import os
import re
import sys
from collections import defaultdict

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

def extract_php_classes(filepath, php_classes_set):
    \"\"\"Reads a PHP file and extracts potential class names from class attributes.\"\"\"
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading PHP file {filepath}: {e}", file=sys.stderr)
        return

    for match in PHP_CLASS_RE.finditer(content):
        attr_value = match.group(1).strip()
        # Basic split and filter - might need refinement for complex PHP
        potential_classes = attr_value.split()
        for pc in potential_classes:
            pc = pc.strip()
            # Filter out obvious non-classes (basic heuristic)
            if pc and '<' not in pc and '>' not in pc and '{' not in pc and '}' not in pc and '$' not in pc:
                 # Handle escaped quotes within the attribute if necessary (basic)
                pc = pc.replace('\\"', '').replace("\\'", '')
                if pc: # Ensure not empty after stripping/replacing
                    php_classes_set.add(pc)

def extract_css_classes(filepath, css_classes_set, css_dir, processed_files):
    \"\"\"
    Reads a CSS file, extracts defined class selectors, and handles @import.
    Avoids infinite recursion by tracking processed_files.
    \"\"\"
    abs_filepath = os.path.abspath(filepath)
    if abs_filepath in processed_files:
        return # Already processed, break recursion
    processed_files.add(abs_filepath)

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading CSS file {filepath}: {e}", file=sys.stderr)
        return

    # Handle @import statements first (simple relative path handling within css_dir)
    for line in lines:
        import_match = CSS_IMPORT_RE.search(line)
        if import_match:
            import_url = import_match.group('url').strip()
            # Very basic relative path handling - assumes import is relative to current file's dir
            # and within the initial css_dir. Does not handle URLs or complex paths.
            imported_filepath = os.path.normpath(os.path.join(os.path.dirname(filepath), import_url))

            # Check if the imported file is within the original css_dir to avoid going outside
            if os.path.abspath(imported_filepath).startswith(os.path.abspath(css_dir)):
                 if os.path.isfile(imported_filepath):
                     # print(f"Following import: {import_url} -> {imported_filepath}", file=sys.stderr)
                     extract_css_classes(imported_filepath, css_classes_set, css_dir, processed_files)
                 else:
                     print(f"Warning: Imported CSS file not found or path issue: {imported_filepath}", file=sys.stderr)


    # Extract class definitions from the current file
    content = "".join(lines) # Join lines for easier regex matching across lines potentially
    for match in CSS_SELECTOR_RE.finditer(content):
        class_name = match.group(1)
        if class_name:
            css_classes_set.add(class_name)


# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description='Analyze PHP and CSS files to find used and defined CSS classes.')
    parser.add_argument('--php-dir', required=True, help='Directory containing PHP files to scan.')
    parser.add_argument('--css-dir', required=True, help='Directory containing CSS files to scan (will follow imports within this dir).')
    parser.add_argument('--output-php', default='php_classes_used.txt', help='Output file for classes used in PHP.')
    parser.add_argument('--output-css', default='css_classes_defined.txt', help='Output file for classes defined in CSS.')
    parser.add_argument('--exclude-dirs', nargs='*', default=['node_modules', '.git', '.svn', '.vscode', '.cursor'], help='Directories to exclude from scanning.')

    args = parser.parse_args()

    if not os.path.isdir(args.php_dir):
        print(f"Error: PHP directory not found: {args.php_dir}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(args.css_dir):
        print(f"Error: CSS directory not found: {args.css_dir}", file=sys.stderr)
        sys.exit(1)

    php_classes_found = set()
    css_classes_defined = set()
    processed_css_files = set() # For handling imports

    print(f"Scanning PHP directory: {args.php_dir}")
    for root, dirs, files in os.walk(args.php_dir, topdown=True):
        # Modify dirs in-place to exclude specified directories
        dirs[:] = [d for d in dirs if d not in args.exclude_dirs]
        for file in files:
            if file.endswith(".php"):
                filepath = os.path.join(root, file)
                # print(f"Processing PHP: {filepath}", file=sys.stderr)
                extract_php_classes(filepath, php_classes_found)

    print(f"Scanning CSS directory: {args.css_dir}")
    for root, dirs, files in os.walk(args.css_dir, topdown=True):
         # Modify dirs in-place to exclude specified directories
        dirs[:] = [d for d in dirs if d not in args.exclude_dirs]
        for file in files:
            if file.endswith(".css"):
                filepath = os.path.join(root, file)
                # print(f"Processing CSS: {filepath}", file=sys.stderr)
                # Pass the base css_dir for import path validation
                extract_css_classes(filepath, css_classes_defined, args.css_dir, processed_css_files)

    print(f"Found {len(php_classes_found)} unique potential classes used in PHP.")
    print(f"Found {len(css_classes_defined)} unique classes defined in CSS.")

    # Write results to files
    try:
        with open(args.output_php, 'w', encoding='utf-8') as f_php:
            for cls in sorted(list(php_classes_found)):
                f_php.write(cls + '\\n')
        print(f"PHP classes written to {args.output_php}")
    except Exception as e:
        print(f"Error writing PHP output file {args.output_php}: {e}", file=sys.stderr)

    try:
        with open(args.output_css, 'w', encoding='utf-8') as f_css:
            for cls in sorted(list(css_classes_defined)):
                f_css.write(cls + '\\n')
        print(f"CSS classes written to {args.output_css}")
    except Exception as e:
        print(f"Error writing CSS output file {args.output_css}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main() 