"""Path helpers for TwinSync++ repositories."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

DEFAULT_REPO_NAME = "twinsync-device"


def get_device_repo_root(base: Optional[Path] = None) -> Path:
    """Return the root path for the per-device twin repository.

    The default mirrors the legacy Bash script location of ``~/twinsync-device``.
    The directory is created if it does not already exist.
    """

    if base is None:
        base = Path.home()
    repo_root = base / DEFAULT_REPO_NAME
    repo_root.mkdir(parents=True, exist_ok=True)
    return repo_root


def get_config_path(repo_root: Optional[Path] = None) -> Path:
    repo_root = repo_root or get_device_repo_root()
    config_path = repo_root / "config.yaml"
    if not config_path.parent.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
    return config_path


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_state_dir(repo_root: Optional[Path] = None) -> Path:
    repo_root = repo_root or get_device_repo_root()
    return _ensure_dir(repo_root / "state")


def get_live_dir(repo_root: Optional[Path] = None) -> Path:
    repo_root = repo_root or get_device_repo_root()
    return _ensure_dir(repo_root / "live")


def get_logs_dir(repo_root: Optional[Path] = None) -> Path:
    repo_root = repo_root or get_device_repo_root()
    return _ensure_dir(repo_root / "logs")


def get_logs_current_dir(repo_root: Optional[Path] = None) -> Path:
    return _ensure_dir(get_logs_dir(repo_root) / "current")


def get_logs_timestamp_dir(timestamp: str, repo_root: Optional[Path] = None) -> Path:
    return _ensure_dir(get_logs_dir(repo_root) / timestamp)


def get_plan_dir(repo_root: Optional[Path] = None) -> Path:
    repo_root = repo_root or get_device_repo_root()
    return _ensure_dir(repo_root / "plan")


def get_plan_history_dir(repo_root: Optional[Path] = None) -> Path:
    return _ensure_dir(get_plan_dir(repo_root) / "history")


def get_plugins_dir(repo_root: Optional[Path] = None) -> Path:
    repo_root = repo_root or get_device_repo_root()
    return _ensure_dir(repo_root / "plugins")


def get_schema_dir(repo_root: Optional[Path] = None) -> Path:
    repo_root = repo_root or get_device_repo_root()
    return _ensure_dir(repo_root / "schema")


def ensure_repo_layout(repo_root: Optional[Path] = None) -> Path:
    """Create the canonical TwinSync++ directory layout and return the root."""

    repo_root = repo_root or get_device_repo_root()
    _ensure_dir(repo_root)
    get_state_dir(repo_root)
    get_live_dir(repo_root)
    logs_dir = get_logs_dir(repo_root)
    _ensure_dir(logs_dir / "current")
    plan_dir = get_plan_dir(repo_root)
    _ensure_dir(plan_dir / "history")
    get_plugins_dir(repo_root)
    get_schema_dir(repo_root)
    return repo_root
