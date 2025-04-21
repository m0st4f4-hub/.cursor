import subprocess
import json
import sys
import platform
import re
import shutil

# --- Configuration ---
# Add tools to check here. Key is tool name, value is the command to get its version.
# Use a list for command + args if needed.
# Use None as value if only checking for existence (path).
TOOLS_TO_CHECK = {
    "git": ["git", "--version"],
    "python": [sys.executable, "--version"], # Use sys.executable for correct python
    "pip": [sys.executable, "-m", "pip", "--version"],
    "npm": ["npm", "--version"],       # Optional: Only checked if package.json exists?
    "node": ["node", "--version"],      # Optional: Only checked if package.json exists?
    "pip-audit": ["pip-audit", "--version"], # Check for the specific tool we installed
    # Add linters or other project-specific tools
    # "eslint": ["eslint", "--version"],
    # "ruff": ["ruff", "--version"],
}

def get_tool_info(tool_name, version_command):
    """Checks for a tool's existence and tries to get its version."""
    info = {
        "name": tool_name,
        "found": False,
        "path": None,
        "version": None,
        "error": None
    }

    # 1. Check existence using shutil.which
    command_executable = version_command[0] if isinstance(version_command, list) else tool_name
    try:
        tool_path = shutil.which(command_executable)
        if tool_path:
            info["found"] = True
            info["path"] = tool_path
        else:
            info["error"] = "Not found in PATH."
            return info
    except Exception as e:
        info["error"] = f"Error checking path: {str(e)}"
        return info

    # 2. If found and version command exists, try to get version
    if info["found"] and version_command:
        try:
            process = subprocess.run(
                version_command,
                capture_output=True,
                text=True,
                check=False, # Don't raise exception on non-zero exit
                encoding='utf-8',
                errors='ignore',
                shell=(platform.system() == "Windows")
            )

            output = process.stdout.strip() or process.stderr.strip()

            if process.returncode == 0 and output:
                # Try to extract a version number (simple regex)
                match = re.search(r'(\d+\.\d+(\.\d+)*)', output)
                if match:
                    info["version"] = match.group(0)
                else:
                    info["version"] = output # Fallback to full output if regex fails
            elif output: # Got output but non-zero exit code
                info["error"] = f"Command ran, but exited {process.returncode}. Output: {output[:100]}"
                # Still treat as found, but version unknown
            else: # No output, non-zero exit
                info["error"] = f"Command failed with exit code {process.returncode}. No output."

        except FileNotFoundError:
            # Should have been caught by shutil.which, but as a fallback
            info["found"] = False
            info["path"] = None
            info["error"] = "Command not found despite initial check."
        except Exception as e:
            info["error"] = f"Error running version command: {str(e)}"

    return info

def verify_all_tools():
    """Verifies all tools specified in TOOLS_TO_CHECK."""
    results = {
        "tools": [],
        "all_critical_found": True # Assume true initially
    }
    for tool, command in TOOLS_TO_CHECK.items():
        tool_info = get_tool_info(tool, command)
        results["tools"].append(tool_info)
        # Define which tools are critical - adjust as needed
        critical_tools = ["git", "python", "pip"]
        if tool in critical_tools and not tool_info["found"]:
            results["all_critical_found"] = False

    return results

if __name__ == "__main__":
    verification_results = verify_all_tools()
    print(json.dumps(verification_results, indent=2))

    # Exit with non-zero status if critical tools are missing
    if not verification_results["all_critical_found"]:
        sys.exit(1)
    else:
        sys.exit(0) 