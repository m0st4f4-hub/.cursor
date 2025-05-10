# Ruleset for Autonomous Agent Framework

This repository contains the Markdown source for rules (`rules-md/`) and the compiled runtime rules (`.cursor/rules/`) defining a framework for autonomous AI agent execution. The `.cursor/rules/` directory is typically managed by a Git submodule as detailed in `rules-md/init.mdc`.

## Overview

The framework enables autonomous execution of tasks by specialized AI agents. Coordination is primarily managed by the `StrategicCoordinatorAgent` using an MCP (Multi-Capability Provider) task-based system, though initial requests may be triggered via chat. Each request typically involves a `requestId` and may utilize a knowledge wiki.

Key framework documents (found in `rules-md/` and compiled to `.cursor/rules/`):
*   `system.mdc`: Core system mandates and principles.
*   `protocol.mdc`: Defines the high-level operational protocol executed by `StrategicCoordinatorAgent`.
*   `loop.mdc`: Standard operational loop for most agents.
*   `concepts.mdc`: Key definitions and conceptual framework.
*   `roles.mdc`: Registry of defined agent roles.
*   Individual agent rule files in `rules-md/agents/` (e.g., `rules-md/agents/implementation-specialist.mdc`).

## Structure

*   `rules-md/`: Contains the Markdown source for all ruleset documents.
    *   `agents/`: Source files for specific agent roles (e.g., `implementation-specialist.md`).
    *   `templates/`: (Optional) Templates for new rule files.
*   `.cursor/rules/`: The runtime directory for compiled `.mdc` rule files, typically managed as a Git submodule (see `rules-md/init.mdc`).
    *   `agents/`: Compiled agent rule files (e.g., `implementation-specialist.mdc`).
    *   `tools/`: Custom Python scripts and PowerShell scripts accessible to agents.
*   `tools/`: Workspace-level tools, potentially including rule synchronization scripts.
*   `.gitignore`: Specifies intentionally untracked files.
*   `.gitattributes`: Defines attributes for pathnames (e.g., line endings).
*   `.gitmodules`: (If `.cursor/rules/` is a submodule) Defines the submodule configuration. 