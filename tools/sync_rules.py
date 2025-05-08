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

def convert_md_to_mdc(source_path, dest_parent_dir_1, dest_parent_dir_2, log_callback):
    """
    Converts/copies an .md file to .mdc format and places it in target directories,
    maintaining the subdirectory structure from the source.
    """
    if not source_path.endswith(".md"):
        log_callback(f"Skipping non-md file: {source_path}")
        return None, None

    try:
        mdc_filename = os.path.basename(source_path)[:-3] + ".mdc"
        # Calculate relative path from SOURCE_DIR to the directory of source_path
        relative_dir_path = os.path.relpath(os.path.dirname(source_path), SOURCE_DIR)
        if relative_dir_path == ".": # if file is in root of SOURCE_DIR
            relative_dir_path = ""

        # Construct destination subdirectories
        dest_subdir_1 = os.path.join(dest_parent_dir_1, relative_dir_path)
        dest_subdir_2 = os.path.join(dest_parent_dir_2, relative_dir_path)

        os.makedirs(dest_subdir_1, exist_ok=True)
        os.makedirs(dest_subdir_2, exist_ok=True)

        mdc_dest_path_1 = os.path.join(dest_subdir_1, mdc_filename)
        mdc_dest_path_2 = os.path.join(dest_subdir_2, mdc_filename)

        log_callback(f"Processing {source_path}")
        # Simple copy for now. Replace with actual conversion if needed.
        shutil.copy2(source_path, mdc_dest_path_1)
        log_callback(f"  -> Copied to {mdc_dest_path_1}")
        shutil.copy2(source_path, mdc_dest_path_2)
        log_callback(f"  -> Copied to {mdc_dest_path_2}")
        return mdc_dest_path_1, mdc_dest_path_2
    except Exception as e:
        log_callback(f"Error converting/copying {source_path}: {e}")
        return None, None


def run_git_command(command, cwd=None):
    """Run a git command with proper git directory and work tree settings"""
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
        log_callback(f"Running git command: '''{command}''' in {WORKSPACE_ROOT}")
        
        if result.returncode != 0:
            log_callback(f"Error running git command: '''{command}'''")
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
        add_command_normal = ["git", "add"] + normal_add_files_relative
        log_callback(f"Attempting to add {len(normal_add_files_relative)} file(s) normally: {', '.join(normal_add_files_relative)}")
        if not run_git_command(add_command_normal, WORKSPACE_ROOT):
            log_callback(f"Failed to git add files: {', '.join(normal_add_files_relative)}.")
            all_adds_successful = False

    if force_add_files_relative:
        add_command_force = ["git", "add", "-f"] + force_add_files_relative
        log_callback(f"Attempting to force-add {len(force_add_files_relative)} file(s): {', '.join(force_add_files_relative)}")
        if not run_git_command(add_command_force, WORKSPACE_ROOT):
            log_callback(f"Failed to git add -f files: {', '.join(force_add_files_relative)}.")
            all_adds_successful = False

    if not all_adds_successful:
        log_callback("One or more git add operations failed. Aborting commit and push.")
        return

    # Check if there are any staged changes before committing
    status_command = ["git", "status", "--porcelain"]
    # We need to capture output here, so temporarily modify run_git_command or use a direct subprocess call
    try:
        log_callback(f"Running git command: '''{' '.join(status_command)}''' in {WORKSPACE_ROOT}")
        process = subprocess.run(status_command, cwd=WORKSPACE_ROOT, check=True, capture_output=True, text=True, shell=False)
        if not process.stdout.strip(): # No output means no staged changes
            log_callback("No changes staged for commit. Skipping commit and push.")
            return
        log_callback(f"Git status output (staged files):\n{process.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        log_callback(f"Error running git status: {e.stderr}")
        log_callback("Could not verify staged changes. Aborting commit to be safe.")
        return
    except Exception as e:
        log_callback(f"An unexpected error occurred running git status: {e}")
        log_callback("Could not verify staged changes. Aborting commit to be safe.")
        return

    commit_command = ["git", "commit", "-m", commit_message]
    if not run_git_command(commit_command, WORKSPACE_ROOT):
        log_callback("Failed to git commit changes. Aborting push.")
        return

    # Attempt to pull before pushing to integrate remote changes
    pull_command = ["git", "pull"]
    log_callback("Attempting to git pull to integrate remote changes...")
    if not run_git_command(pull_command, WORKSPACE_ROOT):
        log_callback("Failed to git pull. Please resolve any conflicts manually and then push. Aborting automated push.")
        return

    push_command = ["git", "push"]
    if not run_git_command(push_command, WORKSPACE_ROOT):
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
    for folder in ['.cursor', 'rules-md']:
        rm_cmd = ['git', 'rm', '-r', '--cached', folder]
        run_git_command(rm_cmd, WORKSPACE_ROOT)

# Utility: Get actual git root
def get_git_root():
    try:
        result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=WORKSPACE_ROOT, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception:
        return WORKSPACE_ROOT

# Utility: Check if remote is set
def has_remote_origin(log_callback):
    try:
        result = subprocess.run(['git', 'remote', '-v'], cwd=WORKSPACE_ROOT, capture_output=True, text=True, check=True)
        if 'origin' in result.stdout:
            return True
        log_callback('No remote origin set. Please set remote to https://github.com/m0st4f4-hub/.cursor')
        return False
    except Exception as e:
        log_callback(f"Error checking remote: {e}")
        return False

# Main sync logic: delete, regenerate, commit/push

def full_sync_and_commit(log_callback):
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
    add_cmd = ['git', 'add', '-A', 'rules/']
    run_git_command(add_cmd, WORKSPACE_ROOT)
    # 6. Commit if there are changes
    status_cmd = ['git', 'status', '--porcelain', 'rules/']
    try:
        result = subprocess.run(status_cmd, cwd=WORKSPACE_ROOT, capture_output=True, text=True, check=True)
        if result.stdout.strip():
            commit_cmd = ['git', 'commit', '-m', f'{COMMIT_MESSAGE_PREFIX}: Full sync']
            run_git_command(commit_cmd, WORKSPACE_ROOT)
            # 7. Push if remote is set
            if has_remote_origin(log_callback):
                push_cmd = ['git', 'push', 'origin', 'HEAD']
                run_git_command(push_cmd, WORKSPACE_ROOT)
        else:
            log_callback('No changes to commit in rules/.')
    except Exception as e:
        log_callback(f"Error checking git status or committing: {e}")

class ChangeHandler(FileSystemEventHandler):
    def __init__(self, log_callback, process_batch_callback):
        self.log_callback = log_callback
        self.process_batch_callback = process_batch_callback
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
            self.log_callback(f"Event detected: {event.event_type} - {event.src_path}")
            self.changed_files_batch.add(event.src_path)
            self.last_event_time = time.time()

    def check_and_process_batch(self):
        if self.processing_lock:
            return
            
        if self.changed_files_batch and (time.time() - self.last_event_time >= DEBOUNCE_PERIOD):
            self.processing_lock = True
            self.log_callback(f"Debounce period ended ({DEBOUNCE_PERIOD}s). Processing batch of {len(self.changed_files_batch)} event(s).")
            
            current_batch = list(self.changed_files_batch)
            self.changed_files_batch.clear()
            
            all_generated_mdc_paths_abs = set()
            commit_file_basenames = []

            for src_path in current_batch:
                mdc_path_1, mdc_path_2 = convert_md_to_mdc(src_path, TARGET_DIR_1, TARGET_DIR_2, self.log_callback)
                if mdc_path_1:
                    all_generated_mdc_paths_abs.add(os.path.abspath(mdc_path_1))
                    commit_file_basenames.append(os.path.basename(mdc_path_1)[:-4]) 
                if mdc_path_2:
                    all_generated_mdc_paths_abs.add(os.path.abspath(mdc_path_2))

            if all_generated_mdc_paths_abs:
                unique_file_basenames = sorted(list(set(commit_file_basenames)))
                commit_message = f"{COMMIT_MESSAGE_PREFIX}: Sync {', '.join(unique_file_basenames)}"
                # Call the main app's processing method
                self.process_batch_callback(list(all_generated_mdc_paths_abs), commit_message)
            else:
                self.log_callback("No files were successfully processed in this batch.")
            
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
        self.geometry("700x500")

        self.observer = None
        self.watcher_thread = None
        self.stop_event = threading.Event()
        self.is_watching = False

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
        self.full_sync_and_commit_gui()

    def run_initial_scan_threaded(self):
        if self.is_watching:
            messagebox.showwarning("Watcher Active", "Please stop the watcher before running an initial scan.")
            return
        self.log_message("Starting initial scan manually...")
        self.initial_scan_button.config(state=tk.DISABLED)
        scan_thread = threading.Thread(target=self._initial_scan_worker, daemon=True)
        scan_thread.start()

    def _initial_scan_worker(self):
        try:
            initial_scan_and_process_logic(self.log_message, self.process_git_commit_batch)
        except Exception as e:
            self.log_message(f"Error during initial scan: {e}")
        finally:
            self.after(0, lambda: self.initial_scan_button.config(state=tk.NORMAL)) # Re-enable button on main thread
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
        # Pass self.process_git_commit_batch to ChangeHandler
        event_handler = ChangeHandler(self.log_message, self.process_git_commit_batch) 
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

    def on_closing(self):
        self.log_message("Closing application...")
        self.stop_watcher() # Ensure watcher is stopped
        # Restore stdout before exiting, if it was redirected
        if hasattr(self, 'original_stdout') and self.original_stdout:
            sys.stdout = self.original_stdout
        self.destroy()

    def full_sync_and_commit_gui(self):
        self.log_message('Starting full sync and commit...')
        full_sync_and_commit(self.log_message)
        self.log_message('Full sync and commit finished.')


if __name__ == "__main__":
    app = RulesSyncApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
# Old command-line execution part removed as it's now a GUI app
# Original main execution block commented out/removed
# if __name__ == "__main__":
#     print("Starting rules sync script...")
# ... (rest of old main) 