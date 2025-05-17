# MCP Configuration for Project Manager Suite (`.cursor/`)

This directory is central to the Model Context Protocol (MCP) functionality within the MCP Project Manager Suite. It houses the rules that define agent behaviors, system protocols, and supporting tools for managing these configurations.

## Directory Structure and Purpose

-   **`rules/`**:
    -   This is the primary directory for all **`.mdc` (Markdown Context) rule files**. These files define the operational logic for AI agents and the overall MCP system within this project.
    -   It contains:
        -   **Agent-Specific Rules**: Files like `project-manager.mdc`, `knowledge-curator.mdc`, `code-structure-specialist.mdc`, etc., which define the roles, capabilities, and behaviors of individual AI agents.
        -   **Core System & Protocol Definitions**: Files such as `system.mdc` (overall system mandates), `loop.mdc` (standard agent execution cycle), `protocol.mdc` (specific operational protocols), `concepts.mdc` (glossary and concepts), `roles.mdc` (agent role registry), and `init.mdc` (initialization procedures). These files provide the foundational framework for agent operations.
    -   These rules are directly used by the MCP integration (e.g., `fastapi-mcp` in the backend) to orchestrate agent actions.

-   **`tools/`**:
    -   This directory contains Python utility scripts to support the management and processing of the `.mdc` rules.
    -   **`sync_rules.py`**: This script may be used to synchronize rules between different locations or formats, or to perform validation or processing steps on the rule files in `rules/`. (Its exact function would require reading the script).
    -   **`generate_description_index.py`**: This script likely generates an index or summary from the descriptions or metadata within the `.mdc` rule files, potentially for easier navigation, understanding, or for use by other agents/tools. (Its exact function would require reading the script).
    -   **`__init__.py`**: Makes the `tools/` directory a Python package.

-   **`.gitignore`**:
    -   Specifies intentionally untracked files and directories within the `.cursor/` configuration. It's important to check its contents to understand what is and isn't committed to version control (e.g., local scratchpads, temporary files).

-   **`.gitattributes`**:
    -   Defines attributes for pathnames, often used to manage line endings or other Git behaviors for files within this directory.

-   **`README.md`**: This file.

## Usage and Importance

The configurations within this `.cursor/` directory are critical for the autonomous and agentic capabilities of the MCP Project Manager Suite. Modifications to the `.mdc` files in `rules/` will directly impact how AI agents behave and interact with the system.

For a deeper understanding of how these rules are structured and how to develop agents, refer to the "Agent Developer Onboarding" section in the main project's `ONBOARDING.md` file, and the "Agent Interaction Model" in `ARCHITECTURE.md`. 