"""GUI settings: Load and save application state to mjlog.toml."""

import tomllib
from pathlib import Path
from typing import Any

import tomli_w


def get_settings_file() -> Path:
    """Get mjlog.toml path (in project root)."""
    repo_root = Path(__file__).parent.parent.parent.parent
    return repo_root / "mjlog.toml"


def load_window_state(window_name: str) -> dict[str, Any]:
    """Load saved window state from mjlog.toml."""
    settings_file = get_settings_file()
    if not settings_file.exists():
        return {}

    try:
        with open(settings_file, "rb") as f:
            data = tomllib.load(f)
        return data.get(window_name, {})
    except (tomllib.TOMLDecodeError, IOError):
        return {}


def save_window_state(window_name: str, state: dict[str, Any]) -> None:
    """Save window state to mjlog.toml."""
    settings_file = get_settings_file()

    # Load existing data
    try:
        if settings_file.exists():
            with open(settings_file, "rb") as f:
                data = tomllib.load(f)
        else:
            data = {}
    except (tomllib.TOMLDecodeError, IOError):
        data = {}

    # Update window state
    data[window_name] = state

    # Write back
    with open(settings_file, "wb") as f:
        tomli_w.dump(data, f)
