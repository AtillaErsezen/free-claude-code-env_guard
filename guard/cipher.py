"""Fernet-based encrypt/decrypt for .env files."""

from __future__ import annotations

from pathlib import Path

from cryptography.fernet import Fernet

_DEFAULT_KEY_FILE = Path.home() / ".config" / "free-claude-code" / ".env.key"
_DEFAULT_ENV = Path(".env")
_DEFAULT_ENC = Path(".env.enc")

# All dotenv filename variants that fcc-guard protects.
# Each plain file gets an encrypted <name>.enc sidecar.
ENV_GLOB_PATTERNS: tuple[str, ...] = (
    ".env",
    ".env.development",
    ".env.dev",
    ".env.local",
    ".env.test",
    ".env.staging",
    ".env.prod",
    ".env.production",
)
_LOCKED_MARKER = b"# locked by fcc-guard\n"


def _load_or_create_key(key_file: Path = _DEFAULT_KEY_FILE) -> bytes:
    if key_file.exists():
        return key_file.read_bytes().strip()
    key = Fernet.generate_key()
    key_file.parent.mkdir(parents=True, exist_ok=True)
    key_file.write_bytes(key)
    key_file.chmod(0o600)
    return key


def lock(
    env: Path = _DEFAULT_ENV,
    enc: Path = _DEFAULT_ENC,
    key_file: Path = _DEFAULT_KEY_FILE,
) -> bool:
    """Encrypt env → enc, replace env with a placeholder. Returns True if newly locked."""
    if not env.exists() or enc.exists():
        return False
    content = env.read_bytes()
    if content == _LOCKED_MARKER:
        return False
    token = Fernet(_load_or_create_key(key_file)).encrypt(content)
    enc.write_bytes(token)
    env.write_bytes(_LOCKED_MARKER)
    return True


def unlock(
    env: Path = _DEFAULT_ENV,
    enc: Path = _DEFAULT_ENC,
    key_file: Path = _DEFAULT_KEY_FILE,
) -> bool:
    """Decrypt enc → env. Returns True if successfully unlocked."""
    if not enc.exists():
        return False
    content = Fernet(_load_or_create_key(key_file)).decrypt(enc.read_bytes())
    env.write_bytes(content)
    enc.unlink()
    return True


def lock_all(cwd: Path = Path("."), key_file: Path = _DEFAULT_KEY_FILE) -> int:
    """Encrypt every matching dotenv file in *cwd*. Returns count of newly locked files."""
    locked = 0
    for name in ENV_GLOB_PATTERNS:
        env = cwd / name
        enc = cwd / (name + ".enc")
        if lock(env, enc, key_file):
            locked += 1
    return locked


def unlock_all(cwd: Path = Path("."), key_file: Path = _DEFAULT_KEY_FILE) -> int:
    """Decrypt every matching dotenv sidecar in *cwd*. Returns count of unlocked files."""
    unlocked = 0
    for name in ENV_GLOB_PATTERNS:
        env = cwd / name
        enc = cwd / (name + ".enc")
        if unlock(env, enc, key_file):
            unlocked += 1
    return unlocked
