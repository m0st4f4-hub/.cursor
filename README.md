# Autonomous Agent Framework Ruleset

This repository defines the operational framework and rules for a system of autonomous AI agents. The core specification is detailed in `rules-md/system.md`.

## Overview

The framework facilitates the execution of complex tasks by a coordinated collective of specialized AI agents. Task management and agent coordination are primarily handled via the MCP (Model Context Protocol) Task Manager, with Chat Triggers as a legacy fallback. The system is designed for robust, rigorous, and verifiable task execution, with a strong emphasis on adherence to defined protocols and mandates.

The central document, `rules-md/system.md` (Unified Framework Specification), consolidates:
*   System Overview & Global Mandates
*   Core Concepts & Glossary
*   Initialization Procedure (`rules-md/init.md`)
*   Agent Execution Framework & Core Loop (`rules-md/loop.md`)
*   Ultra‑Deep Thinking Protocol (`rules-md/protocol.md`)
*   Agent Roles Registry (`rules-md/roles.md`)

Individual agent behaviors are defined by their respective rule files located in `rules-md/agents/`.

## Repository Structure

*   **`README.md`**: This file, providing an overview of the repository.
*   **`rules-md/`**: Contains the Markdown source for all framework specifications and agent rules.
    *   `system.md`: The primary Unified Framework Specification document.
    *   `loop.md`: Defines the core agent execution loop.
    *   `concepts.md`: Explains core concepts and terminology.
    *   `roles.md`: Lists and describes available agent roles.
    *   `init.md`: Details the framework initialization procedure.
    *   `protocol.md`: Describes the Ultra‑Deep Thinking Protocol, mainly for strategic agents like Overmind.
    *   `agents/`: Contains Markdown rule files for individual agent roles (e.g., `Overmind.md`, `InitializationAgent.md`).
*   **`rules/`**: This directory is intended to hold the processed or runtime-effective rules derived from the `rules-md/` sources. (The `.gitignore` indicates this directory is tracked).
*   **`tools/`**: Contains supporting tools and libraries for the framework.
    *   `rules_sync_lib/`: Likely contains libraries or scripts related to synchronizing or managing the rules.
*   **`.gitignore`**: Specifies intentionally untracked files and directories. Notably, it ignores `.cursor/` but tracks `rules/`.
*   **`.gitattributes`**: Defines attributes for pathnames (e.g., line endings).

## Key Principles

*   **MCP Task Manager:** Preferred for task coordination and state management.
*   **Role Adherence:** Agents operate strictly within their defined roles.
*   **Global Mandates:** Non-negotiable rules outlined in `system.md` that all agents must follow.
*   **Verification:** Emphasis on multi-method verification for all actions and outputs.
*   **Self-Improvement:** The framework includes mechanisms for self-improvement via designated agents and processes.

For detailed information on any aspect of the framework, please refer to `rules-md/system.md` and the other referenced documents within the `rules-md/` directory. 