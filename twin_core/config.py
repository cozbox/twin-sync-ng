"""Configuration handling for TwinSync++."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

from . import paths
from . import utils

DEFAULT_CONFIG = {
    "plugins": {
        "enable": [
            "packages.debian",
            "services.systemd",
            "files.mirror",
            "cron.user",
            "logs.systemd_journal",
            "logs.files",
        ]
    }
}


def load_config(repo_root: Path | None = None) -> Dict:
    """Load ``config.yaml`` from the device repo, creating a default if missing."""

    repo_root = repo_root or paths.get_device_repo_root()
    config_path = paths.get_config_path(repo_root)
    if not config_path.exists():
        save_config(DEFAULT_CONFIG, repo_root)
        return DEFAULT_CONFIG.copy()

    data = utils.load_yaml(config_path)
    if "plugins" not in data:
        data["plugins"] = DEFAULT_CONFIG["plugins"]
    return data


def save_config(config: Dict, repo_root: Path | None = None) -> None:
    repo_root = repo_root or paths.get_device_repo_root()
    config_path = paths.get_config_path(repo_root)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    utils.dump_yaml(config_path, config)
