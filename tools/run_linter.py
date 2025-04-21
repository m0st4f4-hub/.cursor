import subprocess
import sys
import json
import platform
import traceback
import os

# --- Configuration ---
LINTER_COMMANDS = {
    "python": {
        "lint": ["flake8", "--format=%(path)s:%(row)d:%(col)d:%(code)s:%(text)s"], # Custom format for parsing
        "format": ["black"]
    }
    # Add commands for other languages (e.g., eslint, prettier for javascript)
}

# --- Functions ---

def parse_flake8_output(output_lines):
    """Parses the custom format output of flake8."""
    issues = []
    for line in output_lines:
        if not line.strip():
            continue
        parts = line.split(':', maxsplit=4)
        if len(parts) == 5:
            try:
                issues.append({
                    "file": parts[0],
                    "line": int(parts[1]),
                    "column": int(parts[2]),
                    "code": parts[3],
                    "message": parts[4].strip()
                })
            except ValueError:
                # Handle cases where parsing fails for a line
                issues.append({"file": "parsing_error", "message": line})
        else:
            # Handle lines that don't match the expected format
             issues.append({"file": "format_error", "message": line})
    return issues

def run_tool(language, action, target):
    """Runs the lint or format command for the specified language and target."""
    if language not in LINTER_COMMANDS or action not in LINTER_COMMANDS[language]:
        return {"language": language, "action": action, "target": target, "success": False, "error": "Unsupported language or action."}

    base_command = LINTER_COMMANDS[language][action]
    full_command = base_command + [target]

    print(f"DEBUG: Running command: {' '.join(full_command)}", file=sys.stderr)
    summary = {
        "language": language,
        "action": action,
        "target": target,
        "success": False,
        "error": None,
        "issues": [],
        "issue_count": 0,
        "files_checked": [], # Placeholder, specific tools might provide this
        "files_formatted": 0 # For formatters
    }

    try:
        process = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            check=False, # Handle exit codes manually
            shell=(platform.system() == "Windows") # May need shell on Windows
        )

        stdout = process.stdout.strip()
        stderr = process.stderr.strip()
        exit_code = process.returncode

        print(f"DEBUG: stdout: {stdout}", file=sys.stderr)
        print(f"DEBUG: stderr: {stderr}", file=sys.stderr)
        print(f"DEBUG: exit code: {exit_code}", file=sys.stderr)

        if action == "lint":
            if language == "python": # flake8 specific handling
                # Flake8 with custom format outputs issues to stdout
                # It typically exits 0 even if issues are found
                summary["issues"] = parse_flake8_output(stdout.splitlines())
                summary["issue_count"] = len(summary["issues"])
                # Assume success unless the command itself failed catastrophically (e.g., not found)
                # A non-zero exit code might indicate a config error or inability to run
                summary["success"] = exit_code == 0
                if exit_code != 0 and stderr:
                     summary["error"] = f"Flake8 execution error (Exit Code: {exit_code}). Stderr: {stderr}"
                elif exit_code !=0:
                     summary["error"] = f"Flake8 execution error (Exit Code: {exit_code}). Check configuration or paths."

            # Add elif for other language linters here

        elif action == "format":
            if language == "python": # black specific handling
                # Black exits 0 if no changes needed or successful formatting
                # Black exits 1 if files were reformatted
                # Black exits >1 on errors
                summary["success"] = exit_code in [0, 1]
                if exit_code == 1:
                    # Need to parse stderr to see which files were changed
                    # Simple approach: just indicate reformatting occurred
                     summary["message"] = "Files were reformatted."
                     # Count formatted files from stderr (crude parsing)
                     summary["files_formatted"] = stderr.count('reformatted')
                elif exit_code == 0:
                    summary["message"] = "No changes needed or formatting applied successfully."
                elif exit_code > 1:
                    summary["error"] = f"Black execution error (Exit Code: {exit_code}). Stderr: {stderr}"

            # Add elif for other language formatters here

        # Handle command not found errors more explicitly
        if exit_code == 127 or ("command not found" in stderr or f"'{base_command[0]}' is not recognized" in stderr):
             summary["success"] = False
             summary["error"] = f"Command '{base_command[0]}' not found. Is it installed and in PATH?"

    except FileNotFoundError:
        summary["success"] = False
        summary["error"] = f"Command '{base_command[0]}' not found. Is it installed and in PATH?"
    except Exception as e:
        summary["success"] = False
        summary["error"] = f"An unexpected error occurred: {str(e)}"
        print(f"FATAL ERROR running tool for {language}/{action}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

    return summary

# --- Main Execution ---
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python run_linter.py <language> <action> <target>", file=sys.stderr)
        print("  language: python, ...", file=sys.stderr)
        print("  action: lint, format", file=sys.stderr)
        print("  target: file or directory path", file=sys.stderr)
        sys.exit(1)

    lang = sys.argv[1].lower()
    act = sys.argv[2].lower()
    tgt = sys.argv[3]

    # Basic validation: Check if target exists
    if not os.path.exists(tgt):
         result = {"language": lang, "action": act, "target": tgt, "success": False, "error": f"Target path does not exist: {tgt}"}
         print(json.dumps(result, indent=2))
         sys.exit(1)

    result = run_tool(lang, act, tgt)

    # Print the final summary JSON to stdout
    print(json.dumps(result, indent=2))

    # Exit code logic:
    # Exit 0 if successful (lint found 0 issues or format was ok/applied)
    # Exit 1 if lint found issues OR format error OR other error
    exit_code = 0
    if not result["success"] or (act == "lint" and result["issue_count"] > 0):
        exit_code = 1

    sys.exit(exit_code) 