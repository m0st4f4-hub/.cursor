import time
import os
import shutil
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
import queue # For thread-safe communication
import sys # Moved here as it's used for stdout redirection
import glob
import frontmatter # For handling YAML frontmatter
import yaml # For YAML processing
import traceback # Added for more detailed error logging in convert_md_to_mdc

# Configuration: These paths are relative to the script's parent directory (workspace root)
# Assumes the script is in a 'tools' subdirectory of the workspace root.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

SOURCE_DIR_NAME = "rules-md"
TARGET_DIR_1_NAME = "rules"
TARGET_DIR_2_NAME = ".cursor/rules"

SOURCE_DIR = os.path.join(WORKSPACE_ROOT, SOURCE_DIR_NAME)
TARGET_DIR_1 = os.path.join(WORKSPACE_ROOT, TARGET_DIR_1_NAME)
TARGET_DIR_2 = os.path.join(WORKSPACE_ROOT, TARGET_DIR_2_NAME)

COMMIT_MESSAGE_PREFIX = "Chore: Auto-sync rule changes"
DEBOUNCE_PERIOD = 2.0  # seconds

# --- Helper class to redirect stdout to GUI ---
class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.queue = queue.Queue()
        self.text_widget.after(100, self._process_queue)

    def write(self, string):
        self.queue.put(string)

    def _process_queue(self):
        try:
            while True:
                string = self.queue.get_nowait()
                self.text_widget.insert(tk.END, string)
                self.text_widget.see(tk.END) # Scroll to the end
        except queue.Empty:
            pass
        self.text_widget.after(100, self._process_queue)

    def flush(self):
        # Tkinter Text widget auto-flushes, but good to have for compatibility
        pass

def parse_md_metadata_and_content(source_path, log_callback):
    """
    Parses metadata and content from an .md file.
    Metadata is expected as commented YAML at the beginning of the file.
    Example:
    # ruleId: my-rule
    # ruleType: Linter
    # title: My Linter Rule
    --- (optional separator)
    This is the rule body.
    """
    metadata = {}
    content_lines = []
    in_metadata_block = True

    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        metadata_yaml_str = ""
        content_start_index = 0

        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if in_metadata_block:
                if stripped_line.startswith("# ") and ':' in stripped_line:
                    # Potential metadata line
                    try:
                        # Attempt to extract key: value from commented line
                        key_value_part = stripped_line[2:] # Remove "# "
                        if ':' in key_value_part:
                             metadata_yaml_str += key_value_part + "\n"
                             content_start_index = i + 1
                        else: # Not a valid key:value, assume end of metadata
                            in_metadata_block = False
                            content_lines.append(line)
                    except Exception: # Not a valid key:value, assume end of metadata
                        in_metadata_block = False
                        content_lines.append(line)
                elif stripped_line == "# ---" or stripped_line == "---": # Common frontmatter separator
                    content_start_index = i + 1
                    in_metadata_block = False # Explicitly end metadata block
                    # Don't add the separator to content_lines if it's just for metadata
                elif not stripped_line.startswith("#"): # Non-comment line, definitely end of metadata
                    in_metadata_block = False
                    content_lines.append(line)
                else: # Comment line but not metadata, treat as content or separator
                    content_start_index = i + 1 # Ensure we capture this line if metadata block was empty
                    in_metadata_block = False
                    content_lines.append(line)
            else:
                content_lines.append(line)
        
        if not metadata_yaml_str and lines: # Check if there was any metadata string formed
            # If no commented metadata found, try to parse as standard frontmatter
            try:
                post = frontmatter.load(source_path)
                metadata = post.metadata
                content_lines = post.content.splitlines(True) # Keep line endings
            except Exception as e_fm:
                log_callback(f"No commented metadata and failed to parse standard frontmatter for {source_path}: {e_fm}. Treating all as content.")
                metadata = {}
                content_lines = lines # All lines are content
        elif metadata_yaml_str:
            try:
                parsed_yaml = yaml.safe_load(metadata_yaml_str)
                if isinstance(parsed_yaml, dict):
                    metadata = parsed_yaml
                else:
                    log_callback(f"Warning: Parsed commented metadata for {source_path} is not a dictionary. Treating as no metadata.")
                    # content_lines were already appended from lines[content_start_index:] if metadata_yaml_str was populated
                    # but if parsing failed, we need to ensure content_lines are correct
                    content_lines = lines[content_start_index:]

            except yaml.YAMLError as e_yaml:
                log_callback(f"YAML parsing error for commented metadata in {source_path}: {e_yaml}. Treating as no metadata.")
                # content_lines were already appended from lines[content_start_index:]
                content_lines = lines[content_start_index:]

        # If after all attempts, content_lines are empty but lines are not, re-evaluate
        if not content_lines and lines and not metadata: # Check if metadata is also empty
             content_lines = lines # Default to all lines as content if metadata parsing failed or was empty

        # Attempt to derive description from content if not in metadata
        if not metadata.get('title') and not metadata.get('description'):
            derived_desc_from_content = ""
            temp_content = "".join(content_lines)
            # Try to find H1
            for line in content_lines:
                stripped_content_line = line.strip()
                if stripped_content_line.startswith("# "):
                    derived_desc_from_content = stripped_content_line[2:].strip()
                    break
            # If no H1, try to find the first non-empty paragraph line
            if not derived_desc_from_content:
                for line in content_lines:
                    stripped_content_line = line.strip()
                    if stripped_content_line and \
                       not stripped_content_line.startswith('>') and \
                       not stripped_content_line.startswith('-') and \
                       not stripped_content_line.startswith('*') and \
                       not stripped_content_line.startswith('+') and \
                       not stripped_content_line.startswith('#') and \
                       not stripped_content_line.startswith('|') and \
                       not stripped_content_line.startswith('`') and \
                       not stripped_content_line.startswith('='):
                        derived_desc_from_content = stripped_content_line
                        break # Take the first such line
            if derived_desc_from_content:
                metadata['description'] = derived_desc_from_content # Store it for convert_md_to_mdc

        return metadata, "".join(content_lines)

    except Exception as e:
        log_callback(f"Error reading or parsing metadata from {source_path}: {e}")
        return {}, "".join(lines) # Return empty metadata and all lines as content on error

def convert_md_to_mdc(source_path, dest_parent_dir_1, dest_parent_dir_2, log_callback):
    """
    Converts an .md file to .mdc format by extracting metadata,
    transforming it into a new YAML frontmatter, and appending the original content.
    Places it in target directories, maintaining the subdirectory structure.
    """
    if not source_path.endswith(".md"):
        log_callback(f"Skipping non-md file: {source_path}")
        return None, None

    try:
        original_metadata, original_content = parse_md_metadata_and_content(source_path, log_callback)
        
        # Construct new .mdc frontmatter
        mdc_frontmatter = {}
        if 'ruleId' in original_metadata:
            mdc_frontmatter['ruleId'] = original_metadata['ruleId']
        if 'ruleType' in original_metadata:
            mdc_frontmatter['ruleType'] = original_metadata['ruleType']
        
        # Description logic
        if 'title' in original_metadata and original_metadata['title']:
            final_description = original_metadata['title']
        elif 'description' in original_metadata and original_metadata['description']:
            final_description = original_metadata['description']
        else:
            final_description = "" # Default to empty string if no description found

        mdc_frontmatter['description'] = final_description
        
        mdc_frontmatter['globs'] = original_metadata.get('globs', [])
        
        # Determine alwaysApply based on filename
        core_always_apply_files = [
            "concepts.md", "entrypoint.md", "init.md", 
            "loop.md", "protocol.md", "roles.md", "system.md"
        ]
        source_filename = os.path.basename(source_path)
        if source_filename in core_always_apply_files:
            mdc_frontmatter['alwaysApply'] = True
        else:
            mdc_frontmatter['alwaysApply'] = original_metadata.get('alwaysApply', False)

        # Process content: replace .md with .mdc
        processed_content = original_content.replace(".md", ".mdc")
        content_links_updated = original_content != processed_content

        # Create a frontmatter.Post object
        mdc_post = frontmatter.Post(processed_content.strip()) # Strip content to avoid leading/trailing newlines from parsing
        mdc_post.metadata = mdc_frontmatter
        
        # Get the string representation with new frontmatter
        mdc_output_content = frontmatter.dumps(mdc_post)
        # Ensure there's a newline after the frontmatter before the content if content exists
        if original_content.strip():
             mdc_output_content = mdc_output_content.replace("---", "---\n", 1)

        # --- Destination path calculations (same as before) ---
        mdc_filename = os.path.basename(source_path)[:-3] + ".mdc"
        relative_dir_path = os.path.relpath(os.path.dirname(source_path), SOURCE_DIR)
        if relative_dir_path == ".":
            relative_dir_path = ""

        dest_subdir_1 = os.path.join(dest_parent_dir_1, relative_dir_path)
        dest_subdir_2 = os.path.join(dest_parent_dir_2, relative_dir_path)

        os.makedirs(dest_subdir_1, exist_ok=True)
        os.makedirs(dest_subdir_2, exist_ok=True)

        mdc_dest_path_1 = os.path.join(dest_subdir_1, mdc_filename)
        mdc_dest_path_2 = os.path.join(dest_subdir_2, mdc_filename)
        # --- End of destination path calculations ---

        log_callback(f"Processing {source_path} for .mdc conversion")
        with open(mdc_dest_path_1, 'w', encoding='utf-8') as f_out:
            f_out.write(mdc_output_content)
        log_callback(f"  -> Converted and written to {mdc_dest_path_1}")
        
        with open(mdc_dest_path_2, 'w', encoding='utf-8') as f_out:
            f_out.write(mdc_output_content)
        log_callback(f"  -> Converted and written to {mdc_dest_path_2}")
        
        return {
            "mdc_path_1": mdc_dest_path_1,
            "mdc_path_2": mdc_dest_path_2,
            "converted": True,
            "source_filename": source_filename, # for checking core status later
            "core_always_apply_set": source_filename in core_always_apply_files,
            "placeholder_description_used": mdc_frontmatter['description'] == "Description to be filled",
            "content_links_updated": content_links_updated
        }
        
    except Exception as e:
        log_callback(f"Error converting {source_path} to .mdc: {e}")
        log_callback(traceback.format_exc())
        return {"converted": False, "source_filename": os.path.basename(source_path)}

def run_git_command(command, log_callback, cwd=None, suppress_not_found=False):
    """Run a git command with proper git directory and work tree settings"""
    # Convert command list to string if it's a list
    if isinstance(command, list):
        command = ' '.join(command)
    
    git_base = f'git --git-dir={os.path.join(WORKSPACE_ROOT, ".git")} --work-tree={WORKSPACE_ROOT}'
    full_command = f'{git_base} {command}'
    try:
        result = subprocess.run(
            full_command,
            shell=True,
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True
        )
        log_callback(f"Running git command: '{full_command}' in {WORKSPACE_ROOT}")
        
        if result.returncode != 0:
            # If we're suppressing "did not match" errors and that's what happened, don't log it as an error
            if suppress_not_found and "did not match any files" in result.stderr:
                log_callback(f"Note: {result.stderr.strip()} (expected, continuing)")
                return True  # Return success in this case
            
            log_callback(f"Error running git command: '{full_command}'")
            log_callback(f"Return code: {result.returncode}")
            if result.stderr:
                log_callback(f"Stderr: {result.stderr}")
        elif result.stdout:
            log_callback(f"Git stdout: {result.stdout}")
        if result.stderr and 'warning:' in result.stderr:
            log_callback(f"Git stderr: {result.stderr}")
            
        return result.returncode == 0
    except Exception as e:
        log_callback(f"Exception running git command: {str(e)}")
        return False

def commit_and_push_changes(abs_mdc_paths_for_git, commit_message, log_callback):
    """Adds, commits, and pushes changes to GitHub."""
    if not abs_mdc_paths_for_git:
        log_callback("No valid files changed to commit.")
        return

    log_callback(f"Preparing to commit changes for {len(abs_mdc_paths_for_git)} file(s) to git.")
    
    normal_add_files_relative = []
    force_add_files_relative = []

    abs_target_dir_1 = os.path.abspath(TARGET_DIR_1)
    abs_target_dir_2 = os.path.abspath(TARGET_DIR_2)

    for abs_f_path in abs_mdc_paths_for_git:
        f_rel = os.path.relpath(abs_f_path, WORKSPACE_ROOT)
        # Normalize paths for reliable comparison, especially on Windows
        normalized_abs_f_path = os.path.normpath(abs_f_path)
        normalized_abs_target_dir_1 = os.path.normpath(abs_target_dir_1)
        normalized_abs_target_dir_2 = os.path.normpath(abs_target_dir_2)

        if normalized_abs_f_path.startswith(normalized_abs_target_dir_2 + os.sep):
            force_add_files_relative.append(f_rel)
        elif normalized_abs_f_path.startswith(normalized_abs_target_dir_1 + os.sep):
            normal_add_files_relative.append(f_rel)
        else:
            # Fallback for files not in primary or secondary target dirs (should be rare)
            log_callback(f"Warning: File {f_rel} is not in expected target directories. Attempting normal add.")
            normal_add_files_relative.append(f_rel)

    all_adds_successful = True

    if normal_add_files_relative:
        files_str = '" "'.join(normal_add_files_relative)
        add_command_normal = f'add "{files_str}"'
        log_callback(f"Attempting to add {len(normal_add_files_relative)} file(s) normally: {', '.join(normal_add_files_relative)}")
        if not run_git_command(add_command_normal, log_callback, WORKSPACE_ROOT):
            log_callback(f"Failed to git add files: {', '.join(normal_add_files_relative)}.")
            all_adds_successful = False

    if force_add_files_relative:
        files_str = '" "'.join(force_add_files_relative)
        add_command_force = f'add -f "{files_str}"'
        log_callback(f"Attempting to force-add {len(force_add_files_relative)} file(s): {', '.join(force_add_files_relative)}")
        if not run_git_command(add_command_force, log_callback, WORKSPACE_ROOT):
            log_callback(f"Failed to git add -f files: {', '.join(force_add_files_relative)}.")
            all_adds_successful = False

    if not all_adds_successful:
        log_callback("One or more git add operations failed. Aborting commit and push.")
        return

    # Check if there are any staged changes before committing
    status_cmd = 'status --porcelain'
    try:
        result = subprocess.run(f'git {status_cmd}', cwd=WORKSPACE_ROOT, check=True, capture_output=True, text=True, shell=True)
        if not result.stdout.strip(): # No output means no staged changes
            log_callback("No changes staged for commit. Skipping commit and push.")
            return
        log_callback(f"Git status output (staged files):\n{result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        log_callback(f"Error running git status: {e.stderr}")
        log_callback("Could not verify staged changes. Aborting commit to be safe.")
        return
    except Exception as e:
        log_callback(f"An unexpected error occurred running git status: {e}")
        log_callback("Could not verify staged changes. Aborting commit to be safe.")
        return

    commit_cmd = f'commit -m "{commit_message}"'
    if not run_git_command(commit_cmd, log_callback, WORKSPACE_ROOT):
        log_callback("Failed to git commit changes. Aborting push.")
        return

    # Attempt to pull before pushing to integrate remote changes
    pull_cmd = 'pull'
    log_callback("Attempting to git pull to integrate remote changes...")
    if not run_git_command(pull_cmd, log_callback, WORKSPACE_ROOT):
        log_callback("Failed to git pull. Please resolve any conflicts manually and then push. Aborting automated push.")
        return

    push_cmd = 'push'
    if not run_git_command(push_cmd, log_callback, WORKSPACE_ROOT):
        log_callback("Failed to git push changes.")
        return

    log_callback(f"Successfully committed and pushed: {commit_message}")

# Utility: Delete all .mdc files in a directory (recursively)
def delete_all_mdc_files(target_dir, log_callback):
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.mdc'):
                try:
                    os.remove(os.path.join(root, file))
                    log_callback(f"Deleted: {os.path.join(root, file)}")
                except Exception as e:
                    log_callback(f"Error deleting {os.path.join(root, file)}: {e}")

# Utility: Ensure .gitignore contains required entries
def ensure_gitignore_entries(entries, log_callback):
    gitignore_path = os.path.join(WORKSPACE_ROOT, '.gitignore')
    try:
        if not os.path.exists(gitignore_path):
            with open(gitignore_path, 'w') as f:
                f.write('\n'.join(entries) + '\n')
            log_callback(f"Created .gitignore with required entries.")
            return
        with open(gitignore_path, 'r') as f:
            lines = f.read().splitlines()
        changed = False
        for entry in entries:
            if entry not in lines:
                lines.append(entry)
                changed = True
        if changed:
            with open(gitignore_path, 'w') as f:
                f.write('\n'.join(lines) + '\n')
            log_callback(f"Updated .gitignore with required entries.")
    except Exception as e:
        log_callback(f"Error updating .gitignore: {e}")

# Utility: Remove tracked files from git index for ignored folders
def remove_ignored_from_git_index(log_callback):
    """Remove tracked files from git index for ignored folders, silently ignoring 'did not match' errors"""
    for folder in ['.cursor', 'rules-md']:
        try:
            # First check if the folder is tracked
            tracked_cmd = f'ls-files "{folder}"'
            result = subprocess.run(
                f'git --git-dir={os.path.join(WORKSPACE_ROOT, ".git")} --work-tree={WORKSPACE_ROOT} {tracked_cmd}',
                shell=True,
                cwd=WORKSPACE_ROOT,
                capture_output=True,
                text=True
            )
            
            # Only try to remove if there are tracked files
            if result.stdout.strip():
                rm_cmd = f'rm -r --cached "{folder}"'
                run_git_command(rm_cmd, log_callback, WORKSPACE_ROOT, suppress_not_found=True)
            else:
                log_callback(f"Folder '{folder}' is not tracked in git - skipping removal")
        except Exception as e:
            # Silently ignore errors here
            pass

# Utility: Check if remote is set
def has_remote_origin(log_callback):
    """Check if remote origin is set"""
    try:
        remote_cmd = 'remote -v'
        if not run_git_command(remote_cmd, log_callback, WORKSPACE_ROOT):
            log_callback('No remote origin set. Please set remote to https://github.com/m0st4f4-hub/.cursor')
            return False
        return True
    except Exception as e:
        log_callback(f"Error checking remote: {e}")
        return False

# Main sync logic: delete, regenerate, commit/push

def full_sync_and_commit(log_callback):
    """
    Complete sync process: delete, regenerate, update gitignore, and commit/push
    """
    # 1. Delete all .mdc files in rules/ and .cursor/rules/
    for target in [TARGET_DIR_1, TARGET_DIR_2]:
        delete_all_mdc_files(target, log_callback)
    
    # 2. Regenerate all .mdc files in both targets from rules-md
    for root, _, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith('.md'):
                source_file_path = os.path.join(root, file)
                convert_md_to_mdc(source_file_path, TARGET_DIR_1, TARGET_DIR_2, log_callback)
    
    # 3. Ensure .gitignore is correct
    ensure_gitignore_entries(['.cursor/', 'rules-md/'], log_callback)
    
    # 4. Remove tracked files from .cursor/ and rules-md/
    remove_ignored_from_git_index(log_callback)
    
    # 5. Add/commit/push only rules/
    add_cmd = 'add -A "rules/"'
    run_git_command(add_cmd, log_callback, WORKSPACE_ROOT)
    
    # 6. Commit if there are changes
    status_cmd = 'status --porcelain "rules/"'
    try:
        result = subprocess.run(f'git {status_cmd}', cwd=WORKSPACE_ROOT, capture_output=True, text=True, check=True, shell=True)
        if result.stdout.strip():
            commit_cmd = f'commit -m "{COMMIT_MESSAGE_PREFIX}: Full sync"'
            if run_git_command(commit_cmd, log_callback, WORKSPACE_ROOT):
                # 7. Push if remote is set and commit was successful
                if has_remote_origin(log_callback):
                    push_cmd = 'push origin HEAD'
                    run_git_command(push_cmd, log_callback, WORKSPACE_ROOT)
        else:
            log_callback('No changes to commit in rules/.')
    except Exception as e:
        log_callback(f"Error checking git status or committing: {e}")

class ChangeHandler(FileSystemEventHandler):
    def __init__(self, app_instance):
        self.app = app_instance # Store the app instance
        self.last_event_time = 0
        self.changed_files_batch = set() # Store src_paths of .md files
        self.timeout_check_interval = DEBOUNCE_PERIOD / 2
        self.processing_lock = False

    def on_any_event(self, event):
        # We are interested in file creation or modification events for .md files
        if event.is_directory or not event.src_path.endswith(".md"):
            return
        
        # For created or modified files
        if event.event_type in ('created', 'modified'):
            self.app.log_message(f"Event detected: {event.event_type} - {event.src_path}")
            self.changed_files_batch.add(event.src_path)
            self.last_event_time = time.time()

    def check_and_process_batch(self):
        if self.processing_lock:
            return
            
        if self.changed_files_batch and (time.time() - self.last_event_time >= DEBOUNCE_PERIOD):
            self.processing_lock = True
            self.app._reset_batch_stats() # Reset stats for this new batch
            self.app.log_message(f"Debounce period ended ({DEBOUNCE_PERIOD}s). Processing batch of {len(self.changed_files_batch)} event(s).")
            
            current_batch = list(self.changed_files_batch)
            self.changed_files_batch.clear()
            
            all_generated_mdc_paths_abs = set()
            commit_file_basenames = []

            for src_path in current_batch:
                conversion_info = convert_md_to_mdc(src_path, TARGET_DIR_1, TARGET_DIR_2, self.app.log_message)
                self.app._update_conversion_stats(conversion_info)

                if conversion_info and conversion_info.get("converted"):
                    all_generated_mdc_paths_abs.add(src_path) 
                    commit_file_basenames.append(os.path.basename(conversion_info.get("source_filename", "unknown"))[:-3]) 

            if commit_file_basenames: 
                unique_file_basenames = sorted(list(set(commit_file_basenames)))
                commit_message = f"{COMMIT_MESSAGE_PREFIX}: Sync changes to {len(unique_file_basenames)} file(s)"
                if len(unique_file_basenames) > 3:
                    commit_message = f"{COMMIT_MESSAGE_PREFIX}: Sync changes to {len(unique_file_basenames)} files including {unique_file_basenames[0]}, etc."
                elif unique_file_basenames:
                    commit_message = f"{COMMIT_MESSAGE_PREFIX}: Sync {', '.join(unique_file_basenames)}"
                
                self.app.process_git_commit_batch(list(all_generated_mdc_paths_abs), commit_message)
            else:
                self.app.log_message("No files were successfully processed in this batch, or no changes warranting commit.")
            
            self.app._log_batch_summary("Watcher Batch") 
            self.processing_lock = False

def initial_scan_and_process_logic(log_callback, process_batch_callback):
    log_callback(f"Performing initial scan of {SOURCE_DIR}...")
    initial_mdc_files_to_commit_abs = set()
    initial_commit_file_basenames = []

    if not os.path.exists(SOURCE_DIR):
        log_callback(f"Source directory {SOURCE_DIR} does not exist. Skipping initial scan.")
        return

    for root, _, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith(".md"):
                source_file_path = os.path.join(root, file)
                mdc_path_1, mdc_path_2 = convert_md_to_mdc(source_file_path, TARGET_DIR_1, TARGET_DIR_2, log_callback)
                if mdc_path_1:
                    initial_mdc_files_to_commit_abs.add(os.path.abspath(mdc_path_1))
                    initial_commit_file_basenames.append(os.path.basename(mdc_path_1)[:-4])
                if mdc_path_2:
                    initial_mdc_files_to_commit_abs.add(os.path.abspath(mdc_path_2))

    if initial_mdc_files_to_commit_abs:
        unique_initial_file_basenames = sorted(list(set(initial_commit_file_basenames)))
        initial_commit_message = f"{COMMIT_MESSAGE_PREFIX}: Initial sync {', '.join(unique_initial_file_basenames)}"
        process_batch_callback(list(initial_mdc_files_to_commit_abs), initial_commit_message)
    else:
        log_callback("No .md files found for initial scan or no changes warranting commit.")

# --- Tkinter App ---
class RulesSyncApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rules Sync Tool")
        self.geometry("700x550") # Increased height slightly for stats

        self.observer = None
        self.watcher_thread = None
        self.stop_event = threading.Event()
        self.is_watching = False

        self._initialize_stats()
        self._setup_ui()
        self.original_stdout = sys.stdout # Save original stdout
        sys.stdout = StdoutRedirector(self.log_text) # Redirect stdout

        # Ensure target directories exist
        os.makedirs(TARGET_DIR_1, exist_ok=True)
        os.makedirs(TARGET_DIR_2, exist_ok=True)
        self.log_message("Application started. Target directories ensured.")
        self.log_message(f"Workspace root: {WORKSPACE_ROOT}")
        self.log_message(f"Watching source: {SOURCE_DIR}")
        self.log_message(f"Target 1: {TARGET_DIR_1}")
        self.log_message(f"Target 2: {TARGET_DIR_2}")

    def _initialize_stats(self):
        self.stats = {
            "md_files_processed_session": 0,
            "mdc_files_written_session": 0, # Counts each .mdc file write (so, up to 2 per source .md)
            "unique_md_converted_session": 0,
            "content_links_updated_session": 0,
            "core_files_always_apply_session": 0,
            "placeholder_descriptions_session": 0,
            "git_commits_triggered_session": 0,
            "git_pushes_triggered_session": 0,
            # Batch specific stats (reset per batch/scan)
            "batch_md_files_processed": 0,
            "batch_mdc_files_written": 0,
            "batch_unique_md_converted": 0,
            "batch_content_links_updated": 0,
            "batch_core_files_always_apply": 0,
            "batch_placeholder_descriptions": 0,
            "batch_git_commits_triggered": 0,
            "batch_git_pushes_triggered": 0,
        }

    def _reset_batch_stats(self):
        self.stats["batch_md_files_processed"] = 0
        self.stats["batch_mdc_files_written"] = 0
        self.stats["batch_unique_md_converted"] = 0
        self.stats["batch_content_links_updated"] = 0
        self.stats["batch_core_files_always_apply"] = 0
        self.stats["batch_placeholder_descriptions"] = 0
        self.stats["batch_git_commits_triggered"] = 0
        self.stats["batch_git_pushes_triggered"] = 0

    def _update_conversion_stats(self, conversion_info):
        if not conversion_info:
            return

        self.stats["batch_md_files_processed"] += 1
        self.stats["md_files_processed_session"] += 1

        if conversion_info.get("converted", False):
            self.stats["batch_unique_md_converted"] += 1
            self.stats["unique_md_converted_session"] += 1
            if conversion_info.get("mdc_path_1"):
                self.stats["batch_mdc_files_written"] += 1
                self.stats["mdc_files_written_session"] += 1
            if conversion_info.get("mdc_path_2"):
                self.stats["batch_mdc_files_written"] += 1
                self.stats["mdc_files_written_session"] += 1
            
            if conversion_info.get("core_always_apply_set", False):
                self.stats["batch_core_files_always_apply"] += 1
                self.stats["core_files_always_apply_session"] += 1
            if conversion_info.get("placeholder_description_used", False):
                self.stats["batch_placeholder_descriptions"] += 1
                self.stats["placeholder_descriptions_session"] += 1
            if conversion_info.get("content_links_updated", False):
                self.stats["batch_content_links_updated"] += 1
                self.stats["content_links_updated_session"] += 1
    
    def _increment_git_commit_stats(self):
        self.stats["batch_git_commits_triggered"] += 1
        self.stats["git_commits_triggered_session"] += 1

    def _increment_git_push_stats(self):
        self.stats["batch_git_pushes_triggered"] += 1
        self.stats["git_pushes_triggered_session"] += 1

    def _log_batch_summary(self, operation_name="Batch"):
        self.log_message(f"--- {operation_name} Statistics Summary ---")
        self.log_message(f"  .md Files Processed in {operation_name}: {self.stats['batch_md_files_processed']}")
        self.log_message(f"  Unique .md Files Converted in {operation_name}: {self.stats['batch_unique_md_converted']}")
        self.log_message(f"  .mdc Files Written in {operation_name}: {self.stats['batch_mdc_files_written']}")
        self.log_message(f"  Content Links Updated in {operation_name}: {self.stats['batch_content_links_updated']}")
        self.log_message(f"  Core Files Set to alwaysApply:true in {operation_name}: {self.stats['batch_core_files_always_apply']}")
        self.log_message(f"  Placeholder Descriptions Used in {operation_name}: {self.stats['batch_placeholder_descriptions']}")
        self.log_message(f"  Git Commits Triggered in {operation_name}: {self.stats['batch_git_commits_triggered']}")
        self.log_message(f"  Git Pushes Triggered in {operation_name}: {self.stats['batch_git_pushes_triggered']}")
        self.log_message( "---------------------------------")

    def _log_session_summary(self):
        self.log_message("--- Session Statistics Summary ---")
        self.log_message(f"  Total .md Files Processed: {self.stats['md_files_processed_session']}")
        self.log_message(f"  Total Unique .md Files Converted: {self.stats['unique_md_converted_session']}")
        self.log_message(f"  Total .mdc Files Written: {self.stats['mdc_files_written_session']}")
        self.log_message(f"  Total Content Links Updated: {self.stats['content_links_updated_session']}")
        self.log_message(f"  Total Core Files Set to alwaysApply:true: {self.stats['core_files_always_apply_session']}")
        self.log_message(f"  Total Placeholder Descriptions Used: {self.stats['placeholder_descriptions_session']}")
        self.log_message(f"  Total Git Commits Triggered: {self.stats['git_commits_triggered_session']}")
        self.log_message(f"  Total Git Pushes Triggered: {self.stats['git_pushes_triggered_session']}")
        self.log_message("---------------------------------")

    def _setup_ui(self):
        # Controls Frame
        controls_frame = ttk.Frame(self, padding="10")
        controls_frame.pack(fill=tk.X)

        self.start_stop_button = ttk.Button(controls_frame, text="Start Watching", command=self.toggle_watcher)
        self.start_stop_button.pack(side=tk.LEFT, padx=5)

        self.initial_scan_button = ttk.Button(controls_frame, text="Run Initial Scan", command=self.run_initial_scan_threaded)
        self.initial_scan_button.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(controls_frame, text="Status: Idle", font=("Arial", 10))
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.full_sync_button = ttk.Button(controls_frame, text="Full Sync & Commit", command=self.full_sync_and_commit_gui)
        self.full_sync_button.pack(side=tk.LEFT, padx=5)

        # Log Text Area
        log_frame = ttk.LabelFrame(self, text="Logs", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.NORMAL, height=15) # state NORMAL to allow programmatic insert
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.configure(state=tk.DISABLED) # Then disable to make it read-only for user

    def log_message(self, message):
        if hasattr(self, 'log_text') and self.log_text:
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        else: # Fallback if GUI not fully initialized
            print(message)

    def process_git_commit_batch(self, mdc_paths_to_commit, commit_msg):
        # Don't trigger another full sync, just commit the changes
        try:
            # Ensure .gitignore is correct
            ensure_gitignore_entries(['.cursor/', 'rules-md/'], self.log_message)
            
            # Properly handle ignored folders
            remove_ignored_from_git_index(self.log_message)
            
            # Add only rules/ directory changes
            add_cmd = 'add -A "rules/"'
            run_git_command(add_cmd, self.log_message, WORKSPACE_ROOT)
            
            # Check if there are actual changes to commit
            status_cmd = 'status --porcelain "rules/"'
            try:
                result = subprocess.run(f'git {status_cmd}', cwd=WORKSPACE_ROOT, capture_output=True, text=True, check=True, shell=True)
                if result.stdout.strip():
                    # Changes exist, commit them
                    commit_cmd = f'commit -m "{commit_msg}"'
                    if run_git_command(commit_cmd, self.log_message, WORKSPACE_ROOT):
                        self._increment_git_commit_stats()
                        # Only push if commit was successful
                        if has_remote_origin(self.log_message):
                            push_cmd = 'push origin HEAD'
                            if run_git_command(push_cmd, self.log_message, WORKSPACE_ROOT):
                                self._increment_git_push_stats()
                else:
                    self.log_message('No changes to commit in rules/.')
            except Exception as e:
                self.log_message(f"Error checking git status or committing: {e}")
            
        except Exception as e:
            self.log_message(f"Error in process_git_commit_batch: {e}")

    def run_initial_scan_threaded(self):
        """
        Start initial scan in a background thread
        """
        if self.is_watching:
            messagebox.showwarning("Watcher Active", "Please stop the watcher before running an initial scan.")
            return
        self.log_message("Starting initial scan manually...")
        self.initial_scan_button.config(state=tk.DISABLED)
        scan_thread = threading.Thread(target=self._initial_scan_worker, daemon=True)
        scan_thread.start()

    def _initial_scan_worker(self):
        """
        Worker function for initial scan thread
        """
        try:
            self._reset_batch_stats() # Reset stats before scan
            self.run_initial_scan()
            self._log_batch_summary("Initial Scan") # Log summary after scan
        except Exception as e:
            self.log_message(f"Error during initial scan: {e}")
        finally:
            self.after(0, lambda: self.initial_scan_button.config(state=tk.NORMAL))

    def run_initial_scan(self):
        """
        Perform initial scan of source directory and process all files
        """
        self.log_message(f"Performing initial scan of {SOURCE_DIR}...")
        
        # Process all .md files in source directory
        files_to_commit_for_initial_scan = set()
        initial_commit_file_basenames = []

        for root, _, files in os.walk(SOURCE_DIR):
            for file in files:
                if file.endswith('.md'):
                    source_path = os.path.join(root, file)
                    conversion_info = self.process_source_file(source_path)
                    self._update_conversion_stats(conversion_info)
                    if conversion_info and conversion_info.get("converted"):
                        if conversion_info.get("mdc_path_1"):
                             files_to_commit_for_initial_scan.add(os.path.abspath(conversion_info.get("mdc_path_1")))
                        if conversion_info.get("mdc_path_2"):
                             files_to_commit_for_initial_scan.add(os.path.abspath(conversion_info.get("mdc_path_2")))
                        initial_commit_file_basenames.append(os.path.basename(conversion_info.get("source_filename", "unknown"))[:-3])
        
        # Only commit changes, don't trigger another full sync
        if files_to_commit_for_initial_scan:
            unique_basenames = sorted(list(set(initial_commit_file_basenames)))
            commit_message = f"{COMMIT_MESSAGE_PREFIX}: Initial sync of {len(unique_basenames)} file(s)"
            if len(unique_basenames) > 3:
                 commit_message = f"{COMMIT_MESSAGE_PREFIX}: Initial sync of {len(unique_basenames)} files including {unique_basenames[0]}, etc."
            elif unique_basenames:
                 commit_message = f"{COMMIT_MESSAGE_PREFIX}: Initial sync {', '.join(unique_basenames)}"

            # process_git_commit_batch expects list of mdc_paths_to_commit (not really used by it now) and commit_msg
            self.process_git_commit_batch(list(files_to_commit_for_initial_scan), commit_message)
        else:
            self.log_message("Initial scan complete. No files processed or no changes to commit.")
        
        self.log_message("Initial scan finished.")

    def toggle_watcher(self):
        if self.is_watching:
            self.stop_watcher()
        else:
            self.start_watcher()

    def start_watcher(self):
        if not os.path.exists(SOURCE_DIR):
            self.log_message(f"Error: Source directory {SOURCE_DIR} does not exist. Cannot start watcher.")
            messagebox.showerror("Error", f"Source directory not found:\n{SOURCE_DIR}")
            return

        self.is_watching = True
        self.start_stop_button.config(text="Stop Watching")
        self.status_label.config(text="Status: Watching...")
        self.initial_scan_button.config(state=tk.DISABLED) # Disable scan while watching
        self.log_message(f"Starting watcher for {SOURCE_DIR}...")
        self.stop_event.clear()

        self.observer = Observer()
        # Pass self (RulesSyncApp instance) to ChangeHandler for stats updates
        event_handler = ChangeHandler(self) 
        self.observer.schedule(event_handler, SOURCE_DIR, recursive=True)
        
        self.watcher_thread = threading.Thread(target=self._run_observer_loop, args=(self.observer, event_handler), daemon=True)
        self.watcher_thread.start()

    def _run_observer_loop(self, observer, event_handler):
        observer.start()
        try:
            while not self.stop_event.is_set():
                event_handler.check_and_process_batch()
                time.sleep(event_handler.timeout_check_interval)
        except Exception as e:
            self.log_message(f"Error in watcher thread: {e}")
        finally:
            observer.stop()
            observer.join()
            self.log_message("Watcher thread stopped.")

    def stop_watcher(self):
        if self.observer and self.watcher_thread and self.watcher_thread.is_alive():
            self.log_message("Stopping watcher...")
            self.stop_event.set()
            # self.watcher_thread.join() # Wait for thread to finish
            # Observer stop/join is handled in _run_observer_loop's finally block

        self.is_watching = False
        self.start_stop_button.config(text="Start Watching")
        self.status_label.config(text="Status: Idle")
        self.initial_scan_button.config(state=tk.NORMAL) # Re-enable scan when not watching
        self.log_message("Watcher stopped.")

        # Restore stdout before exiting, if it was redirected
        if hasattr(self, 'original_stdout') and self.original_stdout:
            sys.stdout = self.original_stdout
        self._log_session_summary() # Log session summary before closing
        self.destroy()

    def on_closing(self):
        self.log_message("Closing application...")
        self.stop_watcher() 
        if hasattr(self, 'original_stdout') and self.original_stdout:
            sys.stdout = self.original_stdout
        self._log_session_summary() 
        self.destroy()

    def full_sync_and_commit_gui(self):
        self._reset_batch_stats()
        self.log_message('Starting full sync and commit...')
        
        for target in [TARGET_DIR_1, TARGET_DIR_2]:
            delete_all_mdc_files(target, self.log_message)
        
        processed_files_in_full_sync = set()
        core_applied_in_full_sync = 0
        placeholder_desc_in_full_sync = 0
        links_updated_in_full_sync = 0

        for root, _, files in os.walk(SOURCE_DIR):
            for file in files:
                if file.endswith('.md'):
                    source_file_path = os.path.join(root, file)
                    conversion_info = convert_md_to_mdc(source_file_path, TARGET_DIR_1, TARGET_DIR_2, self.log_message)
                    self._update_conversion_stats(conversion_info) 
                    if conversion_info and conversion_info.get("converted"):
                        processed_files_in_full_sync.add(conversion_info.get("source_filename"))
                        if conversion_info.get("core_always_apply_set"):
                            core_applied_in_full_sync +=1
                        if conversion_info.get("placeholder_description_used"):
                            placeholder_desc_in_full_sync +=1
                        if conversion_info.get("content_links_updated"):
                            links_updated_in_full_sync +=1
        
        ensure_gitignore_entries(['.cursor/', 'rules-md/'], self.log_message)
        remove_ignored_from_git_index(self.log_message)
        add_cmd = 'add -A "rules/"'
        run_git_command(add_cmd, self.log_message, WORKSPACE_ROOT)
        
        status_cmd = 'status --porcelain "rules/"'
        try:
            result = subprocess.run(f'git {status_cmd}', cwd=WORKSPACE_ROOT, capture_output=True, text=True, check=True, shell=True)
            if result.stdout.strip():
                commit_cmd = f'commit -m "{COMMIT_MESSAGE_PREFIX}: Full sync"'
                if run_git_command(commit_cmd, self.log_message, WORKSPACE_ROOT):
                    self._increment_git_commit_stats()
                    if has_remote_origin(self.log_message):
                        push_cmd = 'push origin HEAD'
                        if run_git_command(push_cmd, self.log_message, WORKSPACE_ROOT):
                             self._increment_git_push_stats()
            else:
                self.log_message('No changes to commit in rules/ after full sync.')
        except Exception as e:
            self.log_message(f"Error checking git status or committing during full sync: {e}")

        self.log_message('Full sync and commit finished.')
        self._log_batch_summary("Full Sync")

    def process_source_file(self, source_path):
        """
        Process a single .md source file and convert it to .mdc in both target directories
        Returns the conversion_info dictionary or None if not an .md file or error.
        """
        if not source_path.endswith('.md'):
            return None
        
        try:
            conversion_info = convert_md_to_mdc(source_path, TARGET_DIR_1, TARGET_DIR_2, self.log_message)
            return conversion_info
        except Exception as e:
            self.log_message(f"Error processing source file {source_path}: {e}")
            return {"converted": False, "source_filename": os.path.basename(source_path)} # Match error return of convert_md_to_mdc

if __name__ == "__main__":
    app = RulesSyncApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
# Old command-line execution part removed as it's now a GUI app
# Original main execution block commented out/removed
# if __name__ == "__main__":
#     print("Starting rules sync script...")
# ... (rest of old main) 