---
name: agent-use
description: Call a user-configured external coding or reasoning agent from Codex, pass the user's task to that agent, capture its visible output/logs, and include a concise work-process summary in the final answer. Use when the user invokes agent-use, asks Codex to call a specified agent, asks to delegate a task to another local agent such as claudecodeagent, or explicitly asks to change the configured external agent command for future agent-use runs.
---

# Agent Use

Use this skill to delegate a task to the configured external agent and report the visible work back to the user.

## Core Rules

- Use the configured agent command in `references/config.json` for normal agent-use tasks.
- Do not change the configured command unless the user explicitly asks to change, replace, switch, update, or configure the agent.
- Preserve the ability to change agents later by keeping all agent command details in `references/config.json`.
- Treat the external agent as advisory unless the user asks it to modify files. Review its output before presenting conclusions.
- In the final answer, include what task was sent, which configured agent was used, the visible work/output summary, and Codex's own conclusion or handoff.
- Save external-agent visible run artifacts under the current conversation/project directory, normally `work/agent-use/`. Do not default to user-home or system-level locations for agent-use artifacts.
- For Claude Code based commands, keep `--no-session-persistence` unless the user explicitly asks to enable persistent Claude sessions.
- Do not claim access to the external agent's hidden reasoning. Summarize only visible stdout, stderr, structured JSON, file changes, and logs.

## Normal Workflow

1. Restate the delegated task briefly.
2. Run `scripts/invoke_agent.py` with the task prompt from the conversation/project working directory.
3. Read the run artifact path printed by the script if a detailed summary is needed.
4. Inspect any file changes if the external agent was allowed to edit the workspace.
5. Produce a final answer that separates:
   - external agent used
   - visible work summary
   - result or recommendation
   - any limitations, errors, or follow-up needed

Example:

```powershell
python "$env:USERPROFILE\.codex\skills\agent-use\scripts\invoke_agent.py" --prompt "Review this project and identify the top risks."
```

For longer prompts, write the task to a temporary file under the project `work/` directory and pass `--prompt-file`.

```powershell
python "$env:USERPROFILE\.codex\skills\agent-use\scripts\invoke_agent.py" --prompt-file 'work\agent-task.txt'
```

## Changing Agents

Only do this when the user explicitly asks to change the configured agent or command.

Update `references/config.json` instead of hardcoding command details in `SKILL.md`. Keep `{prompt}` exactly once in the command array where the delegated task should be inserted.

After changing config:

1. Tell the user the new configured agent label and command shape.
2. Run a lightweight validation such as `--show-config`.
3. Do not run a real delegated task unless the user asked for one.

## Configuration

Read `references/config.json` when using or changing the configured agent.

Important fields:

- `agent_label`: Human-readable name to show in summaries.
- `command`: Command array executed by the script. Include `{prompt}` as the placeholder for the task.
- `timeout_seconds`: Maximum runtime for one agent call.
- `summary_mode`: Preferred visible-summary style.
- `working_directory`: Optional working directory. Empty means use the current directory.
- `project_scoped_artifacts`: Keep run artifacts inside the active project/conversation directory.

The invoke script rejects artifact output directories outside the active working directory unless Codex intentionally passes an override flag. Do not use that override for normal agent-use runs.

## Reporting Pattern

Keep the user-facing summary short and auditable:

```text
Used: <agent_label>
Sent task: <one sentence>
Visible work: <stdout/stderr/log summary>
Codex check: <your verification or judgment>
Result: <answer, files changed, or next step>
```
