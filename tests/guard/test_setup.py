"""Tests for guard/setup.py — idempotent Claude Stop hook injection."""

from __future__ import annotations

import json
from pathlib import Path

from guard.setup import _STOP_COMMAND, ensure_claude_stop_hook


def test_stop_hook_injected_into_empty_settings(tmp_path: Path) -> None:
    settings = tmp_path / ".claude" / "settings.local.json"

    result = ensure_claude_stop_hook(settings)

    assert result is True
    data = json.loads(settings.read_text(encoding="utf-8"))
    commands = [h["command"] for m in data["hooks"]["Stop"] for h in m["hooks"]]
    assert _STOP_COMMAND in commands


def test_stop_hook_injected_when_settings_missing(tmp_path: Path) -> None:
    settings = tmp_path / ".claude" / "settings.local.json"
    assert not settings.exists()

    ensure_claude_stop_hook(settings)

    assert settings.exists()


def test_stop_hook_injected_into_existing_settings(tmp_path: Path) -> None:
    settings = tmp_path / ".claude" / "settings.local.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(
        json.dumps({"permissions": {"allow": ["Bash(uv run *)"]}}),
        encoding="utf-8",
    )

    ensure_claude_stop_hook(settings)

    data = json.loads(settings.read_text(encoding="utf-8"))
    assert data["permissions"]["allow"] == ["Bash(uv run *)"]
    commands = [h["command"] for m in data["hooks"]["Stop"] for h in m["hooks"]]
    assert _STOP_COMMAND in commands


def test_stop_hook_idempotent(tmp_path: Path) -> None:
    settings = tmp_path / ".claude" / "settings.local.json"
    ensure_claude_stop_hook(settings)
    first_content = settings.read_text(encoding="utf-8")

    result = ensure_claude_stop_hook(settings)

    assert result is False
    assert settings.read_text(encoding="utf-8") == first_content


def test_stop_hook_does_not_duplicate_existing_hook(tmp_path: Path) -> None:
    settings = tmp_path / ".claude" / "settings.local.json"
    ensure_claude_stop_hook(settings)
    ensure_claude_stop_hook(settings)

    data = json.loads(settings.read_text(encoding="utf-8"))
    commands = [h["command"] for m in data["hooks"]["Stop"] for h in m["hooks"]]
    assert commands.count(_STOP_COMMAND) == 1
