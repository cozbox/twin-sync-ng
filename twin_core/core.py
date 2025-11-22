"""Core helpers for the TwinSync++ engine."""
from __future__ import annotations

import datetime
import importlib
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import utils
from . import config as config_module
from . import paths
from . import plugins


def load_yaml_file(path: Path) -> Dict:
    return utils.load_yaml(path)


def save_yaml_file(path: Path, data: Dict) -> None:
    utils.dump_yaml(path, data)


def _schema_root() -> Path:
    return Path(__file__).parent / "schema"


def _load_schema(schema_filename: str, repo_root: Path | None = None) -> Dict:
    repo_root = repo_root or paths.get_device_repo_root()
    repo_schema = paths.get_schema_dir(repo_root) / schema_filename
    if repo_schema.exists():
        return utils.load_yaml(repo_schema)
    package_schema = _schema_root() / schema_filename
    return utils.load_yaml(package_schema)


def validate_document(document: Dict, schema_filename: str, repo_root: Path | None = None) -> None:
    spec = importlib.util.find_spec("jsonschema")
    if spec is None:
        return
    jsonschema = importlib.import_module("jsonschema")
    schema = _load_schema(schema_filename, repo_root)
    jsonschema.validate(instance=document, schema=schema)


def init_twin_repo(repo_root: Path | None = None, init_git: bool = True) -> Path:
    """Initialize a twin repository with full structure and optional git init."""
    repo_root = repo_root or paths.get_device_repo_root()
    repo_root = paths.ensure_repo_layout(repo_root)

    # Initialize git if requested
    if init_git:
        utils.git_init(repo_root)
        
        # Create .gitignore if it doesn't exist
        gitignore = repo_root / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text("*.pyc\n__pycache__/\n*.swp\n*.bak\n.DS_Store\n", encoding="utf-8")

    # Copy schemas and plugin definitions into the repo
    schema_dest = paths.get_schema_dir(repo_root)
    for schema_file in _schema_root().glob("*.json"):
        shutil.copy(schema_file, schema_dest / schema_file.name)

    plugin_dest = paths.get_plugins_dir(repo_root)
    package_plugins = Path(__file__).parent / "plugins_definitions"
    for plugin_dir in package_plugins.iterdir():
        if not plugin_dir.is_dir():
            continue
        dest = plugin_dest / plugin_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(plugin_dir, dest)

    # Ensure config exists
    config = config_module.load_config(repo_root)
    config_module.save_config(config, repo_root)

    # Take initial snapshot
    run_snapshot(repo_root, commit=False)

    # Seed state/ with the first live snapshot
    live_dir = paths.get_live_dir(repo_root)
    state_dir = paths.get_state_dir(repo_root)
    for yaml_file in live_dir.glob("*.yaml"):
        shutil.copy(yaml_file, state_dir / yaml_file.name)

    # Initial git commit
    if init_git:
        utils.git_add_all(repo_root)
        utils.git_commit(repo_root, "Initial TwinSync++ repository setup")

    print(f"Initialized twin repository at: {repo_root}")
    return repo_root


def run_snapshot(repo_root: Path | None = None, commit: bool = True, push: bool = False) -> None:
    """Capture live state and logs, optionally commit and push.
    
    Args:
        repo_root: Path to twin repository
        commit: Whether to git commit the changes
        push: Whether to git push after committing
    """
    repo_root = repo_root or paths.get_device_repo_root()
    paths.ensure_repo_layout(repo_root)
    context = plugins.build_context(repo_root)

    # Rotate logs/current if it already contains data
    current_logs = paths.get_logs_current_dir(repo_root)
    if current_logs.exists() and any(current_logs.iterdir()):
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
        dest = paths.get_logs_timestamp_dir(timestamp, repo_root)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.move(str(current_logs), dest)
    current_logs.mkdir(parents=True, exist_ok=True)

    live_dir = paths.get_live_dir(repo_root)
    live_dir.mkdir(parents=True, exist_ok=True)

    # Config plugins - capture current state
    for definition, plugin in plugins.load_config_plugins(context):
        try:
            fragment_names = definition.provides.get("state_fragments", [])
            fragment_payload = plugin.dump_state(context) or {}
            for fragment in fragment_names:
                fragment_data = fragment_payload.get(fragment, {})
                output_path = live_dir / f"{fragment}.yaml"
                save_yaml_file(output_path, {fragment: fragment_data})
        except Exception as e:
            print(f"Warning: Plugin {definition.name} failed during snapshot: {e}")

    # Log plugins build index
    index: Dict[str, object] = {}
    for definition, plugin in plugins.load_logs_plugins(context):
        try:
            fragment_payload = plugin.dump_logs(context) or {}
            index.update(fragment_payload)
        except Exception as e:
            print(f"Warning: Log plugin {definition.name} failed: {e}")

    if index:
        index_path = current_logs / "index.yaml"
        save_yaml_file(index_path, index)

    print(f"Snapshot captured to {live_dir}")

    # Git operations
    if commit and (repo_root / ".git").exists():
        utils.git_add_all(repo_root)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"TwinSync snapshot {timestamp}"
        
        if utils.git_commit(repo_root, message):
            print(f"Snapshot committed: {message}")
            
            # Push if requested and remote is configured
            if push:
                success, output = utils.git_push(repo_root)
                if success:
                    print("Snapshot pushed to remote")
                else:
                    print(f"Push failed or no remote configured: {output}")
        else:
            print("No changes to commit")


def run_plan(repo_root: Path | None = None) -> Dict:
    repo_root = repo_root or paths.get_device_repo_root()
    context = plugins.build_context(repo_root)
    plan: Dict[str, List[Dict]] = {}

    for definition, plugin in plugins.load_config_plugins(context):
        fragments = definition.provides.get("state_fragments", [])
        for fragment in fragments:
            state_path = paths.get_state_dir(repo_root) / f"{fragment}.yaml"
            live_path = paths.get_live_dir(repo_root) / f"{fragment}.yaml"
            desired = load_yaml_file(state_path).get(fragment, {})
            live = load_yaml_file(live_path).get(fragment, {})
            plan_fragment = plugin.plan({fragment: desired}, {fragment: live})
            if plan_fragment:
                plan.update(plan_fragment)

    plan_dir = paths.get_plan_dir(repo_root)
    plan_dir.mkdir(parents=True, exist_ok=True)
    latest_path = plan_dir / "latest.yaml"
    save_yaml_file(latest_path, plan)
    return plan


def run_apply(repo_root: Path | None = None) -> None:
    repo_root = repo_root or paths.get_device_repo_root()
    context = plugins.build_context(repo_root)
    plan_path = paths.get_plan_dir(repo_root) / "latest.yaml"
    plan_data = load_yaml_file(plan_path)
    if not plan_data:
        print("No plan to apply.")
        return

    # dispatch actions by plugin name
    config_plugins = {definition.name: plugin for definition, plugin in plugins.load_config_plugins(context)}
    execution_log: List[Dict[str, object]] = []
    for plugin_name, actions in plan_data.items():
        plugin = config_plugins.get(plugin_name)
        if not plugin:
            continue
        plugin.apply(actions, context)
        execution_log.append({"plugin": plugin_name, "actions": actions})

    # store execution summary in logs index
    index_path = paths.get_logs_current_dir(repo_root) / "index.yaml"
    index_data = load_yaml_file(index_path)
    existing_log = index_data.get("plan_execution", []) if index_data else []
    existing_log.extend(execution_log)
    index_data["plan_execution"] = existing_log
    save_yaml_file(index_path, index_data)


def run_status(repo_root: Path | None = None) -> Dict:
    repo_root = repo_root or paths.get_device_repo_root()
    status: Dict[str, object] = {}
    for fragment_file in paths.get_state_dir(repo_root).glob("*.yaml"):
        fragment_name = fragment_file.stem
        desired = load_yaml_file(fragment_file)
        live_path = paths.get_live_dir(repo_root) / fragment_file.name
        live = load_yaml_file(live_path)
        status[fragment_name] = desired != live
    for name, drift in status.items():
        print(f"{name}: {'drift' if drift else 'in sync'}")
    return status


def run_logs(repo_root: Path | None = None) -> Dict:
    repo_root = repo_root or paths.get_device_repo_root()
    index_path = paths.get_logs_current_dir(repo_root) / "index.yaml"
    data = load_yaml_file(index_path)
    if not data:
        print(f"No logs found at {index_path}")
    else:
        if utils._yaml_module():
            print(utils._yaml_module().safe_dump(data, sort_keys=False))
        else:
            print(json.dumps(data, indent=2))
    return data or {}


def run_pull(repo_root: Path | None = None) -> Tuple[bool, str]:
    """Pull changes from remote repository (fast-forward only).
    
    Returns:
        Tuple of (success, message)
    """
    repo_root = repo_root or paths.get_device_repo_root()
    
    if not (repo_root / ".git").exists():
        return False, "Not a git repository"
    
    success, output = utils.git_pull(repo_root)
    if success:
        print("Successfully pulled from remote")
        return True, output
    else:
        print(f"Pull failed: {output}")
        return False, output


def run_push(repo_root: Path | None = None) -> Tuple[bool, str]:
    """Push changes to remote repository.
    
    Returns:
        Tuple of (success, message)
    """
    repo_root = repo_root or paths.get_device_repo_root()
    
    if not (repo_root / ".git").exists():
        return False, "Not a git repository"
    
    success, output = utils.git_push(repo_root)
    if success:
        print("Successfully pushed to remote")
        return True, output
    else:
        print(f"Push failed: {output}")
        return False, output


def setup_github_remote(user: str, token: str, repo_name: str, 
                       repo_root: Path | None = None) -> Tuple[bool, str]:
    """Setup GitHub remote for the twin repository.
    
    Args:
        user: GitHub username
        token: GitHub personal access token
        repo_name: Name for the device repository
        repo_root: Path to twin repository
        
    Returns:
        Tuple of (success, message)
    """
    repo_root = repo_root or paths.get_device_repo_root()
    
    # Save credentials to config
    config_module.set_github_credentials(user, token, repo_name, repo_root)
    
    # Create or verify GitHub repository
    import subprocess
    import json as json_module
    
    api_url = "https://api.github.com/user/repos"
    payload = json_module.dumps({"name": repo_name, "private": True})
    
    try:
        result = subprocess.run(
            ["curl", "-s", "-u", f"{user}:{token}", api_url, "-d", payload],
            capture_output=True,
            text=True,
            check=False,
        )
        
        # GitHub returns 201 for created, 422 if already exists
        # Both are acceptable
        
    except Exception as e:
        return False, f"Failed to create/verify GitHub repo: {e}"
    
    # Add remote to git
    remote_url = f"https://{user}:{token}@github.com/{user}/{repo_name}.git"
    if not utils.git_remote_add(repo_root, "origin", remote_url):
        return False, "Failed to add git remote"
    
    utils.git_set_branch(repo_root, "main")
    
    # Try initial push
    success, output = utils.git_push(repo_root)
    if success:
        return True, f"GitHub remote configured: https://github.com/{user}/{repo_name}"
    else:
        return True, f"GitHub remote added (push may be needed): https://github.com/{user}/{repo_name}"


def get_git_history(repo_root: Path | None = None, limit: int = 20) -> List[Dict[str, str]]:
    """Get git commit history.
    
    Returns:
        List of commits with hash, date, and message
    """
    repo_root = repo_root or paths.get_device_repo_root()
    return utils.git_log(repo_root, limit)


def reset_to_commit(commit_hash: str, repo_root: Path | None = None) -> bool:
    """Reset repository to a specific commit (time machine).
    
    Args:
        commit_hash: Git commit hash to reset to
        repo_root: Path to twin repository
        
    Returns:
        True if successful
    """
    repo_root = repo_root or paths.get_device_repo_root()
    
    if utils.git_reset_hard(repo_root, commit_hash):
        print(f"Repository reset to commit {commit_hash}")
        print("You can now plan and apply to bring the system to this state")
        return True
    else:
        print(f"Failed to reset to commit {commit_hash}")
        return False


def check_system_dependencies() -> Dict[str, bool]:
    """Check if required system dependencies are installed."""
    return utils.check_dependencies(["git", "whiptail", "dpkg-query", "systemctl", "crontab"])


def get_config_display(repo_root: Path | None = None) -> str:
    """Get a human-readable config display.
    
    Returns:
        Formatted configuration string
    """
    config = config_module.load_config(repo_root)
    
    lines = []
    lines.append("TwinSync++ Configuration")
    lines.append("=" * 50)
    lines.append(f"Twin Repository: {config.get('twin_repo', 'Not set')}")
    lines.append(f"\nFilesystem Roots:")
    for root in config.get('filesystem_roots', []):
        lines.append(f"  - {root}")
    
    github = config.get('github', {})
    lines.append(f"\nGitHub Integration:")
    lines.append(f"  User: {github.get('user', 'Not configured')}")
    lines.append(f"  Device Repo: {github.get('device_repo', 'Not configured')}")
    lines.append(f"  Token: {'***' if github.get('token') else 'Not set'}")
    
    lines.append(f"\nEnabled Plugins:")
    for plugin in config.get('plugins', {}).get('enable', []):
        lines.append(f"  - {plugin}")
    
    return "\n".join(lines)
