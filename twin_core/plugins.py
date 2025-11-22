"""Plugin registry and helpers."""
from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from . import config as config_module
from . import paths
from . import utils


@dataclass
class PluginDefinition:
    name: str
    kind: str  # "config" or "logs"
    provides: Dict
    dependencies: List[str]
    entrypoint: str
    definition_path: Path


@dataclass
class TwinContext:
    repo_root: Path
    config: Dict


def _load_single_plugin(def_path: Path) -> PluginDefinition:
    data = utils.load_yaml(def_path / "plugin.yaml")
    return PluginDefinition(
        name=data.get("name", def_path.name),
        kind=data.get("kind", "config"),
        provides=data.get("provides", {}),
        dependencies=data.get("dependencies", []) or [],
        entrypoint=data.get("entrypoint", ""),
        definition_path=def_path,
    )


def load_plugin_definitions(base_dir: Path | None = None) -> Dict[str, PluginDefinition]:
    base_dir = base_dir or (Path(__file__).parent / "plugins_definitions")
    definitions: Dict[str, PluginDefinition] = {}
    for child in base_dir.iterdir():
        if child.is_dir() and (child / "plugin.yaml").exists():
            definition = _load_single_plugin(child)
            definitions[definition.name] = definition
    return definitions


def _instantiate(definition: PluginDefinition):
    if not definition.entrypoint:
        return None
    module_path, class_name = definition.entrypoint.split(":", 1)
    module = importlib.import_module(module_path)
    plugin_cls = getattr(module, class_name)
    return plugin_cls()


def _is_enabled(definition: PluginDefinition, config: Dict) -> bool:
    enabled = config.get("plugins", {}).get("enable", [])
    return definition.name in enabled


def load_config_plugins(context: TwinContext) -> List:
    definitions = load_plugin_definitions()
    plugins = []
    for definition in definitions.values():
        if definition.kind != "config":
            continue
        if not _is_enabled(definition, context.config):
            continue
        instance = _instantiate(definition)
        if instance is None:
            continue
        detect_fn = getattr(instance, "detect", None)
        if detect_fn and not detect_fn(context):
            continue
        plugins.append((definition, instance))
    return plugins


def load_logs_plugins(context: TwinContext) -> List:
    definitions = load_plugin_definitions()
    plugins = []
    for definition in definitions.values():
        if definition.kind != "logs":
            continue
        if not _is_enabled(definition, context.config):
            continue
        instance = _instantiate(definition)
        if instance is None:
            continue
        detect_fn = getattr(instance, "detect", None)
        if detect_fn and not detect_fn(context):
            continue
        plugins.append((definition, instance))
    return plugins


def build_context(repo_root: Path | None = None) -> TwinContext:
    repo_root = repo_root or paths.get_device_repo_root()
    config = config_module.load_config(repo_root)
    return TwinContext(repo_root=repo_root, config=config)
