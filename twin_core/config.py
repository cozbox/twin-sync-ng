"""Configuration handling for TwinSync++."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from . import paths
from . import utils

DEFAULT_CONFIG = {
    "twin_repo": str(Path.home() / "twinsync-device"),
    "filesystem_roots": ["/etc", str(Path.home() / ".config")],
    "github": {
        "user": "",
        "token": "",
        "device_repo": "",
    },
    "plugins": {
        "enable": [
            "system.info",
            "packages.debian",
            "services.systemd",
            "files.mirror",
            "cron.user",
            "logs.systemd_journal",
            "logs.files",
        ]
    }
}

# Legacy config location for compatibility with bash version
LEGACY_CONFIG_DIR = Path.home() / ".config" / "twinsync"
LEGACY_CONFIG_FILE = LEGACY_CONFIG_DIR / "config"


def load_config(repo_root: Path | None = None) -> Dict:
    """Load configuration from the device repo or legacy location.
    
    Priority:
    1. repo_root/config.yaml (new Python format)
    2. ~/.config/twinsync/config (legacy bash format)
    3. DEFAULT_CONFIG
    """
    repo_root = repo_root or paths.get_device_repo_root()
    config_path = paths.get_config_path(repo_root)
    
    # Try new YAML config first
    if config_path.exists():
        data = utils.load_yaml(config_path)
        # Ensure all required keys exist
        for key, value in DEFAULT_CONFIG.items():
            if key not in data:
                data[key] = value
        return data
    
    # Try legacy bash config
    if LEGACY_CONFIG_FILE.exists():
        data = _load_legacy_config()
        # Migrate to new format
        save_config(data, repo_root)
        return data
    
    # Use defaults
    save_config(DEFAULT_CONFIG, repo_root)
    return DEFAULT_CONFIG.copy()


def _load_legacy_config() -> Dict:
    """Load legacy bash-style config from ~/.config/twinsync/config."""
    config = DEFAULT_CONFIG.copy()
    
    if not LEGACY_CONFIG_FILE.exists():
        return config
    
    try:
        content = LEGACY_CONFIG_FILE.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                
                if key == "TWIN_REPO":
                    config["twin_repo"] = value
                elif key == "GITHUB_USER":
                    config["github"]["user"] = value
                elif key == "GITHUB_TOKEN":
                    config["github"]["token"] = value
                elif key == "GITHUB_DEVICE_REPO":
                    config["github"]["device_repo"] = value
                elif key == "FS_ROOTS":
                    config["filesystem_roots"] = value.split()
    except Exception:
        pass
    
    return config


def save_config(config: Dict, repo_root: Path | None = None) -> None:
    """Save configuration to both new and legacy locations for compatibility."""
    repo_root = repo_root or paths.get_device_repo_root()
    
    # Save to new YAML location
    config_path = paths.get_config_path(repo_root)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    utils.dump_yaml(config_path, config)
    
    # Also save to legacy location for bash script compatibility
    _save_legacy_config(config)


def _save_legacy_config(config: Dict) -> None:
    """Save config in legacy bash format for compatibility."""
    LEGACY_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    twin_repo = config.get("twin_repo", DEFAULT_CONFIG["twin_repo"])
    github = config.get("github", DEFAULT_CONFIG["github"])
    fs_roots = config.get("filesystem_roots", DEFAULT_CONFIG["filesystem_roots"])
    
    content = f"""TWIN_REPO="{twin_repo}"
GITHUB_USER="{github.get('user', '')}"
GITHUB_TOKEN="{github.get('token', '')}"
GITHUB_DEVICE_REPO="{github.get('device_repo', '')}"
FS_ROOTS="{' '.join(fs_roots)}"
"""
    LEGACY_CONFIG_FILE.write_text(content, encoding="utf-8")


def get_twin_repo_path(config: Optional[Dict] = None) -> Path:
    """Get the configured twin repo path."""
    if config is None:
        config = load_config()
    return Path(config.get("twin_repo", DEFAULT_CONFIG["twin_repo"]))


def get_filesystem_roots(config: Optional[Dict] = None) -> List[str]:
    """Get the configured filesystem roots to mirror."""
    if config is None:
        config = load_config()
    return config.get("filesystem_roots", DEFAULT_CONFIG["filesystem_roots"])


def get_github_credentials(config: Optional[Dict] = None) -> Dict[str, str]:
    """Get GitHub credentials from config."""
    if config is None:
        config = load_config()
    return config.get("github", DEFAULT_CONFIG["github"])


def set_github_credentials(user: str, token: str, device_repo: str = "", 
                          repo_root: Path | None = None) -> None:
    """Set GitHub credentials in config."""
    config = load_config(repo_root)
    if "github" not in config:
        config["github"] = {}
    config["github"]["user"] = user
    config["github"]["token"] = token
    if device_repo:
        config["github"]["device_repo"] = device_repo
    save_config(config, repo_root)


def set_filesystem_roots(roots: List[str], repo_root: Path | None = None) -> None:
    """Set filesystem roots in config."""
    config = load_config(repo_root)
    config["filesystem_roots"] = roots
    save_config(config, repo_root)
