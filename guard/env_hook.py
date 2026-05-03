"""EnvLockHook / EnvUnlockHook — encrypt/decrypt .env variants around provider requests."""

from __future__ import annotations

from .cipher import lock_all, unlock_all
from .hooks import HookEvent


class EnvLockHook:
    async def run(self, event: HookEvent) -> None:
        lock_all()


class EnvUnlockHook:
    async def run(self, event: HookEvent) -> None:
        unlock_all()
