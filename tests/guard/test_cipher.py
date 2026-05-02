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
