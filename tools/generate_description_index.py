import os
import sys

# Add the parent directory (tools) to the Python path to import sync_rules
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# WORKSPACE_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..")) # ../ is rulesrepo dir
# sys.path.append(WORKSPACE_ROOT) # Add workspace root if sync_rules is there
sys.path.append(SCRIPT_DIR) # Add tools dir itself if sync_rules is treated as a module in it

# Attempt to import the parser from sync_rules.py
try:
    # from sync_rules import parse_md_metadata_and_content, SOURCE_DIR as RULE_SOURCE_DIR # Old
    from tools.rules_sync_lib.parser import parse_md_metadata_and_content
    from tools.rules_sync_lib.config import SOURCE_DIR as RULE_SOURCE_DIR
except ImportError as e:
    print(f"Error importing from tools.rules_sync_lib: {e}")
    print("Please ensure tools.rules_sync_lib is accessible in PYTHONPATH.")
    print(f"Current SCRIPT_DIR: {SCRIPT_DIR}")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)

def create_description_index():
    """Walks through RULE_SOURCE_DIR, parses .md files, and prints an index of their descriptions."""
    description_index = {}
    print(f"Scanning for .md files in: {RULE_SOURCE_DIR}...")

    if not os.path.exists(RULE_SOURCE_DIR):
        print(f"Error: Source directory {RULE_SOURCE_DIR} does not exist.")
        return

    for root, _, files in os.walk(RULE_SOURCE_DIR):
        for file in files:
            if file.endswith(".md"):
                source_file_path = os.path.join(root, file)
                # dummy log_callback for the parser, as we don't have the GUI logger here
                def dummy_log(message):
                    pass # print(f"[Parser Log] {message}") # Uncomment for debugging parser

                metadata, _ = parse_md_metadata_and_content(source_file_path, dummy_log)
                
                description = ""
                if metadata.get('title'):
                    description = metadata['title']
                elif metadata.get('description'):
                    description = metadata['description']
                
                relative_path = os.path.relpath(source_file_path, RULE_SOURCE_DIR)
                description_index[relative_path] = description.strip()
    
    print("\n--- Description Index ---")
    if description_index:
        for file_path, desc in description_index.items():
            print(f"File: {file_path}\n  Description: {desc}\n")
    else:
        print("No .md files found or no descriptions could be extracted.")
    print("-------------------------")

if __name__ == "__main__":
    create_description_index() 