import sys
import os
import time
import shutil
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
import queue # For thread-safe communication
import glob
import frontmatter # For handling YAML frontmatter
import yaml # For YAML processing
import traceback # Added for more detailed error logging in convert_md_to_mdc

# Ensure the project root is in sys.path to allow absolute imports like 'from tools. ...'
# when this script is run directly.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR) # This assumes 'tools' is directly under project root

if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Import configurations from the new module
from tools.rules_sync_lib.config import (
    SOURCE_DIR, TARGET_DIR_1, TARGET_DIR_2,
    COMMIT_MESSAGE_PREFIX, DEBOUNCE_PERIOD,
    CORE_ALWAYS_APPLY_FILES, WORKSPACE_ROOT # WORKSPACE_ROOT might be needed if not redefined locally
)
# Import utilities
from tools.rules_sync_lib.utils import StdoutRedirector
# Import parser functions
from tools.rules_sync_lib.parser import parse_md_metadata_and_content, convert_md_to_mdc
# Import specific git functions
from tools.rules_sync_lib.git_handler import (
    git_add, git_commit, git_push, 
    git_status_porcelain, git_check_ignore, git_rm_cached
)
from tools.rules_sync_lib.stats_handler import StatsHandler # Import StatsHandler
from tools.rules_sync_lib.event_handler import ChangeHandler # Import ChangeHandler

# Configuration: These paths are relative to the script's parent directory (workspace root)
# Assumes the script is in a 'tools' subdirectory of the workspace root.
# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# WORKSPACE_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# SOURCE_DIR_NAME = "rules-md"
# TARGET_DIR_1_NAME = "rules"
# TARGET_DIR_2_NAME = ".cursor/rules"

# SOURCE_DIR = os.path.join(WORKSPACE_ROOT, SOURCE_DIR_NAME)
# TARGET_DIR_1 = os.path.join(WORKSPACE_ROOT, TARGET_DIR_1_NAME)
# TARGET_DIR_2 = os.path.join(WORKSPACE_ROOT, TARGET_DIR_2_NAME)

# COMMIT_MESSAGE_PREFIX = "Chore: Auto-sync rule changes"
# DEBOUNCE_PERIOD = 2.0  # seconds

# --- Helper class to redirect stdout to GUI ---
# class StdoutRedirector:
#     def __init__(self, text_widget):
#         self.text_widget = text_widget
#         self.queue = queue.Queue()
#         self.text_widget.after(100, self._process_queue)
# 
#     def write(self, string):
#         self.queue.put(string)
# 
#     def _process_queue(self):
#         try:
#             while True:
#                 string = self.queue.get_nowait()
#                 self.text_widget.insert(tk.END, string)
#                 self.text_widget.see(tk.END) # Scroll to the end
#         except queue.Empty:
#             pass
#         self.text_widget.after(100, self._process_queue)
# 
#     def flush(self):
#         # Tkinter Text widget auto-flushes, but good to have for compatibility
#         pass

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

class RulesSyncApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rules Sync Tool")
        self.geometry("700x550")

        self.observer = None
        self.watcher_thread = None
        self.stop_event = threading.Event()
        self.is_watching = False

        # Initialize StatsHandler
        # self.log_message will be available after _setup_ui creates the text widget
        # So, we pass a lambda that will eventually call self.log_message
        # Or, we can pass self.log_message directly if _setup_ui is called before stats_handler methods that log
        # For simplicity, let's assume log_message is ready or stats_handler methods check if log_callback is callable
        self._setup_ui() # Setup UI first so log_text is available
        self.stats_handler = StatsHandler(self.log_message) # Pass the actual log_message method

        self.original_stdout = sys.stdout
        sys.stdout = StdoutRedirector(self.log_text)

        os.makedirs(TARGET_DIR_1, exist_ok=True)
        os.makedirs(TARGET_DIR_2, exist_ok=True)
        self.log_message("Application started. Target directories ensured.")
        self.log_message(f"Workspace root: {WORKSPACE_ROOT}")
        self.log_message(f"Watching source: {SOURCE_DIR}")
        self.log_message(f"Target 1: {TARGET_DIR_1}")
        self.log_message(f"Target 2: {TARGET_DIR_2}")

        self.git_repo_exists = os.path.exists(os.path.join(WORKSPACE_ROOT, ".git"))
        if not self.git_repo_exists:
            self.log_message("Warning: Not a Git repository. Git-related operations will be skipped.")
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_ui(self):
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Log display area
        self.log_text = scrolledtext.ScrolledText(self.main_frame, wrap=tk.WORD, height=20, width=80)
        self.log_text.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        # Buttons
        self.scan_button = ttk.Button(self.main_frame, text="Run Initial Scan & Commit", command=self.run_initial_scan_threaded)
        self.scan_button.grid(row=1, column=0, padx=5, pady=5, sticky=tk.EW)

        self.watch_button = ttk.Button(self.main_frame, text="Start Watching", command=self.start_watching_threaded)
        self.watch_button.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        self.stop_button = ttk.Button(self.main_frame, text="Stop Watching", command=self.stop_watching, state=tk.DISABLED)
        self.stop_button.grid(row=1, column=2, padx=5, pady=5, sticky=tk.EW)

    def log_message(self, message):
        if hasattr(self, 'log_text') and self.log_text:
            self.log_text.insert(tk.END, str(message) + "\n")
            self.log_text.see(tk.END)
            self.update_idletasks() # Ensure GUI updates
        else:
            print(message) # Fallback if GUI not ready

    def process_file(self, md_file_path):
        _, _, conversion_stats, error = convert_md_to_mdc(md_file_path, TARGET_DIR_1, TARGET_DIR_2, self.log_message)
        if error:
            self.log_message(f"Error processing {md_file_path}: {error}")
        if conversion_stats:
            self.stats_handler.update_conversion_stats(conversion_stats) # Use StatsHandler

    def process_files_in_source_dir(self, source_directory):
        for root, _, files in os.walk(source_directory):
            for file in files:
                if file.endswith(".md"):
                    md_file_path = os.path.join(root, file)
                    self.process_file(md_file_path)
        self.stats_handler.log_batch_summary("Initial Scan") # Use StatsHandler

    def process_git_commit_batch(self, file_paths, commit_message_override=None):
        if not self.git_repo_exists: self.log_message("Not a Git repo. Skipping commit/push."); return
        self.log_message(f"Processing git commit batch for relevant changes.") # Changed log message slightly
        
        paths_to_add_rel = []
        # Only add TARGET_DIR_1 (typically 'rules/') to git.
        # TARGET_DIR_2 (typically '.cursor/rules/') is managed by .gitignore and should not be added here.
        if os.path.exists(TARGET_DIR_1):
            paths_to_add_rel.append(os.path.relpath(TARGET_DIR_1, WORKSPACE_ROOT))
        
        if not paths_to_add_rel:
            self.log_message(f"Target directory for git add ({TARGET_DIR_1}) missing or not configured. Skipping git add.")
            return

        success_add, _, stderr_add = git_add(paths_to_add_rel, self.log_message, cwd=WORKSPACE_ROOT)
        if not success_add: self.log_message(f"Error git add for {paths_to_add_rel}. Skip commit/push. Stderr: {stderr_add}"); return

        success_status, stdout_status, stderr_status = git_status_porcelain(paths=paths_to_add_rel, log_callback=self.log_message, cwd=WORKSPACE_ROOT)
        if not success_status: self.log_message(f"Error git status. Skip commit. Stderr: {stderr_status}"); return
        if not stdout_status.strip(): self.log_message("No actual changes to commit. Skip commit."); return
        
        final_commit_message = COMMIT_MESSAGE_PREFIX
        if commit_message_override: final_commit_message = commit_message_override
        elif file_paths:
            basenames = sorted(list(set(os.path.basename(p) for p in file_paths)))
            if len(basenames) > 3: final_commit_message += f": Sync {len(basenames)} files including {basenames[0]}"
            else: final_commit_message += f": Sync {', '.join(basenames)}"
        else: final_commit_message += ": Sync rule files"

        commit_success, _, stderr_commit = git_commit(final_commit_message, self.log_message, cwd=WORKSPACE_ROOT)
        if commit_success:
            self.log_message(f"Successfully committed: {final_commit_message}")
            self.stats_handler.increment_git_commits() # Use StatsHandler
            push_success, _, stderr_push = git_push(self.log_message, cwd=WORKSPACE_ROOT)
            if push_success:
                self.log_message("Successfully pushed changes.")
                self.stats_handler.increment_git_pushes() # Use StatsHandler
            else: self.log_message(f"Git push failed. Stderr: {stderr_push}")
        else: self.log_message(f"Git commit failed. Stderr: {stderr_commit}")

    def run_initial_scan_threaded(self):
        self.stats_handler.reset_batch_stats() # Use StatsHandler
        threading.Thread(target=self.full_sync_and_commit_gui, daemon=True).start()

    def on_closing(self):
        self.log_message("Application closing...")
        self.stats_handler.log_session_summary() # Use StatsHandler
        if self.is_watching:
            self.stop_watching()
        if hasattr(self.original_stdout, 'close') and not self.original_stdout.closed:
             sys.stdout = self.original_stdout # Restore stdout
        self.destroy()

    def full_sync_and_commit_gui(self):
        self.stats_handler.reset_batch_stats()
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
                    self.stats_handler.update_conversion_stats(conversion_info) 
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
                    self.stats_handler.increment_git_commits()
                    if has_remote_origin(self.log_message):
                        push_cmd = 'push origin HEAD'
                        if run_git_command(push_cmd, self.log_message, WORKSPACE_ROOT):
                             self.stats_handler.increment_git_pushes()
            else:
                self.log_message('No changes to commit in rules/ after full sync.')
        except Exception as e:
            self.log_message(f"Error checking git status or committing during full sync: {e}")

        self.log_message('Full sync and commit finished.')
        self.stats_handler.log_batch_summary("Full Sync")

    def start_watching_threaded(self):
        if not os.path.exists(SOURCE_DIR):
            self.log_message(f"Error: Source directory {SOURCE_DIR} does not exist. Cannot start watcher.")
            messagebox.showerror("Error", f"Source directory not found:\n{SOURCE_DIR}")
            return

        self.is_watching = True
        self.watch_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.scan_button.config(state=tk.DISABLED) # Disable scan while watching
        self.log_message(f"Starting watcher for {SOURCE_DIR}...")
        self.stop_event.clear()

        self.observer = Observer() 
        # ChangeHandler is now imported
        event_handler = ChangeHandler(self) # Pass the app instance
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

    def stop_watching(self):
        if self.observer and self.watcher_thread and self.watcher_thread.is_alive():
            self.log_message("Stopping watcher...")
            self.stop_event.set()
            # self.watcher_thread.join() # Wait for thread to finish
            # Observer stop/join is handled in _run_observer_loop's finally block

        self.is_watching = False
        self.watch_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.scan_button.config(state=tk.NORMAL) # Enable scan after stopping
        self.log_message("Watcher stopped.")

        # Restore stdout before exiting, if it was redirected
        if hasattr(self, 'original_stdout') and self.original_stdout:
            sys.stdout = self.original_stdout
        self.stats_handler.log_session_summary() # Log session summary before closing
        self.destroy()

# Ensure the 'tools' directory is in the Python path if this script is run directly
# and rules_sync_lib is a sub-package of tools.
# This allows 'from tools.rules_sync_lib.gui import RulesSyncApp' to work.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR) # Add tools directory itself
# If rules_sync_lib is intended to be imported from the WORKSPACE_ROOT, 
# then WORKSPACE_ROOT needs to be in sys.path.
# For now, assuming execution from tools/ or that tools/ is in PYTHONPATH,
# and rules_sync_lib is a sub-package accessible via tools.rules_sync_lib

# If tools/rules_sync_lib is directly in python path (e.g. installed or PYTHONPATH set to include it)
# from rules_sync_lib.gui import RulesSyncApp

# Assuming this script (sync_rules.py or main.py) is in the 'tools' directory,
# and rules_sync_lib is a subdirectory of 'tools'.
from rules_sync_lib.gui import RulesSyncApp

if __name__ == "__main__":
    app = RulesSyncApp()
    # The protocol WM_DELETE_WINDOW is already handled in RulesSyncApp's __init__.
    app.mainloop()
# Old command-line execution part removed as it's now a GUI app
# Original main execution block commented out/removed
# if __name__ == "__main__":
#     print("Starting rules sync script...")
# ... (rest of old main) 