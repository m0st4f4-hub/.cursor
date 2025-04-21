import subprocess
import sys
import json
import re
import platform
import traceback # Added for detailed exception printing

# Mapping of simple tool names to commands/arguments needed to get version
# Add more tools here as needed
TOOL_COMMANDS = {
    "python": ["python", "--version"],
    "node": ["node", "--version"],
    "git": ["git", "--version"],
    "npm": ["npm", "--version"],
    "yarn": ["yarn", "--version"],
    "docker": ["docker", "--version"],
    "java": ["java", "-version"], # Note: java prints to stderr
    "pip": ["pip", "--version"],
    "python3": ["python3", "--version"] # For systems where python maps to python2
}

def get_tool_version(tool_name):
    """Attempts to get the version of a given tool."""
    print(f"DEBUG: Checking tool: {tool_name}", file=sys.stderr) # Debug print
    if tool_name not in TOOL_COMMANDS:
        print(f"DEBUG: Unknown tool: {tool_name}", file=sys.stderr) # Debug print
        return "unknown tool"

    command = TOOL_COMMANDS[tool_name]
    print(f"DEBUG: Command for {tool_name}: {command}", file=sys.stderr) # Debug print
    try:
        # Force UTF-8 encoding, capture both stdout and stderr
        # Use shell=True only if necessary, be cautious. Prefer direct command list.
        # Some tools like java print version to stderr.
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore', # Ignore decoding errors for unexpected output
            check=False, # Don't raise exception on non-zero exit code
            shell=(platform.system() == "Windows") # May need shell=True on Windows for some commands
        )

        output = process.stdout + process.stderr # Combine stdout and stderr
        print(f"DEBUG: Raw output for {tool_name}: '{output.strip()}'", file=sys.stderr) # Debug print
        print(f"DEBUG: Return code for {tool_name}: {process.returncode}", file=sys.stderr) # Debug print

        if process.returncode != 0 and not output.strip():
             # If return code is non-zero AND there's no output, assume not found
            print(f"DEBUG: Result for {tool_name}: not found (non-zero exit + no output)", file=sys.stderr) # Debug print
            return "not found"

        # Regex to find common version patterns (e.g., X.Y.Z, X.Y)
        # Added patterns for more variations like 'npm 8.19.2', 'pip 22.3.1 from ...'
        version_match = re.search(r'(\d+\.\d+(\.\d+)?(\.\d+)?([a-zA-Z0-9.-]*)?)', output)

        if version_match:
            version = version_match.group(1)
            print(f"DEBUG: Result for {tool_name}: {version} (parsed)", file=sys.stderr) # Debug print
            return version # Return the first captured version string
        elif output.strip():
             # If we got some output but couldn't parse a version, return the output
             # return f"output captured, version unclear: {output.strip()[:100]}" # Optionally limit length
             print(f"DEBUG: Result for {tool_name}: version format unrecognized", file=sys.stderr) # Debug print
             return "version format unrecognized"
        else:
            # No output and possibly zero return code (unusual)
            print(f"DEBUG: Result for {tool_name}: not found (no output)", file=sys.stderr) # Debug print
            return "not found (no output)"

    except FileNotFoundError:
        print(f"DEBUG: Result for {tool_name}: not found (FileNotFoundError)", file=sys.stderr) # Debug print
        return "not found"
    except Exception as e:
        print(f"DEBUG: Error checking {tool_name}: {e}", file=sys.stderr) # Debug print
        traceback.print_exc(file=sys.stderr) # Print full traceback
        return f"error: {str(e)}"

if __name__ == "__main__":
    results = {}
    try: # Added try block
        tools_to_check = sys.argv[1:]
        if not tools_to_check:
            # Default tools if none are provided
            print("DEBUG: No tools specified, using defaults [python, node, git]", file=sys.stderr)
            tools_to_check = ["python", "node", "git"]
        else:
             print(f"DEBUG: Tools specified: {tools_to_check}", file=sys.stderr)

        for tool in tools_to_check:
            tool_lower = tool.lower() # Normalize to lowercase
            results[tool_lower] = get_tool_version(tool_lower)

        # Print results as JSON to stdout
        print(json.dumps(results, indent=2))

    except Exception as main_e: # Added except block
        print(f"FATAL ERROR in main execution: {main_e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr) # Print full traceback
        # Still attempt to print any results gathered so far
        print(json.dumps(results, indent=2)) # Print potentially partial results
        sys.exit(1) # Exit with error code 