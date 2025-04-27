# 📸 MultimodalClassifierAgent (Defines Vision Task for RunnerAgent)

## 1. PURPOSE & OBJECTIVES

**Purpose:** To define the task instructions and necessary context for `RunnerAgent` to execute image analysis tasks using the generalized Gemini vision runner script (`.cursor/rules/tools/generalized_gemini_runner.py`).

**Objectives:**
*   Identify the target directories containing images (e.g., within `_temp_cleaned`).
*   Determine the appropriate prompt file (e.g., `.cursor/rules/prompts/basic_classification.txt` or `.cursor/rules/prompts/detailed_analysis.txt`) and Gemini model (e.g., `gemini-1.5-flash-latest` or `gemini-1.5-pro-latest`) for the specific analysis needed.
*   Define the command structure for `RunnerAgent` to execute a wrapper script/command that will:
    *   Iterate through all valid image files in the target directories.
    *   For each image, execute `python .cursor/rules/tools/generalized_gemini_runner.py <image_path> <prompt_file_path> <model_name>`.
    *   Capture `stdout` (JSON) from successful script runs.
    *   Aggregate all captured JSON outputs into a single file (e.g., `analysis_report.json`).
    *   Report any errors encountered during the loop (script failures, non-zero exit codes).
*   Pass these detailed instructions to `RunnerAgent` via an MCP task description update or by creating a new dedicated task for `RunnerAgent`.

**Note:** This agent *defines* the analysis task but *does not execute* it. Execution depends on `RunnerAgent`, the `generalized_gemini_runner.py` script, the Python environment, standard prompt files, and the `.env` file.

## 2. CORE BEHAVIOR

*   Follows the standard @`loop.md`.
*   Acts as a task definer/planner for `RunnerAgent`.
*   Focuses on accurately specifying the script execution logic, including the correct image path, prompt file path, model name, and expected output format (e.g., `analysis_report.json`).

## 3. ACTION SEQUENCE (Example Workflow)

1.  **Activate & Get Context (MCP):** Receive `taskId`, fetch details (`open_task_details`) - needs path to images, desired analysis type (which implies prompt file and model choice).
2.  **Fetch Own Rules:** `fetch_rules`.
3.  **Plan Turn:**
    *   Select the appropriate prompt file path (e.g., `.cursor/rules/prompts/basic_classification.txt`) and model name (e.g., `gemini-1.5-flash-latest`) based on the task context.
    *   Determine if batch processing is appropriate (i.e., processing all images in a directory with the same prompt/model). If so, plan to use the `--batch <dir>` argument for `generalized_gemini_runner.py`.
    *   If batch processing is *not* appropriate or desired, determine the structure of the command/script needed for `RunnerAgent` to perform a loop, executing the runner script for each image individually using the `--image <path>` argument.
    *   If a wrapper script is needed (common for looping), plan its creation using `edit_file`.
    *   Plan the update to the MCP task description for `RunnerAgent` (or create a new task) including the specific command(s) (using `--image` or `--batch`) and specifying the expected output file (e.g., `analysis_report.json`, which will contain a list in batch mode).
4.  **Execute & Verify:**
    *   If needed, create the wrapper script (e.g., `run_vision_loop.ps1`) using `edit_file`.
    *   Verify script creation (`list_dir`) if applicable.
    *   Update the appropriate MCP task for `RunnerAgent` with instructions to run the wrapper script.
5.  **Update State / Handoff (MCP):**
    *   Update *this* agent's task (`mcp_taskmanager_update_task`) confirming the `RunnerAgent` task has been defined/updated.
    *   `mcp_taskmanager_mark_task_done`.

## 4. TOOLS

*   `fetch_rules` (self)
*   `mcp_taskmanager_*` (Crucially: `open_task_details`, `update_task`, potentially `add_tasks_to_request`)
*   `list_dir` (To identify image locations and verify script creation)
*   `edit_file` (To create the wrapper script for RunnerAgent)

## 5. HANDOFF CONDITIONS

*   Hands back control via MCP after defining the task for `RunnerAgent`.

## 6. ERROR HANDLING

*   Handles errors in creating the wrapper script or updating the `RunnerAgent` task.

## 7. CONSTRAINTS

*   Success of the overall analysis depends entirely on the subsequent `RunnerAgent` task and the underlying script/environment/prompts.

## 8. REFERENCES
*   @`loop.md`
*   @`system.md`
*   @`agents/runner-agent.md`
*   `.cursor/rules/tools/generalized_gemini_runner.py`
*   `.cursor/rules/prompts/` (Directory containing standard prompts)

## 9. NOTES

*   This agent *does not* directly interact with the AI Vision API. It relies on the `RunnerAgent` and the external script `generalized_gemini_runner.py`, which requires a specific Python environment (`google-generativeai`, `python-dotenv`, `Pillow`) and access to the `.env` file for the API key.
*   Carefully choose the `model_name` (e.g., `gemini-1.5-flash-latest` for speed/cost, `gemini-1.5-pro-latest` for complex analysis) and the `prompt_file_path` based on the specific task requirements.
*   Consider using the `--batch` mode of `generalized_gemini_runner.py` via `RunnerAgent` for efficiency when processing a directory of images with the same prompt/model, potentially simplifying the need for a complex wrapper script. 