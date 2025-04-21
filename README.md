# Rules Repository

This repository contains the configuration rules, agent definitions, and custom tools for the Unified Agent Framework.

## Structure

*   `/rules`: Contains the core rulesets, agent prompts, and tools.
    *   `/agents`: Specific prompts and configurations for different agent roles.
    *   `/tools`: Custom Python scripts and PowerShell scripts accessible to agents.
*   `.gitignore`: Specifies intentionally untracked files that Git should ignore.
*   `.gitmodules`: Defines the `.cursor` ruleset submodule (if applicable).

## Purpose

The framework defined by these rules enables autonomous execution of tasks by specialized AI agents, coordinated through log files and a defined set of allowed tools. Refer to the `.cursor/rules/shared-core.mdc` and individual agent files for detailed operational logic. 