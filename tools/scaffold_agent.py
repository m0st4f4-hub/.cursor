import sys
import os
import re
import json

AGENT_RULES_DIR = ".cursor/rules/agents"

def sanitize_filename(name):
    """Converts CamelCase or PascalCase to kebab-case and removes invalid chars."""
    # Convert CamelCase/PascalCase to snake_case first
    name = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    # Replace underscores and spaces with hyphens
    name = name.replace('_', '-').replace(' ', '-')
    # Remove invalid filename characters (allow letters, numbers, hyphens)
    name = re.sub(r'[^a-z0-9-]', '', name)
    # Remove leading/trailing hyphens and collapse multiple hyphens
    name = re.sub(r'-+', '-', name).strip('-')
    return name

def generate_rule_content(agent_name_pascal):
    """Generates the basic markdown content for the agent rule file."""
    return f"""# Agent Rule: {agent_name_pascal}

## Role Description
(TODO: Describe the primary purpose and responsibilities of the {agent_name_pascal}.)

## Core Tasks
- (TODO: List the specific actions this agent performs, e.g., Analyze X, Generate Y, Refactor Z.)
- ...

## Input
- `handoffMessage`: (String) Instructions from the previous agent.
- `observations`: (List) Data/findings from previous agents (via request log).
- (TODO: List any other specific inputs required, e.g., file paths, configuration data).

## Output
- `observations`: (List) Key findings, analysis results, or outcomes of actions taken.
- `nextAgent`: (String) The role of the agent to hand off to (e.g., "BuilderAgent", "AuditAgent", "Overmind", null).
- `handoffMessage`: (String) Clear instructions for the `nextAgent`.
- (TODO: Specify any files created/modified or other outputs).

## Tools Used
- (TODO: List the primary tools this agent will utilize, e.g., `read_file`, `edit_file`, `custom_tool.py`).
- ...

## Handoff Conditions
- **To `BuilderAgent`:** When ... (e.g., research is complete).
- **To `AuditAgent`:** When ... (e.g., implementation is complete).
- **To `Overmind`:** When ... (e.g., task is fully complete or requires re-planning).
- **To `null` (Halt):** When ... (e.g., critical error or request completion).

## Notes
- (TODO: Add any specific constraints, edge cases, or important considerations for this agent).
"""

def scaffold_agent(agent_name):
    """Creates the agent rule file."""
    if not agent_name or not re.match(r'^[A-Z][a-zA-Z0-9]*Agent$', agent_name):
        return {"success": False, "error": "Invalid agent name. Must be PascalCase ending in 'Agent' (e.g., 'MyNewAgent')."}

    file_basename = sanitize_filename(agent_name)
    if not file_basename:
        return {"success": False, "error": "Could not generate a valid filename from agent name."}

    filename = f"{file_basename}.mdc"
    filepath = os.path.join(AGENT_RULES_DIR, filename)

    try:
        # Ensure the target directory exists
        os.makedirs(AGENT_RULES_DIR, exist_ok=True)

        # Check if the file already exists
        if os.path.exists(filepath):
            return {"success": False, "error": f"Rule file already exists: {filepath}"}

        # Generate content and write the file
        content = generate_rule_content(agent_name)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return {"success": True, "message": f"Agent rule file created: {filepath}", "filepath": filepath}

    except Exception as e:
        return {"success": False, "error": f"Failed to create rule file: {str(e)}"}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"success": False, "error": "Usage: python scaffold_agent.py <AgentNameInPascalCase>"}), file=sys.stderr)
        sys.exit(1)

    agent_name_arg = sys.argv[1]
    result = scaffold_agent(agent_name_arg)

    print(json.dumps(result, indent=2))

    if not result["success"]:
        sys.exit(1)
    else:
        sys.exit(0) 