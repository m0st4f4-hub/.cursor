import sys
import os
# import time # No longer needed here
# import shutil # No longer needed here
# import subprocess # No longer needed here
# from watchdog.observers import Observer # No longer needed here
# from watchdog.events import FileSystemEventHandler # No longer needed here
# import tkinter as tk # No longer needed here
# from tkinter import scrolledtext, ttk, messagebox # No longer needed here
# import threading # No longer needed here
# import queue # No longer needed here
# import glob # No longer needed here
# import frontmatter # No longer needed here
# import yaml # No longer needed here
# import traceback # No longer needed here

# Ensure the project root is in sys.path 
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR) 

if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# # Import configurations - No longer directly used here, but good for context if this file had more logic
# from tools.rules_sync_lib.config import (
#     SOURCE_DIR, TARGET_DIR_1, TARGET_DIR_2,
#     COMMIT_MESSAGE_PREFIX, DEBOUNCE_PERIOD,
#     CORE_ALWAYS_APPLY_FILES, WORKSPACE_ROOT 
# )
# # Import utilities - No longer directly used here
# from tools.rules_sync_lib.utils import StdoutRedirector 
# # Import parser functions - No longer directly used here
# from tools.rules_sync_lib.parser import parse_md_metadata_and_content, convert_md_to_mdc 
# # Import specific git functions - No longer directly used here
# from tools.rules_sync_lib.git_handler import (
#     git_add, git_commit, git_push, 
#     git_status_porcelain, git_check_ignore, git_rm_cached
# )
# from tools.rules_sync_lib.stats_handler import StatsHandler 
# from tools.rules_sync_lib.event_handler import ChangeHandler 

# Removed helper functions that are now in rules_sync_lib:
# - commit_and_push_changes
# - delete_all_mdc_files
# - ensure_gitignore_entries
# - remove_ignored_from_git_index
# - has_remote_origin
# - full_sync_and_commit

# Assuming this script (sync_rules.py or main.py) is in the 'tools' directory,
# and rules_sync_lib is a subdirectory of 'tools'.
from tools.rules_sync_lib.gui import RulesSyncApp

if __name__ == "__main__":
    app = RulesSyncApp()
    app.mainloop()
# Old command-line execution part removed as it's now a GUI app
# Original main execution block commented out/removed
# if __name__ == "__main__":
#     print("Starting rules sync script...")
# ... (rest of old main) 