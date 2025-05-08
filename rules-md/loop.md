# ⚙️ Framework & Core Agent Execution Loop

**Defines:**
1.  **External Agent Execution Framework:** Orchestrates agents (Part 1).
2.  **Mandatory Core Agent Execution Loop:** Internal steps per turn (Part 2).

## PART 1: AGENT EXECUTION FRAMEWORK (External Orchestrator)

**Purpose:** System/process orchestrating agent execution (MCP preferred). **Not an agent.**

**Responsibilities (MUST):**
1.  **Activation & Sequencing:**
    *   Activate agents based on MCP tasks (via `Overmind` polling) or Chat Triggers.
    *   Load agent rules (respecting hierarchy).
    *   Invoke agent, providing context (`taskId` / trigger payload) per **Part 2, Step 1**.
    *   Ensure sequential execution per `requestId`.
2.  **Capability Provision:** Provide authorized capabilities; execute calls; return results.
3.  **Rule Management:** Provide means to fetch rules; manage `.cursor/rules/`; respect hierarchy.
4.  **Lifecycle:** Initiate (`Overmind`); manage flow; detect halt conditions.
5.  **Environment:** Provide runtime; manage resource access via authorized capabilities only.

**Interaction:** Activation, Capability Interface, Transition detection (Chat) / MCP operations (MCP). **MUST NOT** require semantic understanding of tasks/triggers. **MUST** enforce **Part 2** loop.

---

## PART 2: CORE AGENT EXECUTION LOOP (Mandatory, MCP Focus)

**Purpose:** You **MUST** follow this mandatory sequence of steps each time you are activated for a task turn. This ensures your behavior is consistent, predictable, and auditable. You will primarily use the MCP Task Manager (or Chat, if applicable) as your Single Source of Truth for instructions and status.

**Rules You MUST Follow:**
*   You **MUST** execute Steps 1 through 6 sequentially in every turn. You cannot skip steps, except when a HALT condition is met.
*   You **MUST** treat the coordination mechanism (MCP Task details or Chat Payload) as the definitive source for your task instructions and context.
*   You **MUST** get your full context (Step 2) *before* taking significant action.
*   You **MUST** fetch and use your own role-specific rules (Step 3).
*   When reporting your results (Step 6), you **MUST** include details about your verification actions and any assumptions you made or identified.

**Action Sequence (Your Mandatory Steps):**

**Step 1: Activate & Get Initial Context**
*   **Activation:** The Framework activates you.
*   **Input:** You receive a `taskId` (MCP) or a Trigger Payload (Chat).
*   **Action:** You will store the `taskId` or parse the payload to extract initial context.

**Step 2: Get Full Task/Operational Context & Update Status**
*   **Action:** You will fetch detailed instructions and operational context, employing a comprehensive suite of tools as per @`system.md` MANDATE 1.
*   **Tooling (MCP Focus):**
    *   Primary: `mcp_project-manager_get_task_by_id_tasks__task_id__get` (for core task details).
    *   Supporting (as needed for full understanding): `mcp_desktop-commander_get_file_info`, `mcp_desktop-commander_list_directory`, `mcp_desktop-commander_read_file` / `default_api.read_file`, `default_api.codebase_search`, `mcp_desktop-commander_search_code` / `default_api.grep_search`, `default_api.file_search`.
    *   External Knowledge (if applicable): `mcp_context7_resolve-library-id` & `get-library-docs`, `default_api.web_search` / `mcp_web-fetch_fetch`.
*   **Action (Chat):** Use context parsed from payload in Step 1, supplementing with relevant read-only tools if necessary and feasible.
*   **Critical Evaluation (Both):** You **MUST** critically evaluate all gathered context according to principles in @`system.md`. Identify assumptions and verify task feasibility.
*   **MCP Status Update:** Upon completion of context gathering and initial analysis, you **MUST** update the MCP task via `mcp_project-manager_update_task_tasks__task_id__put`, setting status to reflect "Context Gathered & Analyzed" (or similar) and logging key findings/tools used, as per @`system.md` MANDATE 4.

**Step 3: Fetch Your Role Specification**
*   **Action:** You will retrieve the rules that define your current role.
*   **Method:** You will fetch your specific agent rule file (e.g., `builder-agent.md`).

**Step 4: Plan Your Turn (Internal)**
*   **Action:** You will internally prepare your plan of action for the current turn.
*   **Input:** Your rules (from Step 3) and the full task context (from Step 2).
*   **Process:** You will construct your internal reasoning or prompt. You will plan the specific operations needed for Step 5, ensuring you include **mandatory verification** steps and checks for any **assumptions** you identified, as required by @`system.md`.

**Step 5: Execute Your Core Task(s), Verify Rigorously & Update Status**
*   **Action:** Perform the primary function(s) defined by your role and the current task, using authorized capabilities.
*   **Input:** Your plan (from Step 4) and context (from Step 2).
*   **Process:**
    1.  **MCP Status Update (Execution Start):** Before starting significant execution, update MCP task status to "Execution In Progress" or similar via `mcp_project-manager_update_task_tasks__task_id__put`.
    2.  **Execute:** Run the operations planned in Step 4.
    3.  **MCP Status Update (Verification Start):** After execution and before verification, update MCP task status to "Pending Verification" or similar.
    4.  **Verify Rigorously:** Execute verification steps planned in Step 4. This **MUST** adhere to @`system.md` MANDATE 2 (Multi-Method Verification), employing diverse tools and appropriate example workflows detailed therein.
    5.  **Analyze & Record Internally:** Consolidate action results, verification outcomes (PASS/FAIL with specific tools/methods used), assumptions addressed, and any remaining uncertainties. This internal record is crucial for the comprehensive report in Step 6.
    6.  **MCP Status Update (Post-Verification):** Update MCP task status to reflect verification outcome (e.g., "Verification Succeeded," "Verification Failed - Analyzing").

**Step 6: Update State / Construct Handoff & Finalize Your Turn (FINAL ACTION)**
*   **Action:** You will persist the results of your turn to the coordination mechanism and then terminate your execution for this turn.
*   **Operations (MCP):** You will update the task and potentially mark the task done.
*   **Mechanism (Chat):** You will use the Framework's Chat Mechanism.
*   **Input:** Your `taskId` (MCP), your internal results recorded in Step 5.
*   **Process (MCP):**
    1.  **Comprehensive Update & Final Status:** You **MUST** update the MCP task using `mcp_project-manager_update_task_tasks__task_id__put`. This update serves as your primary handoff and **MUST** include:
        *   A **comprehensive summary** of findings as per @`system.md` MANDATE 4 (actions taken, tools used, verification methods and detailed results (PASS/FAIL), assumptions made/addressed, remaining uncertainties, errors encountered).
        *   A clear **final task status** reflecting the outcome (e.g., "Successfully Completed & Verified," "Blocked - Escalating to Overmind," "Failed - Max Retries Reached"). This status is critical for `Overmind` or the framework to determine the next step in the workflow.
        *   Set the `completed` flag to true if the task is genuinely finished and verified according to its objectives and your role's rules.
    2.  **Terminate:** You **MUST** end your execution turn now.
*   **Process (Chat):**
    1.  **Determine Next Agent:** You will determine the `<NextAgentRole>` based on your rules and the task outcome.
    2.  **Construct Handoff:** You will create a concise payload containing your **comprehensive findings** (as described for MCP above).
    3.  **Trigger:** You will send the Chat Trigger: "Hey `<NextAgentRole>`, [Handoff Payload]".
    4.  **Terminate:** You **MUST** end your execution turn now.

**Error Handling:**
*   **Step 2 Failure (Cannot get context):** You will HALT.
*   **Step 6 Failure (Cannot update state/trigger next):** You may retry the final operation once. If it still fails, you will HALT. Attempt local logging if possible.
*   **Step 5 Errors (During core task):** You **MUST** log a detailed analysis of the error (ensuring report content aligns with @`system.md` Global Mandate 6) in your Step 6 update/handoff message before either continuing (if recoverable per your rules) or HALTing. You **MUST** ensure errors are clearly reported to `Overmind` via the coordination mechanism.
