"""Tests for guard/cipher.py — lock/unlock lifecycle."""

from __future__ import annotations

from pathlib import Path

import pytest

from guard.cipher import _LOCKED_MARKER, lock, unlock


@pytest.fixture()
def env_files(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Return (env, enc, key_file) paths inside tmp_path."""
    env = tmp_path / ".env"
    enc = tmp_path / ".env.enc"
    key_file = tmp_path / ".env.key"
    return env, enc, key_file


def test_lock_encrypts_env(env_files: tuple[Path, Path, Path]) -> None:
    env, enc, key_file = env_files
    env.write_bytes(b"SECRET=abc\n")

    result = lock(env, enc, key_file)

    assert result is True
    assert enc.exists()
    assert env.read_bytes() == _LOCKED_MARKER


def test_lock_ciphertext_differs_from_plaintext(
    env_files: tuple[Path, Path, Path],
) -> None:
    env, enc, key_file = env_files
    env.write_bytes(b"SECRET=abc\n")

    lock(env, enc, key_file)

    assert enc.read_bytes() != b"SECRET=abc\n"


def test_unlock_restores_original(env_files: tuple[Path, Path, Path]) -> None:
    env, enc, key_file = env_files
    original = b"SECRET=abc\nANOTHER=xyz\n"
    env.write_bytes(original)

    lock(env, enc, key_file)
    result = unlock(env, enc, key_file)

    assert result is True
    assert env.read_bytes() == original
    assert not enc.exists()


def test_lock_is_idempotent(env_files: tuple[Path, Path, Path]) -> None:
    env, enc, key_file = env_files
    env.write_bytes(b"SECRET=abc\n")

    lock(env, enc, key_file)
    second = lock(env, enc, key_file)

    assert second is False


def test_lock_returns_false_when_no_env(env_files: tuple[Path, Path, Path]) -> None:
    env, enc, key_file = env_files

    result = lock(env, enc, key_file)

    assert result is False


def test_unlock_returns_false_when_no_enc(env_files: tuple[Path, Path, Path]) -> None:
    env, enc, key_file = env_files

    result = unlock(env, enc, key_file)

    assert result is False


def test_key_file_created_on_first_lock(env_files: tuple[Path, Path, Path]) -> None:
    env, enc, key_file = env_files
    env.write_bytes(b"SECRET=abc\n")

    assert not key_file.exists()
    lock(env, enc, key_file)
    assert key_file.exists()


def test_same_key_used_across_lock_unlock(env_files: tuple[Path, Path, Path]) -> None:
    env, enc, key_file = env_files
    original = b"KEY=value\n"
    env.write_bytes(original)

    lock(env, enc, key_file)
    unlock(env, enc, key_file)

    assert env.read_bytes() == original


# ---------------------------------------------------------------------------
# lock_all / unlock_all
# ---------------------------------------------------------------------------


from guard.cipher import ENV_GLOB_PATTERNS, lock_all, unlock_all  # noqa: E402


def test_lock_all_encrypts_multiple_variants(tmp_path: Path) -> None:
    """lock_all() encrypts every dotenv variant that exists in the directory."""
    key_file = tmp_path / ".env.key"
    variants = [".env", ".env.dev", ".env.production"]
    for name in variants:
        (tmp_path / name).write_bytes(f"SECRET_{name}=1\n".encode())

    count = lock_all(tmp_path, key_file)

    assert count == len(variants)
    for name in variants:
        assert (tmp_path / (name + ".enc")).exists()
        assert (tmp_path / name).read_bytes() != f"SECRET_{name}=1\n".encode()


def test_lock_all_skips_absent_files(tmp_path: Path) -> None:
    """lock_all() does not fail when most variants are absent."""
    key_file = tmp_path / ".env.key"
    (tmp_path / ".env").write_bytes(b"KEY=value\n")

    count = lock_all(tmp_path, key_file)

    assert count == 1


def test_lock_all_returns_zero_when_nothing_to_lock(tmp_path: Path) -> None:
    """lock_all() returns 0 when no recognised dotenv files exist."""
    key_file = tmp_path / ".env.key"

    count = lock_all(tmp_path, key_file)

    assert count == 0


def test_unlock_all_restores_all_variants(tmp_path: Path) -> None:
    """unlock_all() decrypts every encrypted sidecar back to its original file."""
    key_file = tmp_path / ".env.key"
    originals: dict[str, bytes] = {}
    for name in [".env", ".env.staging", ".env.local"]:
        data = f"VAR_{name}=secret\n".encode()
        originals[name] = data
        (tmp_path / name).write_bytes(data)

    lock_all(tmp_path, key_file)
    count = unlock_all(tmp_path, key_file)

    assert count == 3
    for name, data in originals.items():
        assert (tmp_path / name).read_bytes() == data
        assert not (tmp_path / (name + ".enc")).exists()


def test_lock_all_only_covers_known_patterns(tmp_path: Path) -> None:
    """lock_all() ignores arbitrary .env.* files not in ENV_GLOB_PATTERNS."""
    key_file = tmp_path / ".env.key"
    (tmp_path / ".env.custom").write_bytes(b"CUSTOM=1\n")

    count = lock_all(tmp_path, key_file)

    assert count == 0
    assert not (tmp_path / ".env.custom.enc").exists()


def test_all_env_glob_patterns_are_gitignored() -> None:
    """Every pattern in ENV_GLOB_PATTERNS has a corresponding .enc entry in .gitignore."""
    gitignore = (Path(__file__).resolve().parents[2] / ".gitignore").read_text(
        encoding="utf-8"
    )
    for name in ENV_GLOB_PATTERNS:
        enc_entry = name + ".enc"
        assert enc_entry in gitignore, f"{enc_entry} missing from .gitignore"
