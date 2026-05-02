"""Fernet-based encrypt/decrypt for .env files."""

from __future__ import annotations

from pathlib import Path

from cryptography.fernet import Fernet

_DEFAULT_KEY_FILE = Path.home() / ".config" / "free-claude-code" / ".env.key"
_DEFAULT_ENV = Path(".env")
_DEFAULT_ENC = Path(".env.enc")
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
