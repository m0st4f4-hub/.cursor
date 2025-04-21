import json
import sys
import os
from datetime import datetime, timezone

LOGS_DIR = "logs"

def parse_log_entry(entry):
    """Safely parses timestamp and extracts key info from a log entry."""
    parsed_entry = {
        "agentRole": entry.get("agentRole", "UnknownAgent"),
        "status": entry.get("status", "unknown"),
        "nextAgent": entry.get("nextAgent"),
        "timestamp": None,
        "error": None # Placeholder for potential errors in observations
    }
    try:
        ts_str = entry.get("timestamp")
        if ts_str:
            # Attempt to parse various ISO 8601 formats
            try:
                # Try with microseconds
                parsed_entry["timestamp"] = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            except ValueError:
                # Try without microseconds
                parsed_entry["timestamp"] = datetime.strptime(ts_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                parsed_entry["timestamp"] = parsed_entry["timestamp"].replace(tzinfo=timezone.utc)

        # Check for errors within observations (simple check for now)
        observations = entry.get("observations", [])
        for obs in observations:
            if isinstance(obs, str) and ("error" in obs.lower() or "failed" in obs.lower()):
                parsed_entry["error"] = obs
                break # Take the first error-like observation
            elif isinstance(obs, dict) and obs.get("type") == "error":
                 parsed_entry["error"] = obs.get("message", "Unknown error in observation")
                 break

    except Exception as e:
        # Log parsing errors specific to this entry if needed, but don't stop analysis
        pass
    return parsed_entry

def analyze_log_file(request_id):
    """Analyzes a specific request log file."""
    log_filename = f"{request_id}.json"
    log_filepath = os.path.join(LOGS_DIR, log_filename)

    summary = {
        "requestId": request_id,
        "logFile": log_filepath,
        "found": False,
        "entryCount": 0,
        "agentsUsed": [],
        "startTime": None,
        "endTime": None,
        "durationSeconds": None,
        "finalStatus": "Unknown",
        "finalNextAgent": None,
        "errorsEncountered": [],
        "error": None # For errors reading/parsing the log file itself
    }

    if not os.path.exists(log_filepath):
        summary["error"] = "Log file not found."
        return summary

    summary["found"] = True

    try:
        with open(log_filepath, 'r', encoding='utf-8') as f:
            log_data = json.load(f)

        if not isinstance(log_data, list):
            summary["error"] = "Log file does not contain a JSON list."
            return summary

        summary["entryCount"] = len(log_data)
        if not log_data:
            summary["error"] = "Log file is empty."
            return summary

        parsed_entries = [parse_log_entry(entry) for entry in log_data]
        # Filter out entries where timestamp parsing failed, if necessary
        valid_entries = [p for p in parsed_entries if p["timestamp"]]
        valid_entries.sort(key=lambda x: x["timestamp"]) # Ensure sorted by time

        if not valid_entries:
             summary["error"] = "No log entries with valid timestamps found."
             return summary

        summary["agentsUsed"] = sorted(list(set(entry["agentRole"] for entry in valid_entries)))
        summary["startTime"] = valid_entries[0]["timestamp"].isoformat()
        summary["endTime"] = valid_entries[-1]["timestamp"].isoformat()

        duration = valid_entries[-1]["timestamp"] - valid_entries[0]["timestamp"]
        summary["durationSeconds"] = round(duration.total_seconds(), 2)

        summary["finalStatus"] = valid_entries[-1]["status"]
        summary["finalNextAgent"] = valid_entries[-1]["nextAgent"]

        summary["errorsEncountered"] = [e["error"] for e in parsed_entries if e["error"]]

    except json.JSONDecodeError as e:
        summary["error"] = f"Failed to decode JSON: {str(e)}"
    except Exception as e:
        summary["error"] = f"An unexpected error occurred during analysis: {str(e)}"

    return summary

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"success": False, "error": "Usage: python analyze_log.py <requestId>"}), file=sys.stderr)
        sys.exit(1)

    request_id_arg = sys.argv[1]
    # Basic validation for request ID (e.g., prevent path traversal)
    if not re.match(r'^[a-zA-Z0-9_-]+$', request_id_arg):
        print(json.dumps({"success": False, "error": "Invalid requestId format."}), file=sys.stderr)
        sys.exit(1)

    result = analyze_log_file(request_id_arg)

    print(json.dumps(result, indent=2))

    # Exit with non-zero if log not found or major error occurred
    if not result["found"] or result.get("error"):
        sys.exit(1)
    else:
        sys.exit(0) 