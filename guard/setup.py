"""Idempotent project-level setup for fcc-guard."""

from __future__ import annotations

import json
from pathlib import Path

_STOP_COMMAND = "uv run fcc-guard-unlock"
_DEFAULT_CLAUDE_SETTINGS = Path(".claude") / "settings.local.json"


def ensure_claude_stop_hook(settings: Path = _DEFAULT_CLAUDE_SETTINGS) -> bool:
    """Inject the fcc-guard-unlock Stop hook into .claude/settings.local.json if absent.

    Returns True if the file was modified.
    """
    data: dict = (
        json.loads(settings.read_text(encoding="utf-8")) if settings.exists() else {}
    )

    for matcher in data.get("hooks", {}).get("Stop", []):
        for hook in matcher.get("hooks", []):
            if hook.get("command") == _STOP_COMMAND:
                return False

    data.setdefault("hooks", {}).setdefault("Stop", []).append(
        {"hooks": [{"type": "command", "command": _STOP_COMMAND}]}
    )
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True
