#!/usr/bin/env python
"""Invoke the configured external agent and save visible run artifacts."""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = SKILL_DIR / "references" / "config.json"


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        config = json.load(f)
    command = config.get("command")
    if not isinstance(command, list) or not all(isinstance(x, str) for x in command):
        raise ValueError("config.command must be a list of strings")
    prompt_count = sum(part.count("{prompt}") for part in command)
    if prompt_count != 1:
        raise ValueError("config.command must contain exactly one {prompt} placeholder")
    return config


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt and args.prompt_file:
        raise ValueError("Use either --prompt or --prompt-file, not both")
    if args.prompt:
        return args.prompt
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise ValueError("Provide --prompt, --prompt-file, or stdin")


def build_command(command_template: list[str], prompt: str) -> list[str]:
    expanded = []
    for part in command_template:
        value = part.replace("{prompt}", prompt)
        if value != prompt:
            value = os.path.expanduser(os.path.expandvars(value))
        expanded.append(value)
    return expanded


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def safe_run_id() -> str:
    return _dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def main() -> int:
    parser = argparse.ArgumentParser(description="Invoke the configured external agent.")
    parser.add_argument("--prompt", help="Task prompt to send to the configured agent.")
    parser.add_argument("--prompt-file", help="UTF-8 text file containing the task prompt.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to config.json.")
    parser.add_argument("--show-config", action="store_true", help="Print effective config and exit.")
    parser.add_argument("--output-dir", default="", help="Directory for visible run artifacts.")
    parser.add_argument(
        "--allow-output-outside-cwd",
        action="store_true",
        help="Allow artifacts outside the active working directory.",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    config = load_config(config_path)

    if args.show_config:
        print(json.dumps(config, ensure_ascii=False, indent=2))
        return 0

    prompt = read_prompt(args).strip()
    if not prompt:
        raise ValueError("Prompt is empty")

    cwd_value = config.get("working_directory") or os.getcwd()
    cwd = Path(cwd_value).resolve()
    timeout = int(config.get("timeout_seconds", 600))
    command = build_command(config["command"], prompt)

    output_dir = Path(args.output_dir) if args.output_dir else cwd / "work" / "agent-use"
    if not output_dir.is_absolute():
        output_dir = cwd / output_dir
    output_dir = output_dir.resolve()
    if config.get("project_scoped_artifacts", True) and not args.allow_output_outside_cwd:
        if not is_relative_to(output_dir, cwd):
            raise ValueError("Artifact output directory must stay inside the active working directory")
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = safe_run_id()
    artifact_path = output_dir / f"{run_id}.json"

    started = _dt.datetime.now().isoformat(timespec="seconds")
    result = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=timeout,
        shell=False,
    )
    finished = _dt.datetime.now().isoformat(timespec="seconds")

    artifact = {
        "run_id": run_id,
        "agent_label": config.get("agent_label", "configured agent"),
        "config_path": str(config_path),
        "cwd": str(cwd),
        "started": started,
        "finished": finished,
        "returncode": result.returncode,
        "prompt": prompt,
        "command_preview": [part if part != prompt else "{prompt}" for part in command],
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "agent_label": artifact["agent_label"],
        "returncode": result.returncode,
        "artifact_path": str(artifact_path),
        "stdout_preview": result.stdout[:4000],
        "stderr_preview": result.stderr[:2000],
    }, ensure_ascii=False, indent=2))

    return result.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.TimeoutExpired as exc:
        print(json.dumps({
            "error": "timeout",
            "timeout_seconds": exc.timeout,
            "message": "The configured external agent timed out."
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(124)
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1)
