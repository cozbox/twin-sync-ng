"""Core helpers for the TwinSync++ engine."""
from __future__ import annotations

import datetime
import importlib
import json
import shutil
from pathlib import Path
from typing import Dict, List

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


def init_twin_repo() -> Path:
    repo_root = paths.ensure_repo_layout()

    # copy schemas and plugin definitions into the repo
    schema_dest = paths.get_schema_dir(repo_root)
    for schema_file in _schema_root().glob("*.json"):
        shutil.copy(schema_file, schema_dest / schema_file.name)

    plugin_dest = paths.get_plugins_dir(repo_root)
    package_plugins = Path(__file__).parent / "plugins_definitions"
    for plugin_dir in package_plugins.iterdir():
        dest = plugin_dest / plugin_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(plugin_dir, dest)

    # ensure config exists
    config_module.save_config(config_module.DEFAULT_CONFIG, repo_root)

    run_snapshot(repo_root)

    # seed state/ with the first live snapshot
    live_dir = paths.get_live_dir(repo_root)
    state_dir = paths.get_state_dir(repo_root)
    for yaml_file in live_dir.glob("*.yaml"):
        shutil.copy(yaml_file, state_dir / yaml_file.name)

    return repo_root


def run_snapshot(repo_root: Path | None = None) -> None:
    repo_root = repo_root or paths.get_device_repo_root()
    paths.ensure_repo_layout(repo_root)
    context = plugins.build_context(repo_root)

    # rotate logs/current if it already contains data
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

    # Config plugins
    for definition, plugin in plugins.load_config_plugins(context):
        fragment_names = definition.provides.get("state_fragments", [])
        fragment_payload = plugin.dump_state(context) or {}
        for fragment in fragment_names:
            fragment_data = fragment_payload.get(fragment, {})
            output_path = live_dir / f"{fragment}.yaml"
            save_yaml_file(output_path, {fragment: fragment_data})

    # Log plugins build index
    index: Dict[str, object] = {}
    for definition, plugin in plugins.load_logs_plugins(context):
        fragment_payload = plugin.dump_logs(context) or {}
        index.update(fragment_payload)

    if index:
        index_path = current_logs / "index.yaml"
        save_yaml_file(index_path, index)


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
