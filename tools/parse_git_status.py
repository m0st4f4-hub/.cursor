import subprocess
import json
import sys
import os
import platform

def parse_git_status_porcelain(output):
    """Parses the output of 'git status --porcelain=v1 -uall'."""
    status = {
        "staged": [],        # Files added to the index (e.g., 'A  file.txt', 'M  file.txt')
        "unstaged": [],     # Files modified but not staged (e.g., ' M file.txt')
        "untracked": [],    # Files not tracked by git (e.g., '?? file.txt')
        "conflicts": [],    # Unmerged paths (e.g., 'UU file.txt')
        "is_clean": False,
        "error": None
    }

    lines = output.strip().split('\n')
    if not output.strip(): # If output is empty, the working directory is clean
        status["is_clean"] = True
        return status

    for line in lines:
        if not line:
            continue

        xy = line[:2]
        path = line[3:]
        # Handle potentially quoted paths (e.g., containing spaces)
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1].encode('utf-8').decode('unicode_escape') # Decode escape sequences

        x = xy[0]
        y = xy[1]

        file_info = {"path": path, "x_status": x.strip(), "y_status": y.strip()}

        if xy == '??':
            status["untracked"].append(file_info)
        elif xy == 'UU':
            status["conflicts"].append(file_info)
            file_info["description"] = "Unmerged"
        else:
            # Staged changes (index status)
            if x in 'MADRC':
                staged_info = file_info.copy()
                if x == 'M': staged_info["description"] = "Modified"
                if x == 'A': staged_info["description"] = "Added"
                if x == 'D': staged_info["description"] = "Deleted"
                if x == 'R': staged_info["description"] = "Renamed"
                if x == 'C': staged_info["description"] = "Copied"
                status["staged"].append(staged_info)

            # Unstaged changes (work-tree status)
            if y in 'MD':
                unstaged_info = file_info.copy()
                if y == 'M': unstaged_info["description"] = "Modified"
                if y == 'D': unstaged_info["description"] = "Deleted"
                status["unstaged"].append(unstaged_info)
            elif y == 'A' and x == 'A': # Handle 'AA' case (added and staged, technically clean but listed)
                 pass # Often indicates a merge commit state, ignore for basic unstaged

    # Determine overall cleanliness
    status["is_clean"] = not (status["staged"] or status["unstaged"] or status["untracked"] or status["conflicts"])

    return status

def run_git_status():
    """Runs 'git status --porcelain=v1 -uall' and returns parsed results or error."""
    command = ["git", "status", "--porcelain=v1", "-uall"]
    try:
        # Check if it's a git repository first
        check_process = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore',
            shell=(platform.system() == "Windows")
        )
        if check_process.returncode != 0 or check_process.stdout.strip() != 'true':
            return {"error": "Not a git repository or git command not found.", "is_clean": False}

        # Run the status command
        process = subprocess.run(
            command,
            capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore',
            shell=(platform.system() == "Windows") # Use shell=True on Windows
        )

        if process.returncode != 0:
            return {"error": f"Git command failed with exit code {process.returncode}. Stderr: {process.stderr.strip()}", "is_clean": False}

        return parse_git_status_porcelain(process.stdout)

    except FileNotFoundError:
        return {"error": "'git' command not found. Is Git installed and in PATH?", "is_clean": False}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}", "is_clean": False}

if __name__ == "__main__":
    result = run_git_status()
    print(json.dumps(result, indent=2))
    # Exit with non-zero status if not clean or if there was an error
    if result.get("error") or not result.get("is_clean", False):
        sys.exit(1)
    else:
        sys.exit(0) 