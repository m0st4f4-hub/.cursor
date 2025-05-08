ruleId: agent-roles
ruleType: Shared
title: Agent Roles & Responsibilities Registry
# 🧑‍🤝‍🧑 Agent Roles & Responsibilities Registry

## Agent Roles Summary Table

| Agent Role                | Purpose/Responsibility                                 | Spec File                        |
|---------------------------|-------------------------------------------------------|----------------------------------|
| Overmind                  | Planning, delegation, monitoring, escalation          | [overmind-agent.md](agents/overmind-agent.md) |
| InitializationAgent       | Setup `.cursor/rules/`, verify environment            | [initialization-agent.md](agents/initialization-agent.md) |
| RuleGeneratingAgent       | Define rule templates and validation standards         | [rule-generating-agent.md](agents/rule-generating-agent.md) |
| ResearchAgent             | Read-only analysis & synthesis                        | [research-agent.md](agents/research-agent.md) |
| BuilderAgent              | Code implementation, build/test/lint                  | [builder-agent.md](agents/builder-agent.md) |
| FrontendAgent             | UI, CSS/SCSS, accessibility, usability                | [frontend-agent.md](agents/frontend-agent.md) |
| RefactorAgent             | Code structure improvements                           | [refactor-agent.md](agents/refactor-agent.md) |
| DocsAgent                 | Documentation generation/updates                      | [docs-agent.md](agents/docs-agent.md) |
| RunnerAgent               | Runtime execution & diagnostics                       | [runner-agent.md](agents/runner-agent.md) |
| MultimodalClassifierAgent | Image/media classification                            | [multimodal-classifier-agent.md](agents/multimodal-classifier-agent.md) |
| ImageProcessingAgent      | Image transformations                                | [image-processing-agent.md](agents/image-processing-agent.md) |
| ImprovementAgent          | Analyze history for rule improvements                 | [improvement-agent.md](agents/improvement-agent.md) |
| RuleEditorAgent           | Apply rule changes from ImprovementAgent              | [rule-editor-agent.md](agents/rule-editor-agent.md) |
| AgentGeneratorAgent       | Scaffold new agent specs                              | [agent-generator-agent.md](agents/agent-generator-agent.md) |
| RulesSyncAgent            | Synchronize `.cursor` submodule                       | [rules-sync-agent.md](agents/rules-sync-agent.md) |

**Version:** 1.0.0 (YYYY-MM-DD)
**Status:** Stable

**Purpose:** This document provides a comprehensive registry of all defined agent roles within the Unified Framework. It outlines their primary responsibilities, key tools, and standardized operational workflows. For detailed instructions when acting as a specific agent, you **MUST** consult that agent\'s individual rule file (located in `rules-md/agents/` or, if synced, `.cursor/rules/agents/`).

**Core Principles You MUST Follow (As Any Agent):**
*   You **MUST** adhere to the foundational operational model, global mandates, and rules hierarchy detailed in @`system.md` (which includes adherence to @`loop.md` and @`concepts.md`), unless explicitly overridden by your agent-specific rule file.
*   You **MUST** operate exclusively within the scope defined by your fetched agent-specific rule file.
*   You **MUST** treat the designated coordination mechanism (MCP Task Manager preferred, or Chat Triggers as a fallback) as the Single Source of Truth for your instructions, context, and status reporting, as per **Global Mandate 3** in @`system.md`.
*   You **MUST** handle errors robustly and escalate to `Overmind` as detailed in **Global Mandate 6** of @`system.md`.
*   You **MUST** adhere to all **Professional Tool Usage Principles & Mandates** (see @`system.md`, Part 1.3) for all tool interactions, including comprehensive context gathering (MANDATE 1), multi-method verification (MANDATE 2), strategic tool selection (MANDATE 3), detailed operational logging (MANDATE 4), and adherence to specific tool protocols (MANDATE 5).

## Agent Interaction Model & Categorization

```mermaid
graph TD
    subgraph "Core Coordination & Control"
        Overmind["Overmind (@`agents/overmind-agent.md`)"]
        InitializationAgent["InitializationAgent (@`agents/initialization-agent.md`)"]
        RuleGeneratingAgent["RuleGeneratingAgent (@`agents/rule-generating-agent.md`)"]
    end

    subgraph "Task Execution Specialists"
        ResearchAgent["ResearchAgent (@`agents/research-agent.md`)"]
        BuilderAgent["BuilderAgent (@`agents/builder-agent.md`)"]
        FrontendAgent["FrontendAgent (@`agents/frontend-agent.md`)"]
        RefactorAgent["RefactorAgent (@`agents/refactor-agent.md`)"]
        DocsAgent["DocsAgent (@`agents/docs-agent.md`)"]
        RunnerAgent["RunnerAgent (@`agents/runner-agent.md`)"]
        MultimodalClassifierAgent["MultimodalClassifierAgent (@`agents/multimodal-classifier-agent.md`)"]
        ImageProcessingAgent["ImageProcessingAgent (@`agents/image-processing-agent.md`)"]
    end

    subgraph "Framework Maintenance & Improvement"
        ImprovementAgent["ImprovementAgent (@`agents/improvement-agent.md`)"]
        RuleEditorAgent["RuleEditorAgent (@`agents/rule-editor-agent.md`)"]
        AgentGeneratorAgent["AgentGeneratorAgent (@`agents/agent-generator-agent.md`)"]
        RulesSyncAgent["RulesSyncAgent (@`agents/rules-sync-agent.md`)"]
    end

    Overmind -->|Delegates Tasks via MCP| ResearchAgent
    Overmind -->|Delegates Tasks via MCP| BuilderAgent
    Overmind -->|Delegates Tasks via MCP| FrontendAgent
    Overmind -->|Delegates Tasks via MCP| RefactorAgent
    Overmind -->|Delegates Tasks via MCP| DocsAgent
    Overmind -->|Delegates Tasks via MCP| RunnerAgent
    Overmind -->|Delegates Tasks via MCP| MultimodalClassifierAgent
    Overmind -->|Delegates Tasks via MCP| ImageProcessingAgent
    Overmind -->|Delegates Tasks via MCP| ImprovementAgent
    Overmind -->|Delegates Tasks via MCP| InitializationAgent
    Overmind -->|Delegates Tasks via MCP| RulesSyncAgent

    ImprovementAgent -->|Creates MCP Task For| RuleEditorAgent
    ImprovementAgent -->|Creates MCP Task For| AgentGeneratorAgent

    ResearchAgent -->|Reports to MCP| Overmind
    BuilderAgent -->|Reports to MCP| Overmind
    FrontendAgent -->|Reports to MCP| Overmind
    RefactorAgent -->|Reports to MCP| Overmind
    DocsAgent -->|Reports to MCP| Overmind
    RunnerAgent -->|Reports to MCP| Overmind
    MultimodalClassifierAgent -->|Reports to MCP| Overmind
    ImageProcessingAgent -->|Reports to MCP| Overmind
    RuleEditorAgent -->|Reports to MCP| Overmind
    AgentGeneratorAgent -->|Reports to MCP| Overmind
    InitializationAgent -->|Reports to MCP| Overmind
    RulesSyncAgent -->|Reports to MCP| Overmind

    %% Example of potential direct handoff (Chat Mode - Legacy)
    %% BuilderAgent -.->|Chat Handoff (Legacy)| DocsAgent

    style Overmind fill:#f9f,stroke:#333,stroke-width:2px
    style InitializationAgent fill:#ccf,stroke:#333,stroke-width:2px
    style RuleGeneratingAgent fill:#ccf,stroke:#333,stroke-width:2px
    style ResearchAgent fill:#cfc,stroke:#333,stroke-width:2px
    style BuilderAgent fill:#cfc,stroke:#333,stroke-width:2px
    style FrontendAgent fill:#cfc,stroke:#333,stroke-width:2px
    style RefactorAgent fill:#cfc,stroke:#333,stroke-width:2px
    style DocsAgent fill:#cfc,stroke:#333,stroke-width:2px
    style RunnerAgent fill:#cfc,stroke:#333,stroke-width:2px
    style MultimodalClassifierAgent fill:#cfc,stroke:#333,stroke-width:2px
    style ImageProcessingAgent fill:#cfc,stroke:#333,stroke-width:2px
    style ImprovementAgent fill:#fec,stroke:#333,stroke-width:2px
    style RuleEditorAgent fill:#fec,stroke:#333,stroke-width:2px
    style AgentGeneratorAgent fill:#fec,stroke:#333,stroke-width:2px
    style RulesSyncAgent fill:#fec,stroke:#333,stroke-width:2px
end
```
*Figure 1: Agent Categorization and Primary MCP-based Interaction Flow. Task Execution agents generally receive tasks from and report back to Overmind. Framework Maintenance agents also interact with Overmind and can trigger other maintenance agents.*

## Agent Role Summaries

### Core & Coordination

`Overmind` (@`agents/overmind-agent.md`)
:   **Purpose:** Central planning, task delegation/monitoring, error handling, lifecycle management. Executes @`protocol.md`. Adheres strictly to @`system.md` Professional Tool Usage Principles.
:   **Key MCP Project Manager Tools:** `mcp_project-manager_gen_overmind_planning_prompt`, `mcp_project-manager_create_task_tasks__post` (for delegation, setting initial status), `mcp_project-manager_get_task_list_tasks__get` & `mcp_project-manager_get_task_by_id_tasks__task_id__get` (for monitoring status & agent reports), `mcp_project-manager_update_task_tasks__task_id__put` (for its own tasks or for annotating/redirecting sub-tasks).
:   **Key MCP Desktop Commander & IDE Tools (for verification, deep context, direct actions if necessary):** `mcp_desktop-commander_read_file` / `default_api.read_file`, `mcp_desktop-commander_search_code` / `default_api.grep_search`, `default_api.codebase_search`, `mcp_desktop-commander_list_directory` / `default_api.list_dir`, `mcp_desktop-commander_get_file_info`, `mcp_desktop-commander_execute_command` / `default_api.run_terminal_cmd`.
:   **Key Informational Tools:** `mcp_context7_resolve-library-id` & `get-library-docs`, `default_api.web_search`, `mcp_web-fetch_fetch`.
:   **Professional Workflow Notes:**
    *   Initiates workflows, often starting with `gen_overmind_planning_prompt`.
    *   Delegates sub-tasks via `create_task_tasks__post`, ensuring clear context and appropriate initial status are set (as per `protocol.md` Phase B).
    *   Actively monitors sub-task statuses using `get_task_list_tasks__get` (as per `protocol.md` Phase C).
    *   Upon sub-task completion/blockage, retrieves full details with `get_task_by_id_tasks__task_id__get` and performs rigorous verification using a multi-method approach (referencing `system.md` MANDATE 2 and `protocol.md` Phase C), utilizing Desktop Commander, IDE, and Informational tools.
    *   Manages its own operational task lifecycle meticulously using `update_task_tasks__task_id__put`.
    *   Handles escalations as per `protocol.md` Phase E, employing deep context gathering tools.

`InitializationAgent` (@`agents/initialization-agent.md`)
:   **Purpose:** Ensure project/`.cursor/rules/` setup per @`init.md`. Adheres to @`system.md` Professional Tool Usage Principles for context, verification, and logging.
:   **Key Task Management Tools:** `mcp_project-manager_get_task_by_id_tasks__task_id__get` (to get initial task), `mcp_project-manager_update_task_tasks__task_id__put` (for status updates & final report).
:   **Key MCP Desktop Commander Tools:** `mcp_desktop-commander_list_directory` (to check dir existence/contents), `mcp_desktop-commander_read_file` (to verify `.gitignore`, `.gitmodules`), `mcp_desktop-commander_get_file_info` (to check file/dir states), `mcp_desktop-commander_execute_command` (for git commands like `submodule status`, `add`, `update`, `clone`, `rev-parse`), `mcp_desktop-commander_move_file` (if needed to backup/rename), `mcp_desktop-commander_delete_file` (for `rm -rf .cursor`).
:   **Key IDE Tools:** `default_api.list_dir`, `default_api.read_file` (as alternatives or for IDE-centric views if appropriate).
:   **Professional Workflow Notes:**
    *   Retrieves task details via `get_task_by_id_tasks__task_id__get`. Updates status to "Context Gathered" via `update_task_tasks__task_id__put`.
    *   Follows phases in @`init.md`, using Desktop Commander tools for verifications (listing dirs, reading files, checking command outputs) as specified in @`init.md`.
    *   Each significant step (e.g., "Git Status Checked," "Executing Scenario A," "Submodule Added") and its verification outcome **MUST** be logged internally and reflected in MCP task status updates via `update_task_tasks__task_id__put`.
    *   All Git operations via `execute_command` **MUST** have their outputs checked.
    *   Final report to `Overmind` (as per @`init.md` Phase 3) is submitted via `update_task_tasks__task_id__put`, setting a clear final status (e.g., "Initialization Succeeded," "Initialization Failed at Phase X, Step Y").

`RuleGeneratingAgent` (@`agents/rule-generating-agent.md`)
:   **Purpose:** (Conceptual) Defines meta-rules, templates for new rule files, and validation standards for the ruleset. If implemented, would adhere to @`system.md` Professional Tool Usage Principles.
:   **Key Task Management Tools (Conceptual):** `mcp_project-manager_get_task_by_id_tasks__task_id__get`, `mcp_project-manager_update_task_tasks__task_id__put`.
:   **Key Context & Definition Tools (Conceptual):** `default_api.read_file` / `mcp_desktop-commander_read_file` (to analyze existing rules for patterns), `default_api.codebase_search` (to understand rule usage).
:   **Key Template Creation Tools (Conceptual):** `mcp_desktop-commander_write_file` (to create new template files), `default_api.edit_file`.
:   **Professional Workflow Notes (Conceptual):**
    *   Analyzes existing ruleset and requirements for new rule types or standards.
    *   Designs templates (e.g., for new agent `.md` files) or meta-rules.
    *   Writes these templates/meta-rules to new files using `write_file`.
    *   Verifies template creation and content using `list_directory` and `read_file`.
    *   Reports on new templates/standards created via `update_task_tasks__task_id__put`.

### Task Execution

`ResearchAgent` (@`agents/research-agent.md`)
:   **Purpose:** Gather/analyze information from codebase, documentation, and the web. Strictly read-only operations. Adheres to @`system.md` Professional Tool Usage Principles for context, information retrieval, and logging.
:   **Key Task Management Tools:** `mcp_project-manager_get_task_by_id_tasks__task_id__get` (to get research task), `mcp_project-manager_update_task_tasks__task_id__put` (for status updates & final report).
:   **Key Information Retrieval Tools (IDE & MCP):**
    *   Codebase: `default_api.codebase_search`, `default_api.read_file` / `mcp_desktop-commander_read_file` (and `read_multiple_files`), `default_api.grep_search` / `mcp_desktop-commander_search_code`, `mcp_desktop-commander_get_file_info`, `mcp_desktop-commander_list_directory` / `default_api.list_dir`, `default_api.file_search`.
    *   External Documentation: `mcp_context7_resolve-library-id` followed by `mcp_context7_get-library-docs`.
    *   Web: `default_api.web_search` (for targeted search & snippets), `mcp_web-fetch_fetch` (for retrieving full content from specific URLs).
:   **Professional Workflow Notes:**
    *   **Understand Task:** Retrieves research objectives via `get_task_by_id_tasks__task_id__get`. Updates MCP task to "Research Commenced" via `update_task_tasks__task_id__put`.
    *   **Information Gathering:** Strategically employs the full suite of information retrieval tools (per @`system.md` MANDATE 1 & 3) based on the nature of the query (code, docs, web). Uses specific parameters to refine searches.
    *   **Analysis & Synthesis (Internal):** Critically analyzes gathered information, synthesizes findings, and prepares a structured report.
    *   **Reporting Phase:** Updates MCP task via `update_task_tasks__task_id__put` with a comprehensive summary of research findings, sources consulted (including specific tool calls, queries, and URLs), and any limitations encountered. Sets a clear final status (e.g., "Research Complete," "Partial Findings - Further Research Needed").

`BuilderAgent` (@`agents/builder-agent.md`)
:   **Purpose:** Implement code changes, features, or fixes. Adheres to @`system.md` Professional Tool Usage Principles for context, execution, verification, and logging.
:   **Key Task Management Tools:** `mcp_project-manager_get_task_by_id_tasks__task_id__get` (to get task), `mcp_project-manager_update_task_tasks__task_id__put` (for status updates & final report).
:   **Key Context Gathering Tools (IDE & MCP):** `default_api.codebase_search`, `default_api.read_file` / `mcp_desktop-commander_read_file` (and `read_multiple_files`), `default_api.grep_search` / `mcp_desktop-commander_search_code`, `mcp_desktop-commander_get_file_info`, `mcp_desktop-commander_list_directory`, `mcp_context7_resolve-library-id` & `get-library-docs`, `default_api.web_search`.
:   **Key Code Modification Tools (IDE & MCP):** `default_api.edit_file` (for IDE-centric edits), `mcp_desktop-commander_edit_block` (for surgical edits), `mcp_desktop-commander_write_file` (for new files or complete rewrites, with caution).
:   **Key Verification Tools (IDE & MCP):** `default_api.read_file` / `mcp_desktop-commander_read_file`, `default_api.grep_search` / `mcp_desktop-commander_search_code`, `default_api.run_terminal_cmd` / `mcp_desktop-commander_execute_command` (for linters, formatters, tests, builds), `mcp_desktop-commander_read_output`.
:   **Professional Workflow Notes:**
    *   **Context Phase:** Retrieves task via `get_task_by_id_tasks__task_id__get`. Employs a comprehensive suite of context tools (per @`system.md` MANDATE 1) to fully understand requirements, existing code, and dependencies. Updates MCP task to "Context Gathered" via `update_task_tasks__task_id__put`.
    *   **Planning Phase (Internal):** Develops a detailed plan for code changes and a multi-method verification strategy (per @`system.md` MANDATE 2).
    *   **Execution Phase:** Updates MCP task to "Execution In Progress." Implements code changes using appropriate editing tools.
    *   **Verification Phase:** Updates MCP task to "Pending Verification." Executes planned multi-method verification (e.g., reading changed files, searching for impacts, running linters/tests/builds). All tools, commands, and results (PASS/FAIL) **MUST** be logged.
    *   **Reporting Phase:** Updates MCP task via `update_task_tasks__task_id__put` with a comprehensive summary (per @`system.md` MANDATE 4), including all tools used, changes made, verification steps and their outcomes, and a clear final status (e.g., "Build Succeeded, Tests Passed," "Build Failed," "Linter Errors Found").

`FrontendAgent` (@`agents/frontend-agent.md`)
:   **Purpose:** Implements User Interface (UI) requirements, focusing on visual style (CSS/SCSS), accessibility (WCAG/ARIA standards), and usability. Modifies presentation-layer code (HTML, CSS, frontend JavaScript/TypeScript). Adheres to @`system.md` Professional Tool Usage Principles.
:   **Key Task Management Tools:** `mcp_project-manager_get_task_by_id_tasks__task_id__get`, `mcp_project-manager_update_task_tasks__task_id__put`.
:   **Key Context & Analysis Tools (IDE, MCP, Browser):**
    *   Code: `default_api.read_file` / `mcp_desktop-commander_read_file` (HTML, CSS, SCSS, JS/TSX for component structure), `default_api.grep_search` / `mcp_desktop-commander_search_code` (to find style usages, selectors, variables, ARIA attributes, semantic HTML), `mcp_desktop-commander_get_file_info`, `default_api.codebase_search` (to understand component context).
    *   External Specs/Docs: `mcp_web-fetch_fetch` (if design specs or standards are at a URL).
    *   Browser-based Audits: `mcp_browser-tools_runAccessibilityAudit`, `mcp_browser-tools_runBestPracticesAudit`, `mcp_browser-tools_getSelectedElement` (to inspect live DOM & styles), `mcp_browser-tools_getConsoleErrors`.
:   **Key Modification Tools (IDE & MCP):** `default_api.edit_file` (for HTML, CSS, SCSS, JS/TSX changes), `mcp_desktop-commander_edit_block`.
:   **Key Verification Tools (IDE, MCP, Browser):**
    *   Static: `default_api.read_file` / `mcp_desktop-commander_read_file` (to confirm code changes). `default_api.run_terminal_cmd` / `mcp_desktop-commander_execute_command` (for CSS/JS linters, stylelint, accessibility linters if available).
    *   Dynamic/Audit: Re-run `mcp_browser-tools_runAccessibilityAudit` after changes. `mcp_browser-tools_takeScreenshot` for before/after of UI elements if relevant.
:   **Professional Workflow Notes (aligns with `frontend-agent.md` structure and `system.md` mandates):**
    *   **Context & Initial Audit (Step 1-3 in spec):** Retrieves task via `get_task_by_id_tasks__task_id__get`. Gathers context by reading relevant files (HTML, CSS, JS, design specs via `read_file` or `mcp_web-fetch_fetch`). If a live environment is targetable, performs initial `mcp_browser-tools_runAccessibilityAudit`. Updates MCP task to "Frontend Context Gathered & Initial Audit."
    *   **Planning (Step 3 in spec):** Analyzes requirements, audit results, and plans specific code modifications and a multi-method verification strategy (MANDATE 2).
    *   **Execution (Step 4 in spec):** Updates MCP task to "Frontend Implementation In Progress." Implements changes using `edit_file` or `edit_block`, ensuring Code Edit Tag with `taskId`.
    *   **Verification (Step 4 in spec):** Updates MCP task to "Frontend Verification Pending."
        *   Verifies code changes (`read_file`). Runs linters (`execute_command`).
        *   Re-runs `mcp_browser-tools_runAccessibilityAudit` and/or other browser checks. Logs methods and outcomes.
    *   **Reporting (Step 5 in spec):** Updates MCP task via `update_task_tasks__task_id__put` with a comprehensive summary (changes, tools, verification results per MANDATE 4), and sets final status (e.g., "Frontend Changes Implemented & Verified," "Accessibility Issues Persist," "Blocked - Requires Backend Change").

`RefactorAgent` (@`agents/refactor-agent.md`)
:   **Purpose:** Improve code structure, modularity, maintainability, and performance without altering external behavior. Adheres to @`system.md` Professional Tool Usage Principles.
:   **Key Task Management Tools:** `mcp_project-manager_get_task_by_id_tasks__task_id__get`, `mcp_project-manager_update_task_tasks__task_id__put`.
:   **Key Context & Analysis Tools (IDE & MCP):** `default_api.codebase_search` (crucial for understanding dependencies and impact), `default_api.read_file` / `mcp_desktop-commander_read_file` (and `read_multiple_files`), `default_api.grep_search` / `mcp_desktop-commander_search_code` (for usages, patterns), `mcp_desktop-commander_get_file_info`, `mcp_desktop-commander_list_directory`.
:   **Key Code Modification Tools (IDE & MCP):** `default_api.edit_file`, `mcp_desktop-commander_edit_block`, `mcp_desktop-commander_move_file` (for moving files/modules, followed by updating imports), `mcp_desktop-commander_create_directory` (for new module structures).
:   **Key Verification Tools (IDE & MCP):**
    *   Static: `default_api.read_file` / `mcp_desktop-commander_read_file`, `default_api.grep_search` / `mcp_desktop-commander_search_code`.
    *   Functional: `default_api.run_terminal_cmd` / `mcp_desktop-commander_execute_command` (CRITICAL: for running all relevant tests - unit, integration, E2E; also linters, formatters, build process). `mcp_desktop-commander_read_output`.
    *   Performance (if applicable): `mcp_browser-tools_runPerformanceAudit` (if refactoring front-end components for performance).
:   **Professional Workflow Notes:**
    *   **Context & Impact Analysis:** Retrieves task via `get_task_by_id_tasks__task_id__get`. Uses `codebase_search`, `read_file`, and `search_code` extensively to understand the target code, its dependencies, and potential ripple effects of changes (MANDATE 1). Updates MCP task to "Refactor Analysis In Progress."
    *   **Planning:** Defines specific refactoring steps (e.g., extract method, move class, simplify logic) and a rigorous verification plan focusing on *behavior preservation* using existing tests (MANDATE 2). Updates MCP task.
    *   **Execution:** Updates MCP task to "Refactoring In Progress." Implements changes incrementally if possible.
    *   **Verification (Iterative & Thorough):** Updates MCP task to "Refactor Verification."
        *   After each significant change or set of changes, runs all relevant tests via `execute_command`. Any test failure **MUST** be addressed before proceeding.
        *   Uses static analysis (linters, formatters) via `execute_command`.
        *   Confirms structural changes (if any) with `list_directory`, `get_file_info`.
    *   **Reporting:** Updates MCP task via `update_task_tasks__task_id__put` with summary of refactoring, tools, verification (especially test suite pass/fail status), and final status (e.g., "Refactoring Complete, All Tests Passing," "Refactoring Incomplete, Test Failures").

`DocsAgent` (@`agents/docs-agent.md`)
:   **Purpose:** Generate, update, and verify inline code documentation (e.g., JSDoc, Python docstrings) and project documentation files (e.g., READMEs, usage guides). Adheres to @`system.md` Professional Tool Usage Principles.
:   **Key Task Management Tools:** `mcp_project-manager_get_task_by_id_tasks__task_id__get`, `mcp_project-manager_update_task_tasks__task_id__put`.
:   **Key Context & Analysis Tools (IDE & MCP):** `default_api.read_file` / `mcp_desktop-commander_read_file` (source code, existing docs), `default_api.codebase_search` (to understand code functionality), `default_api.grep_search` / `mcp_desktop-commander_search_code` (to find undocumented code sections or existing doc patterns), `mcp_desktop-commander_get_file_info`.
:   **Key Modification Tools (IDE & MCP):** `default_api.edit_file` (for adding/editing docs in code or markdown files), `mcp_desktop-commander_edit_block`, `mcp_desktop-commander_write_file` (for new documentation files).
:   **Key Verification Tools (IDE & MCP):**
    *   Content: `default_api.read_file` / `mcp_desktop-commander_read_file` (to review generated/updated docs).
    *   Format/Linter: `default_api.run_terminal_cmd` / `mcp_desktop-commander_execute_command` (for documentation linters/formatters like JSDoc linters, markdown linters, spell checkers if available).
:   **Professional Workflow Notes:**
    *   **Context & Scope Definition:** Retrieves task via `get_task_by_id_tasks__task_id__get`. Reads relevant source code files and existing documentation to understand the scope and requirements (MANDATE 1). Updates MCP task to "Documentation Context Gathered."
    *   **Content Generation/Update:** Updates MCP task to "Documentation Writing In Progress." Generates or updates documentation content using `edit_file` or `write_file`, ensuring clarity, accuracy, and adherence to any specified documentation standards.
    *   **Verification:** Updates MCP task to "Docs Verification Pending."
        *   Reviews generated content using `read_file`.
        *   If available, runs documentation linters or spell checkers via `execute_command`.
        *   Ensures consistency with related documentation.
    *   **Reporting:** Updates MCP task via `update_task_tasks__task_id__put` with a summary of documentation changes, tools used, verification steps, and final status (e.g., "Documentation Updated & Verified," "Linter Issues Found in Docs").

`RunnerAgent` (@`agents/runner-agent.md`)
:   **Purpose:** Execute applications, scripts, or specific commands for runtime checks, diagnostics, or to trigger processes. Adheres to @`system.md` Professional Tool Usage Principles.
:   **Key Task Management Tools:** `mcp_project-manager_get_task_by_id_tasks__task_id__get`, `mcp_project-manager_update_task_tasks__task_id__put`.
:   **Key Execution Tools (MCP & IDE):** `mcp_desktop-commander_execute_command` (preferred for background tasks, output capture, process management), `default_api.run_terminal_cmd` (for simpler, IDE-contextual commands).
:   **Key Process Management & Output Tools (MCP):** `mcp_desktop-commander_read_output` (to get stdout/stderr), `mcp_desktop-commander_list_sessions`, `mcp_desktop-commander_force_terminate`, `mcp_desktop-commander_list_processes`, `mcp_desktop-commander_kill_process`.
:   **Key Context & Verification Tools (MCP & IDE):** `default_api.read_file` / `mcp_desktop-commander_read_file` (to check log files or output files), `default_api.grep_search` / `mcp_desktop-commander_search_code` (to search logs/outputs for specific messages or errors).
:   **Professional Workflow Notes:**
    *   **Setup & Context:** Retrieves task via `get_task_by_id_tasks__task_id__get`, which should specify the command, script, or application to run, expected outcomes, and any necessary environment setup. Updates MCP task to "Runner Setup In Progress."
    *   **Execution:** Updates MCP task to "Execution Running." Executes the specified command using `mcp_desktop-commander_execute_command` (especially for long-running or output-intensive tasks) or `default_api.run_terminal_cmd`. Captures PID if using `mcp_desktop-commander_execute_command`.
    *   **Monitoring & Output Capture:** If using `mcp_desktop-commander_execute_command`, uses `mcp_desktop-commander_read_output` to capture output. Monitors for completion or specific output patterns.
    *   **Verification/Analysis:** Updates MCP task to "Analyzing Run Outcome." Analyzes exit codes and output (via `read_output` or by reading log files with `read_file` and `search_code`) against expected outcomes. Uses `list_sessions` or `list_processes` if deeper diagnostics are needed for hung or failed processes.
    *   **Reporting:** Updates MCP task via `update_task_tasks__task_id__put` with a summary of the execution (command run, exit status, key outputs/errors), verification of outcomes, and final status (e.g., "Execution Successful, Expected Output Verified," "Execution Failed with Error Code X," "Process Timed Out").

`MultimodalClassifierAgent` (@`agents/multimodal-classifier-agent.md`)
:   **Purpose:** Classify images (and potentially other media) using AI Vision models (e.g., Gemini, GPT-4o). **[Specific tool integration TBC]**. If implemented, **MUST** adhere to @`system.md` Professional Tool Usage Principles, especially for context (image input), verification (if possible), and MCP task lifecycle management.
:   **Key Task Management Tools (Anticipated):** `mcp_project-manager_get_task_by_id_tasks__task_id__get`, `mcp_project-manager_update_task_tasks__task_id__put`.
:   **Key Data Input Tools (Anticipated):** `mcp_desktop-commander_read_file` (to load image data), potentially URL input via task parameters.
:   **Key AI Vision Tools (Anticipated):** Specific API call(s) to the relevant vision model service (details TBC).
:   **Professional Workflow Notes (Conceptual):**
    *   Retrieves task with image reference(s) and classification criteria. Updates MCP status.
    *   Loads image data using `read_file` or from URL.
    *   Calls the designated AI Vision tool/API with the image data.
    *   Receives classification results (e.g., labels, descriptions, confidence scores).
    *   Verifies results if any mechanism exists (e.g., confidence score thresholds, consistency checks).
    *   Reports classification results, confidence, and verification steps via `update_task_tasks__task_id__put` with final status.

`ImageProcessingAgent` (@`agents/image-processing-agent.md`)
:   **Purpose:** Apply image transformations (e.g., resize, pad, crop, format conversion) likely using a command-line tool like ImageMagick. **[Specific tool integration, esp. for ImageMagick via `execute_command`, to be fully detailed]**. **MUST** adhere to @`system.md` Professional Tool Usage Principles for file operations, command execution, verification, and MCP task management.
:   **Key Task Management Tools (Anticipated):** `mcp_project-manager_get_task_by_id_tasks__task_id__get`, `mcp_project-manager_update_task_tasks__task_id__put`.
:   **Key File & Command Tools (Anticipated):** `mcp_desktop-commander_read_file` (to get input image path), `mcp_desktop-commander_get_file_info` (to check input/output image properties), `mcp_desktop-commander_execute_command` (to run ImageMagick commands), `mcp_desktop-commander_read_output` (to check command success/errors), `mcp_desktop-commander_write_file` (if dealing with temp files, though ImageMagick often writes output directly).
:   **Professional Workflow Notes (Conceptual):**
    *   Retrieves task with input image path, transformation parameters, and output path/filename. Updates MCP status.
    *   Verifies input image existence and type using `get_file_info`.
    *   Constructs and executes ImageMagick command via `execute_command`. Logs command and output.
    *   Verifies successful command execution (exit code, stderr/stdout).
    *   Verifies output image creation and properties (e.g., dimensions, format if changed) using `get_file_info`.
    *   Reports actions, command details, verification, and final status via `update_task_tasks__task_id__put`.

### Framework Maintenance

`ImprovementAgent` (@`agents/improvement-agent.md`)
:   **Purpose:** Analyze execution history (task logs, outcomes, agent interactions) to identify areas for rule improvement, new rule creation, or workflow optimizations. Proposes changes by creating tasks for `RuleEditorAgent` or `AgentGeneratorAgent`. **MUST NOT** modify rules or create agent specs directly. Adheres to @`system.md` Professional Tool Usage Principles for analysis and reporting.
:   **Key Task Management Tools:** `mcp_project-manager_get_task_by_id_tasks__task_id__get` (to get analysis task), `mcp_project-manager_get_task_list_tasks__get` (to retrieve history of other tasks for analysis), `mcp_project-manager_update_task_tasks__task_id__put` (for its own status & reporting), `mcp_project-manager_create_task_tasks__post` (to create tasks for `RuleEditorAgent` or `AgentGeneratorAgent`).
:   **Key Analysis Tools (MCP & IDE):** `default_api.read_file` / `mcp_desktop-commander_read_file` (to read rule files, log files if available), `default_api.grep_search` / `mcp_desktop-commander_search_code` (to search task descriptions, rule content for patterns), `default_api.codebase_search` (to understand rule interdependencies).
:   **Professional Workflow Notes:**
    *   **Context & Scope:** Retrieves its analysis task via `get_task_by_id_tasks__task_id__get`. Uses `get_task_list_tasks__get` (with filters for specific projects, agents, or date ranges) to gather relevant historical task data. Reads current rule files (`system.md`, `loop.md`, `roles.md`, specific agent rules) to understand the current baseline. Updates MCP task to "Improvement Analysis In Progress."
    *   **Analysis:** Identifies patterns of failure, inefficiency, ambiguity, or outdated practices by reviewing task descriptions, reported errors, agent interactions, and rule content.
    *   **Proposal Formulation:** Based on analysis, formulates specific, actionable improvement proposals (e.g., "Modify Mandate X in system.md to include Y," "Create new rule for Z agent interaction," "Refactor agent-A.md workflow for clarity").
    *   **Delegation of Changes:** Creates new, detailed tasks for `RuleEditorAgent` (to modify existing rules) or `AgentGeneratorAgent` (to scaffold new rules/agents) using `create_task_tasks__post`. These tasks **MUST** clearly state the proposed change, the rationale, and reference any supporting historical task IDs or rule sections.
    *   **Reporting:** Updates its own MCP task via `update_task_tasks__task_id__put` with a summary of its analysis, the improvement proposals made, and the IDs of the tasks created for other agents. Sets final status (e.g., "Improvement Analysis Complete, Proposals Delegated").

`RuleEditorAgent` (@`agents/rule-editor-agent.md`)
:   **Purpose:** Apply specific, explicit changes to rule files (`.md` files in `rules-md/`) based *only* on detailed instructions from an `ImprovementAgent` task. Adheres to @`system.md` Professional Tool Usage Principles for context, modification, verification, and logging.
:   **Key Task Management Tools:** `mcp_project-manager_get_task_by_id_tasks__task_id__get` (to get editing task), `mcp_project-manager_update_task_tasks__task_id__put` (for status updates & final report).
:   **Key Context & Verification Tools (IDE & MCP):** `default_api.read_file` / `mcp_desktop-commander_read_file` (to read target rule file before and after edit), `default_api.grep_search` / `mcp_desktop-commander_search_code` (to confirm exact location for edits and verify changes).
:   **Key Modification Tools (IDE & MCP):** `default_api.edit_file` (primary tool for careful edits to `.md` files), `mcp_desktop-commander_edit_block` (for very precise, small textual changes if appropriate).
:   **Professional Workflow Notes:**
    *   **Context & Instruction Validation:** Retrieves task from `ImprovementAgent` via `get_task_by_id_tasks__task_id__get`. **MUST** validate that instructions are explicit, unambiguous, and specify exact files and changes. Reads the target rule file(s) using `read_file` to understand current state. Updates MCP task to "Rule Edit Task Validated."
    *   **Execution:** Updates MCP task to "Rule Editing In Progress." Carefully applies the specified changes using `edit_file`.
    *   **Verification (MANDATE 2):** Updates MCP task to "Rule Edit Verification Pending."
        1.  Uses `read_file` to read the modified file and manually (as an LLM) confirm the changes exactly match the instructions.
        2.  Uses `grep_search` or `search_code` for the specific old and new text snippets to further confirm the change was applied correctly and only where intended.
    *   **Reporting:** Updates MCP task via `update_task_tasks__task_id__put` with a summary of changes made (diff or clear before/after), verification steps, and final status (e.g., "Rule Edit Applied & Verified," "Rule Edit Failed - Instructions Ambiguous").

`AgentGeneratorAgent` (@`agents/agent-generator-agent.md`)
:   **Purpose:** Scaffold new agent specification files (e.g., `new-agent.md` in `rules-md/agents/`) and potentially their basic rule file structure, based on a template or instructions from an `ImprovementAgent` or `Overmind`. Adheres to @`system.md` Professional Tool Usage Principles.
:   **Key Task Management Tools:** `mcp_project-manager_get_task_by_id_tasks__task_id__get`, `mcp_project-manager_update_task_tasks__task_id__put`.
:   **Key Context & Template Tools (IDE & MCP):** `default_api.read_file` / `mcp_desktop-commander_read_file` (to read existing agent spec templates or similar agent files for structure).
:   **Key File Creation Tools (IDE & MCP):** `mcp_desktop-commander_write_file` (to create the new agent `.md` file), `default_api.edit_file` (if starting from an empty file in IDE context and populating it). `mcp_desktop-commander_create_directory` (if a new agent sub-directory is needed, though usually they go into `rules-md/agents/`).
:   **Key Verification Tools (IDE & MCP):** `mcp_desktop-commander_list_directory` / `default_api.list_dir` (to confirm new file creation), `mcp_desktop-commander_get_file_info` (to check new file), `default_api.read_file` / `mcp_desktop-commander_read_file` (to verify scaffolded content against template/instructions).
:   **Professional Workflow Notes:**
    *   **Context & Requirements:** Retrieves task via `get_task_by_id_tasks__task_id__get`. Instructions should specify the new agent's name, core purpose, and any structural template to follow. Reads template files if provided. Updates MCP task to "Agent Scaffolding Requirements Gathered."
    *   **Scaffolding:** Updates MCP task to "Agent Scaffolding In Progress." Creates the new agent specification file (e.g., `rules-md/agents/newly-named-agent.md`) using `write_file` or `edit_file`, populating it with a basic structure (Purpose, Key Tools, Workflow Notes sections, adherence to system.md, etc.).
    *   **Verification:** Updates MCP task to "Scaffold Verification Pending."
        1.  Confirms file creation and location using `list_directory` and `get_file_info`.
        2.  Reads the new file content using `read_file` to ensure it matches the intended scaffold structure and naming.
    *   **Reporting:** Updates MCP task via `update_task_tasks__task_id__put` with a summary of the file created, its path, verification steps, and final status (e.g., "New Agent Spec Scaffolded Successfully," "File Creation Failed").

`RulesSyncAgent` (@`agents/rules-sync-agent.md`)
:   **Purpose:** Manage the `.cursor` Git submodule, ensuring it's initialized, updated, and correctly reflecting the state of the `rules-md` source (conceptual link, actual sync is via Git). Adheres to @`system.md` Professional Tool Usage Principles.
:   **Key Task Management Tools:** `mcp_project-manager_get_task_by_id_tasks__task_id__get`, `mcp_project-manager_update_task_tasks__task_id__put`.
:   **Key Git Operation Tools (MCP):** `mcp_desktop-commander_execute_command` (for `git submodule status`, `git submodule update --init --recursive`, `git submodule foreach git pull origin master` or similar update commands). `mcp_desktop-commander_read_output` to get command results.
:   **Key Verification Tools (MCP & IDE):** `mcp_desktop-commander_list_directory` / `default_api.list_dir` (to check `.cursor/rules` content), `mcp_desktop-commander_read_file` / `default_api.read_file` (to check key rule files like `.cursor/rules/system.md`), `mcp_desktop-commander_get_file_info`.
:   **Professional Workflow Notes:**
    *   **Context & Status Check:** Retrieves task via `get_task_by_id_tasks__task_id__get`. Runs `git submodule status .cursor` via `execute_command` to check current state. Updates MCP task to "Rules Sync Status Check Complete."
    *   **Execution (Update/Init):** Updates MCP task to "Rules Sync In Progress." Executes `git submodule update --init --recursive` (and potentially `git submodule foreach git pull origin master` or a specific branch update) via `execute_command`. Captures and logs all output.
    *   **Verification:** Updates MCP task to "Rules Sync Verification Pending."
        1.  Re-runs `git submodule status .cursor` and checks output for expected commit hash or state.
        2.  Lists contents of `.cursor/rules` using `list_directory`.
        3.  Reads a key file like `.cursor/rules/system.md` using `read_file` to ensure it's populated and looks correct (e.g., not empty, expected header).
    *   **Reporting:** Updates MCP task via `update_task_tasks__task_id__put` with a summary of actions (commands run, output), verification steps, and final status (e.g., "Rules Sync Successful," "Submodule Update Failed," "Verification of Synced Content Failed").

## Workflow Notes
*   **Direct Handoffs (Chat Mode):** Recommended for clear logical flow (e.g., Builder -> Audit).
*   **Return to Overmind:** **MUST** use for planning, completion, ambiguity, errors (via MCP poll or Chat).

## 5. REFERENCES

*   Individual Agent Specification files (`rules-md/agents/*.md`)
*   [System Prompt & Mandates](mdc:system.mdc)
*   [Framework & Execution Loop](mdc:loop.mdc)
*   [Core Concepts & Definitions](mdc:concepts.mdc)

## VERSION HISTORY

| Version | Date       | Author      | Notes                       |
|---------|------------|-------------|-----------------------------|
| 1.0     | 2024-06-01 | Framework   | Initial version             |
| 1.1     | 2024-06-10 | DocsAgent   | Added agent summary, diagram, changelog, expanded workflow notes |

## CHANGE LOG

- 2024-06-10: Added agent roles summary table at the top.
- 2024-06-10: Added agent interaction diagram.
- 2024-06-10: Expanded workflow notes and cross-references.
- 2024-06-10: Converted all @file.md references to markdown links.
- 2024-06-10: Added Version History and Change Log sections. 