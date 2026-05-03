"""CLI entry points for the installed package."""

from __future__ import annotations

import sys as _sys
from pathlib import Path


def _load_env_template() -> str:
    """Load the canonical root env template from package resources or source."""
    import importlib.resources

    packaged = importlib.resources.files("cli").joinpath("env.example")
    if packaged.is_file():
        return packaged.read_text("utf-8")

    source_template = Path(__file__).resolve().parents[1] / ".env.example"
    if source_template.is_file():
        return source_template.read_text(encoding="utf-8")

    raise FileNotFoundError("Could not find bundled or source .env.example template.")


def guard_lock() -> None:
    """Encrypt all .env variants in place (registered as `fcc-guard-lock` script)."""
    from guard.cipher import lock_all

    count = lock_all()
    print(
        f".env guard: locked {count} file(s)"
        if count
        else ".env guard: nothing to lock"
    )


def guard_unlock() -> None:
    """Decrypt all .env.enc sidecars (registered as `fcc-guard-unlock` script)."""
    from guard.cipher import unlock_all

    count = unlock_all()
    print(
        f".env guard: unlocked {count} file(s)"
        if count
        else ".env guard: nothing to unlock"
    )


# ANSI colour codes — suppressed when stdout is not a real terminal.
_USE_COLOR = _sys.stdout.isatty()

_B = "\033[34m" if _USE_COLOR else ""  # blue   (border)
_T = "\033[1;32m" if _USE_COLOR else ""  # bold green (title)
_Y = "\033[33m" if _USE_COLOR else ""  # yellow (section headings)
_D = "\033[2m" if _USE_COLOR else ""  # dim    (body text)
_R = "\033[0m" if _USE_COLOR else ""  # reset

# Inner width (visible characters between the two ║ borders, including spaces).
_W = 60
_TOP = f"{_B}╔{'═' * _W}╗{_R}"
_MID = f"{_B}╠{'═' * _W}╣{_R}"
_BOT = f"{_B}╚{'═' * _W}╝{_R}"


def _row(text: str = "", *, visible_len: int = 0) -> str:
    """Return one box row, padding *text* to _W visible characters.

    *visible_len* must equal len(text) minus the total byte-length of any
    embedded ANSI escape sequences — i.e. the number of printed columns.
    """
    pad = _W - 2 - visible_len  # 2 for the leading space after ║
    return f"{_B}║{_R} {text}{' ' * pad} {_B}║{_R}"


def _plain(label: str) -> str:
    """A plain (uncoloured) row."""
    return _row(label, visible_len=len(label))


def _section(label: str) -> str:
    """A yellow section-heading row."""
    return _row(f"{_Y}{label}{_R}", visible_len=len(label))


def _body(label: str) -> str:
    """A dim body-text row."""
    return _row(f"{_D}{label}{_R}", visible_len=len(label))


_TITLE = ".env guard is active"
_title_pad = (_W - 2 - len(_TITLE)) // 2  # centre the title

_GUARD_BANNER = "\n".join(
    [
        _TOP,
        _row(
            f"{' ' * _title_pad}{_T}{_TITLE}{_R}",
            visible_len=_title_pad + len(_TITLE),
        ),
        _MID,
        _section("WHY"),
        _body("Your .env files contain API keys and secrets. Without"),
        _body("protection, Claude can read them via the Read tool and"),
        _body("the contents end up in the model's context window."),
        _plain(""),
        _section("HOW IT WORKS"),
        _body("Each time you submit a prompt, the proxy encrypts .env"),
        _body("files with AES-128 (Fernet). The plaintext is gone before"),
        _body("the request reaches the model. The running server is"),
        _body("unaffected because settings are already loaded in memory."),
        _plain(""),
        _section("AUTOMATIC RESTORE"),
        _body("Your .env files are restored automatically after each"),
        _body("response."),
        _BOT,
    ]
)


def fcc_claude() -> None:
    """Launch Claude CLI with the .env guard banner (registered as `fcc-claude` script)."""
    import subprocess
    import sys

    from guard.setup import ensure_claude_stop_hook

    ensure_claude_stop_hook()
    print(_GUARD_BANNER)
    result = subprocess.run(["claude", *sys.argv[1:]])
    sys.exit(result.returncode)


def serve() -> None:
    """Start the FastAPI server (registered as `free-claude-code` script)."""
    import uvicorn

    from cli.process_registry import kill_all_best_effort
    from config.settings import get_settings

    settings = get_settings()
    try:
        uvicorn.run(
            "api.app:create_asgi_app",
            factory=True,
            host=settings.host,
            port=settings.port,
            log_level="debug",
            timeout_graceful_shutdown=5,
        )
    finally:
        kill_all_best_effort()


def init() -> None:
    """Scaffold config at ~/.config/free-claude-code/.env (registered as `fcc-init`)."""
    config_dir = Path.home() / ".config" / "free-claude-code"
    env_file = config_dir / ".env"

    if env_file.exists():
        print(f"Config already exists at {env_file}")
        print("Delete it first if you want to reset to defaults.")
        return

    config_dir.mkdir(parents=True, exist_ok=True)
    template = _load_env_template()
    env_file.write_text(template, encoding="utf-8")
    print(f"Config created at {env_file}")
    print(
        "Edit it to set your API keys and model preferences, then run: free-claude-code"
    )
