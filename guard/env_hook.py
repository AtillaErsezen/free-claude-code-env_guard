"""EnvLockHook / EnvUnlockHook — encrypt/decrypt .env around provider requests."""

from __future__ import annotations

from .cipher import lock, unlock
from .hooks import HookEvent


class EnvLockHook:
    async def run(self, event: HookEvent) -> None:
        lock()


class EnvUnlockHook:
    async def run(self, event: HookEvent) -> None:
        unlock()
