import subprocess
import sys
import json
import platform
import traceback

# --- Configuration ---
# Add more package managers and their audit commands here
AUDIT_COMMANDS = {
    "npm": ["npm", "audit", "--json"], # Requires npm >= 6
    "pip": ["pip-audit", "-f", "json", "--progress-spinner", "off"] # Requires pip-audit installed
    # Add yarn, pnpm, etc. as needed
    # "yarn": ["yarn", "audit", "--json"]
}

# --- Functions ---

def parse_npm_audit(json_data):
    """Parses the JSON output of 'npm audit --json'."""
    summary = {
        "tool": "npm",
        "vulnerabilities_found": 0,
        "severity_counts": {"info": 0, "low": 0, "moderate": 0, "high": 0, "critical": 0},
        "vulnerable_packages": [],
        "error": None
    }
    try:
        if "error" in json_data:
            summary["error"] = json_data.get("error", {}).get("summary", "Unknown npm error")
            return summary

        metadata = json_data.get("metadata", {})
        summary["vulnerabilities_found"] = metadata.get("vulnerabilities", {}).get("total", 0)
        severities = metadata.get("vulnerabilities", {})
        for sev in summary["severity_counts"]:
            summary["severity_counts"][sev] = severities.get(sev, 0)

        vulnerabilities = json_data.get("vulnerabilities", {})
        for pkg_name, details in vulnerabilities.items():
            via_details = []
            if isinstance(details.get("via"), list):
                for item in details["via"]:
                     if isinstance(item, str):
                         via_details.append(item)
                     elif isinstance(item, dict):
                         via_details.append(f"{item.get('name', '?')} ({item.get('severity', '?')}) - {item.get('title', '?')}")

            summary["vulnerable_packages"].append({
                "name": pkg_name,
                "severity": details.get("severity", "unknown"),
                "fixAvailable": details.get("fixAvailable", False),
                "via": via_details
            })

    except Exception as e:
        summary["error"] = f"Error parsing npm audit results: {str(e)}"

    return summary

def parse_pip_audit(json_data):
    """Parses the JSON output of 'pip-audit --json'."""
    summary = {
        "tool": "pip",
        "vulnerabilities_found": 0,
        "severity_counts": {"low": 0, "medium": 0, "high": 0, "critical": 0}, # pip-audit uses medium
        "vulnerable_packages": [],
        "error": None
    }
    try:
        dependencies_analyzed = json_data.get("dependencies_analyzed", 0)
        vulnerabilities = json_data.get("vulnerabilities", [])
        summary["vulnerabilities_found"] = len(vulnerabilities)

        for vuln in vulnerabilities:
            pkg_name = vuln.get("name", "unknown_package")
            severity = vuln.get("severity", "unknown").lower()
            # Map pip-audit severity (medium) to our common keys if needed, or keep as is
            if severity in summary["severity_counts"]:
                 summary["severity_counts"][severity] += 1
            # else: handle unknown severities if necessary

            summary["vulnerable_packages"].append({
                "name": pkg_name,
                "version": vuln.get("version", "unknown"),
                "severity": severity,
                "id": vuln.get("id", "N/A"),
                "description": vuln.get("description", "N/A")
            })

    except Exception as e:
        summary["error"] = f"Error parsing pip-audit results: {str(e)}"

    return summary

def run_audit(manager_type):
    """Runs the audit command for the specified package manager."""
    if manager_type not in AUDIT_COMMANDS:
        return {"tool": manager_type, "error": "Unsupported package manager type."}

    command = AUDIT_COMMANDS[manager_type]
    print(f"DEBUG: Running command: {' '.join(command)}", file=sys.stderr)

    try:
        # Run the audit command
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            check=False, # Don't fail on non-zero exit (audit tools often exit non-zero if vulns found)
            shell=(platform.system() == "Windows") # May need shell on Windows
        )

        output = process.stdout
        stderr_output = process.stderr
        print(f"DEBUG: Command stdout (first 500 chars): {output[:500]}", file=sys.stderr)
        print(f"DEBUG: Command stderr: {stderr_output}", file=sys.stderr)
        print(f"DEBUG: Command return code: {process.returncode}", file=sys.stderr)

        # Handle cases where the command failed to run or produced no JSON
        if not output.strip() and process.returncode != 0:
             error_message = f"Command failed with exit code {process.returncode}. Stderr: {stderr_output.strip()}"
             # Specific check for pip-audit not found
             if manager_type == "pip" and ("command not found" in stderr_output or "'pip-audit' is not recognized" in stderr_output):
                 error_message = "'pip-audit' command not found. Please install it (pip install pip-audit)."
             return {"tool": manager_type, "error": error_message}
        if not output.strip() and process.returncode == 0:
             # Command ran but produced no output (might happen if no dependencies)
             return {"tool": manager_type, "vulnerabilities_found": 0, "severity_counts": {}, "vulnerable_packages": [], "error": None, "message": "Command ran successfully, no JSON output produced (potentially no dependencies?)."}

        # Parse the JSON output
        try:
            json_data = json.loads(output)
        except json.JSONDecodeError as json_e:
            return {"tool": manager_type, "error": f"Failed to decode JSON output: {json_e}. Raw output: {output[:500]}"}

        # Call the appropriate parser
        if manager_type == "npm":
            return parse_npm_audit(json_data)
        elif manager_type == "pip":
            return parse_pip_audit(json_data)
        else:
            return {"tool": manager_type, "error": "No parser implemented for this manager."}

    except FileNotFoundError:
        return {"tool": manager_type, "error": f"Command '{command[0]}' not found. Is it installed and in PATH?"}
    except Exception as e:
        print(f"FATAL ERROR running audit for {manager_type}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {"tool": manager_type, "error": f"An unexpected error occurred: {str(e)}"}

# --- Main Execution ---
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_dependencies.py <npm|pip>", file=sys.stderr)
        sys.exit(1)

    manager = sys.argv[1].lower()

    result = run_audit(manager)

    # Print the final summary JSON to stdout
    print(json.dumps(result, indent=2))

    # Exit with non-zero code if vulnerabilities were found or an error occurred
    if result.get("error") or result.get("vulnerabilities_found", 0) > 0:
        sys.exit(1)
    else:
        sys.exit(0) 