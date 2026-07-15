# agent-use skill

`agent-use` is a Codex skill for calling a configured external agent from a Codex conversation, capturing the agent's visible output, and summarizing that visible work back to the user.

## Install

Install the skill from this repository path:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo peikaizhao80-wq/agent-use-skill --path skills/agent-use
```

## Default behavior

- Delegates the task to the configured external agent.
- Saves visible run artifacts under the active project directory, normally `work/agent-use/`.
- Uses `--no-session-persistence` for the default Claude Code command.
- Does not change the configured external agent unless the user explicitly asks to switch or update it.

## Change the external agent

Edit:

```text
skills/agent-use/references/config.json
```

Keep exactly one `{prompt}` placeholder in the `command` array.

## Files

- `skills/agent-use/SKILL.md`: Codex skill instructions.
- `skills/agent-use/references/config.json`: External-agent command configuration.
- `skills/agent-use/scripts/invoke_agent.py`: Invocation helper that captures visible stdout/stderr artifacts.
- `skills/agent-use/agents/openai.yaml`: UI metadata.
