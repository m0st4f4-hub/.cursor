# Ruleset for Autonomous Agent Framework

This repository contains the core rules (`.cursor/rules/`) and documentation (`rules-md/`) defining a framework for autonomous AI agent execution.

## Overview

The framework defined by these rules enables autonomous execution of tasks by specialized AI agents, coordinated through **Chat Triggers and a Knowledge Wiki** (`<requestId>-wiki.md`) and a defined set of allowed tools. Refer to the `.cursor/rules/shared-core.mdc` and individual agent files for detailed operational logic.

## Structure

*   `/rules`: Contains the core rulesets, agent prompts, and tools.
    *   `/agents`: Specific prompts and configurations for different agent roles.
    *   `/tools`: Custom Python scripts and PowerShell scripts accessible to agents.
*   `.gitignore`: Specifies intentionally untracked files that Git should ignore.
*   `.gitmodules`: Defines the `.cursor` ruleset submodule (if applicable). 