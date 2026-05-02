"""Hook system for the env guard — modelled after Claude Code hooks."""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol


class HookEvent(StrEnum):
    PRE_FORWARD = "pre_forward"
    POST_FORWARD = "post_forward"


class Hook(Protocol):
    async def run(self, event: HookEvent) -> None: ...


class HookRegistry:
    def __init__(self) -> None:
        self._hooks: dict[HookEvent, list[Hook]] = {}

    def register(self, event: HookEvent, hook: Hook) -> None:
        self._hooks.setdefault(event, []).append(hook)

    async def fire(self, event: HookEvent) -> None:
        for hook in self._hooks.get(event, []):
            await hook.run(event)
