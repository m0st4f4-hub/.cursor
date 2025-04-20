import os

# Configuration
ROOT_DIR = "."  # Set to your project root
OUTPUT_FILE = "full_code.txt"

EXCLUDED_DIRS = {
    ".git" 
    # Only exclude the .git directory
}

EXCLUDED_FILES = {
    "full_code.txt", "consolidate_code.py" # Exclude the output file and the script itself
}

# INCLUDED_EXTENSIONS is removed as we want all files

def should_include_file(file_path):
    # Normalize path for comparison
    normalized_path = os.path.normpath(file_path)
    return os.path.basename(normalized_path) not in EXCLUDED_FILES

def is_excluded_dir(path):
    # Normalize path for comparison
    normalized_path = os.path.normpath(path)
    # Check if any part of the path matches an excluded directory name
    return any(excluded in normalized_path.split(os.sep) for excluded in EXCLUDED_DIRS)

def collect_files(base_dir):
    code_files = []
    for root, dirs, files in os.walk(base_dir, topdown=True):
        # Filter out excluded directories directly
        dirs[:] = [d for d in dirs if not is_excluded_dir(os.path.join(root, d))]
        
        for file in files:
            full_path = os.path.join(root, file)
            # Check if the directory containing the file is excluded (redundant but safe)
            if is_excluded_dir(root):
                continue
            if should_include_file(full_path):
                code_files.append(os.path.normpath(full_path)) # Normalize path before adding
    return sorted(code_files) # Sort files alphabetically by path

def write_all_code_to_file(file_list, output_path):
    with open(output_path, "w", encoding="utf-8") as output:
        last_dir = None
        for path in file_list:
            # Normalize path for display
            display_path = os.path.normpath(path)
            current_dir = os.path.dirname(display_path)

            # Optionally add a comment when the directory changes
            if last_dir is not None and current_dir != last_dir:
                 output.write(f"\n# >>> Entering Directory: {current_dir}\n\n")
            elif last_dir is None and current_dir != '.': # Avoid printing for root unless it's the only dir
                 output.write(f"# >>> Entering Directory: {current_dir if current_dir else '.'}\n\n")

            output.write(f"# ======================\n")
            output.write(f"# File: {display_path}\n")
            output.write(f"# ======================\n\n")
            try:
                # Try reading as text first, fallback for binary/unsupported encodings
                try:
                    with open(path, "r", encoding="utf-8", errors='strict') as f: 
                        output.write(f.read())
                except UnicodeDecodeError:
                    output.write(f"# --- BINARY FILE or UNSUPPORTED ENCODING ---\n")
            except Exception as e:
                output.write(f"# ERROR READING FILE: {e}")
            output.write("\n\n")
            last_dir = current_dir if current_dir else '.' # Handle root directory case

if __name__ == "__main__":
    files = collect_files(ROOT_DIR)
    write_all_code_to_file(files, OUTPUT_FILE)
    print(f"✅ Consolidated {len(files)} files into {OUTPUT_FILE}") 