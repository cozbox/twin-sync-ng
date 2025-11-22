"""Utility functions for TwinSync++."""
from __future__ import annotations

import datetime
import importlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _yaml_module():
    """Get PyYAML module if available."""
    spec = importlib.util.find_spec("yaml")
    if spec is None:
        return None
    return importlib.import_module("yaml")


def load_yaml(path: Path) -> Dict:
    """Load YAML or JSON file."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    module = _yaml_module()
    if module:
        return module.safe_load(text) or {}
    return json.loads(text) if text else {}


def dump_yaml(path: Path, data: Any) -> None:
    """Save data as YAML or JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    module = _yaml_module()
    if module:
        text = module.safe_dump(data, sort_keys=False)
    else:
        text = json.dumps(data, indent=2)
    path.write_text(text, encoding="utf-8")


# File operations
def copy_file_safe(src: Path, dest: Path, backup: bool = True) -> bool:
    """Copy a file safely with optional backup."""
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup if destination exists
        if backup and dest.exists():
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            backup_path = Path(str(dest) + f".twinbak-{timestamp}")
            shutil.copy2(dest, backup_path)
        
        shutil.copy2(src, dest)
        return True
    except Exception as e:
        print(f"Failed to copy {src} to {dest}: {e}")
        return False


def is_text_file(path: Path, max_size_mb: int = 1) -> bool:
    """Check if file is text and under size limit."""
    try:
        if not path.is_file():
            return False
        
        # Check size
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > max_size_mb:
            return False
        
        # Try to read as text
        with open(path, 'rb') as f:
            chunk = f.read(512)
            if b'\x00' in chunk:  # Binary file indicator
                return False
        
        return True
    except Exception:
        return False


def walk_directory(root: Path, max_size_mb: int = 1) -> List[Path]:
    """Walk directory and return list of files under size limit."""
    files = []
    try:
        for item in root.rglob("*"):
            if item.is_file() and is_text_file(item, max_size_mb):
                files.append(item)
    except Exception as e:
        print(f"Error walking {root}: {e}")
    return files


# Git operations
def git_init(repo_path: Path) -> bool:
    """Initialize a git repository."""
    try:
        if not (repo_path / ".git").exists():
            subprocess.run(
                ["git", "init"],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )
        return True
    except Exception as e:
        print(f"Failed to init git repo at {repo_path}: {e}")
        return False


def git_add_all(repo_path: Path) -> bool:
    """Git add all files."""
    try:
        subprocess.run(
            ["git", "add", "."],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        return True
    except Exception as e:
        print(f"Failed to git add in {repo_path}: {e}")
        return False


def git_commit(repo_path: Path, message: str) -> bool:
    """Commit changes with a message."""
    try:
        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=repo_path,
            capture_output=True,
        )
        if result.returncode == 0:
            # No changes to commit
            return True
        
        # Ensure git user is configured (use generic if not set)
        result = subprocess.run(
            ["git", "config", "user.email"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if not result.stdout.strip():
            subprocess.run(
                ["git", "config", "user.email", "twinsync@localhost"],
                cwd=repo_path,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "TwinSync"],
                cwd=repo_path,
                capture_output=True,
            )
        
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        return True
    except Exception as e:
        print(f"Failed to commit in {repo_path}: {e}")
        return False


def git_push(repo_path: Path, remote: str = "origin", branch: str = "main") -> Tuple[bool, str]:
    """Push to remote repository."""
    try:
        result = subprocess.run(
            ["git", "push", remote, branch],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True, result.stdout + result.stderr
        else:
            return False, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def git_pull(repo_path: Path, remote: str = "origin", branch: str = "main") -> Tuple[bool, str]:
    """Pull from remote repository (fast-forward only)."""
    try:
        result = subprocess.run(
            ["git", "pull", "--ff-only", remote, branch],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True, result.stdout + result.stderr
        else:
            return False, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def git_remote_add(repo_path: Path, name: str, url: str) -> bool:
    """Add a git remote."""
    try:
        # Remove existing remote if present
        subprocess.run(
            ["git", "remote", "remove", name],
            cwd=repo_path,
            capture_output=True,
        )
        
        subprocess.run(
            ["git", "remote", "add", name, url],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        return True
    except Exception as e:
        print(f"Failed to add remote {name} at {url}: {e}")
        return False


def git_set_branch(repo_path: Path, branch: str = "main") -> bool:
    """Set the default branch."""
    try:
        subprocess.run(
            ["git", "branch", "-M", branch],
            cwd=repo_path,
            capture_output=True,
        )
        return True
    except Exception:
        return False


def git_log(repo_path: Path, limit: int = 20) -> List[Dict[str, str]]:
    """Get git log entries."""
    try:
        result = subprocess.run(
            ["git", "log", "--pretty=format:%h\t%ad\t%s", "--date=short", f"-n{limit}"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        
        entries = []
        for line in result.stdout.splitlines():
            parts = line.split("\t", 2)
            if len(parts) == 3:
                entries.append({
                    "hash": parts[0],
                    "date": parts[1],
                    "message": parts[2],
                })
        return entries
    except Exception:
        return []


def git_reset_hard(repo_path: Path, commit: str) -> bool:
    """Reset repository to a specific commit."""
    try:
        subprocess.run(
            ["git", "reset", "--hard", commit],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        return True
    except Exception as e:
        print(f"Failed to reset to {commit}: {e}")
        return False


# System checks
def check_command_exists(command: str) -> bool:
    """Check if a command is available in PATH."""
    return shutil.which(command) is not None


def check_dependencies(required: Optional[List[str]] = None) -> Dict[str, bool]:
    """Check if required dependencies are installed."""
    if required is None:
        required = ["git", "whiptail"]
    
    results = {}
    for cmd in required:
        results[cmd] = check_command_exists(cmd)
    return results


def run_command(cmd: List[str], check: bool = False, capture: bool = True) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            check=check,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout or "", e.stderr or ""
    except Exception as e:
        return -1, "", str(e)


def get_hostname() -> str:
    """Get the system hostname."""
    try:
        result = subprocess.run(
            ["hostname"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "device"
