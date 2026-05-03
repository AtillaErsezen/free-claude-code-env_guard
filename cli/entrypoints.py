"""CLI entry points for the installed package."""

from __future__ import annotations

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
    """Encrypt .env in place (registered as `fcc-guard-lock` script)."""
    from guard.cipher import lock

    locked = lock()
    print(
        "fcc-guard: locked" if locked else "fcc-guard: already locked or no .env found"
    )


def guard_unlock() -> None:
    """Decrypt .env back from .env.enc (registered as `fcc-guard-unlock` script)."""
    from guard.cipher import unlock

    unlocked = unlock()
    print("fcc-guard: unlocked" if unlocked else "fcc-guard: nothing to unlock")


_GUARD_BANNER = """\
╔══════════════════════════════════════════════════════════════╗
║                    fcc-guard is active                       ║
╠══════════════════════════════════════════════════════════════╣
║  WHY                                                         ║
║  Your .env file contains API keys and secrets. Without       ║
║  protection, Claude can read it via the Read tool and the    ║
║  contents end up in the model's context window.              ║
║                                                              ║
║  HOW IT WORKS                                                ║
║  Each time you submit a prompt, the proxy encrypts .env      ║
║  with AES-128 (Fernet). The plaintext is gone before the     ║
║  request reaches the model. The running server is unaffected ║
║  because settings are already loaded in memory.              ║
║                                                              ║
║  TO RESTORE YOUR .env WHEN DONE                              ║
║    fcc-guard-unlock                                          ║
╚══════════════════════════════════════════════════════════════╝
"""


def fcc_claude() -> None:
    """Launch Claude CLI with the fcc-guard banner (registered as `fcc-claude` script)."""
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
