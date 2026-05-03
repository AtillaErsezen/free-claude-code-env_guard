"""Tests for guard/hooks.py — HookRegistry event firing."""

from __future__ import annotations

import pytest

from guard.hooks import HookEvent, HookRegistry


class _RecordingHook:
    def __init__(self) -> None:
        self.calls: list[HookEvent] = []

    async def run(self, event: HookEvent) -> None:
        self.calls.append(event)


@pytest.mark.asyncio
async def test_registered_hook_is_called() -> None:
    registry = HookRegistry()
    hook = _RecordingHook()
    registry.register(HookEvent.PRE_FORWARD, hook)

    await registry.fire(HookEvent.PRE_FORWARD)

    assert hook.calls == [HookEvent.PRE_FORWARD]


@pytest.mark.asyncio
async def test_hook_not_called_for_different_event() -> None:
    registry = HookRegistry()
    hook = _RecordingHook()
    registry.register(HookEvent.PRE_FORWARD, hook)

    await registry.fire(HookEvent.POST_FORWARD)

    assert hook.calls == []


@pytest.mark.asyncio
async def test_multiple_hooks_all_called() -> None:
    registry = HookRegistry()
    hooks = [_RecordingHook(), _RecordingHook()]
    for h in hooks:
        registry.register(HookEvent.PRE_FORWARD, h)

    await registry.fire(HookEvent.PRE_FORWARD)

    for h in hooks:
        assert h.calls == [HookEvent.PRE_FORWARD]


@pytest.mark.asyncio
async def test_fire_with_no_hooks_is_safe() -> None:
    registry = HookRegistry()
    await registry.fire(HookEvent.PRE_FORWARD)


@pytest.mark.asyncio
async def test_env_lock_hook_calls_cipher(tmp_path, monkeypatch) -> None:
    from guard.env_hook import EnvLockHook

    calls: list[str] = []
    monkeypatch.setattr("guard.env_hook.lock_all", lambda: calls.append("lock_all"))

    hook = EnvLockHook()
    await hook.run(HookEvent.PRE_FORWARD)

    assert calls == ["lock_all"]


@pytest.mark.asyncio
async def test_env_unlock_hook_calls_cipher(tmp_path, monkeypatch) -> None:
    from guard.env_hook import EnvUnlockHook

    calls: list[str] = []
    monkeypatch.setattr("guard.env_hook.unlock_all", lambda: calls.append("unlock_all"))

    hook = EnvUnlockHook()
    await hook.run(HookEvent.POST_FORWARD)

    assert calls == ["unlock_all"]
