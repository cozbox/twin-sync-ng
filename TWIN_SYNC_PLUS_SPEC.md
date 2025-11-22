# TwinSync++ Vision

This document captures the target architecture for the next generation of TwinSync. It focuses on a per-machine Git repository, a structured plugin system, and a new `twin` CLI that wraps both configuration and log capture.

## 1. Repository layout
Each device keeps a Git repo (for example `~/twin-sync-device`) with machine-readable YAML/JSON artifacts only—no database. The layout is:

```
twin-sync-device/
  config.yaml

  state/
    packages.yaml
    services.yaml
    files.yaml
    network.yaml
    desktop.yaml
    containers.yaml
    cron.yaml
    home_assistant.yaml
    logs_config.yaml

  live/
    packages.yaml
    services.yaml
    files.yaml
    network.yaml
    desktop.yaml
    containers.yaml
    cron.yaml
    home_assistant.yaml

  logs/
    current/
      index.yaml
      systemd/
        journal_tail.txt
        errors_last_boot.txt
      files/
        syslog_tail.txt
        authlog_tail.txt
        nginx_error_tail.txt
      home_assistant/
        core_tail.txt
        supervisor_tail.txt
        summary.yaml
    2025-11-22T13-00-00Z/
      index.yaml
      systemd/...
      files/...
      home_assistant/...

  plan/
    latest.yaml
    history/
      2025-11-22T13-05-00Z.yaml

  plugins/
    packages.debian/
      plugin.yaml
      schema.yaml
    services.systemd/
      plugin.yaml
      schema.yaml
    files.mirror/
      plugin.yaml
      schema.yaml
    network.networkmanager/
      plugin.yaml
      schema.yaml
    desktop.gnome/
      plugin.yaml
      schema.yaml
    cron.user/
      plugin.yaml
      schema.yaml
    containers.docker/
      plugin.yaml
      schema.yaml
    logs.systemd_journal/
      plugin.yaml
      schema.yaml
    logs.files/
      plugin.yaml
      schema.yaml
    logs.home_assistant/
      plugin.yaml
      schema.yaml
    home_assistant.core/
      plugin.yaml
      schema.yaml

  schema/
    state.schema.json
    live.schema.json
    plan.schema.json
    logs_index.schema.json
```

The legacy `twinsync` Bash script remains at the repo root during migration and eventually becomes a thin wrapper around the new `twin` binary.

## 2. CLI commands
The new `twin` CLI provides:
- `twin init`
- `twin snapshot`
- `twin plan`
- `twin apply`
- `twin status`
- `twin logs`
- `twin config ...`

`init` bootstraps a repo, copies template schemas/plugins, runs an initial snapshot, and commits. Other commands delegate to plugins for state capture, planning, applying, status checks, and log inspection.

## 3. Data models
All artifacts are YAML (or JSON-equivalent) and Git-versioned.

### 3.1 Desired state (`state/`)
- **packages.yaml**: list of packages with source and `ensure` (present/absent).
- **services.yaml**: systemd units with `enabled`/`running` booleans.
- **files.yaml**: metadata for managed files plus `twin_path` pointing to mirrored content under `filesystem/...`.
- **network.yaml**: connection profiles (e.g., NetworkManager) with priorities and autoconnect.
- **desktop.yaml**: desktop backend (GNOME/KDE/etc.) and settings (e.g., `gsettings` keys).
- **containers.yaml**: container backend and service definitions with desired images and running state.
- **cron.yaml**: user cron entries with schedule, command, and enabled flag.
- **home_assistant.yaml**: managed HA config files and addons.
- **logs_config.yaml**: which log sources to collect (systemd journal, log files, Home Assistant) and tailing parameters.

### 3.2 Live state (`live/`)
Mirrors the structure of `state/` but represents observed reality—e.g., installed packages with versions, actual service enablement/runtime, container status, etc.

### 3.3 Log snapshots (`logs/`)
- Raw captures live under `logs/current` (journal tails, file tails, HA logs).
- `logs/current/index.yaml` summarizes counts (errors/warnings, auth failures, HA error stats) and can include plan execution results.
- Older snapshots rotate into timestamped folders.

### 3.4 Plans (`plan/`)
`plan/latest.yaml` holds actions grouped by plugin namespace (e.g., `packages.debian`, `services.systemd`, `files.mirror`, `network.networkmanager`, `desktop.gnome`, `cron.user`, `containers.docker`, `home_assistant.core`). Each action describes operations like install/remove packages, enable/disable services, sync files, create/modify network profiles, apply desktop settings, set crontabs, ensure containers run, or sync HA config.

## 4. Plugin system
Plugins live under `plugins/<name>/` with `plugin.yaml` metadata:

```yaml
name: "packages.debian"
kind: "config" # or "logs"
provides:
  state_fragments:
    - "packages"
dependencies: []
entrypoint: "twin_plugins.packages_debian:DebianPackagesPlugin"
```

Log plugins use `logs_fragments` instead of `state_fragments`. Each plugin has a matching `schema.yaml` describing its fragment.

### 4.1 Interfaces
- **Config plugins** implement `detect()`, `dump_state()`, `plan(desired_fragment, live_fragment)`, and `apply(actions)`.
- **Log plugins** implement `detect()` and `dump_logs(logs_config_fragment)` to write files under `logs/current` and return a summary fragment for `index.yaml`.

### 4.2 Core flows
- **snapshot**: load config, discover plugins, run `dump_state` for config plugins, and `dump_logs` for log plugins (with optional rotation of `logs/current`).
- **plan**: load `state/` and `live/`, call `plan()` per config plugin, and merge into `plan/latest.yaml`.
- **apply**: read `plan/latest.yaml`, prompt/confirm, dispatch actions to plugins, and record execution summaries inside `logs/current/index.yaml`.
- **status**: quick drift summary comparing `state/` vs `live/` per plugin.
- **logs**: human-friendly views/grep over `logs/current` and its index.

## 5. Log plugins
- **logs.systemd_journal**: uses `journalctl` to capture tails and error-only views, counts warnings/errors for the last hour, and notes critical units.
- **logs.files**: tails configured log files (e.g., syslog, auth.log, nginx) with optional parsing of error/auth failures.
- **logs.home_assistant**: tails HA core/supervisor logs (Docker or host), counts errors/warnings, and records last error line and last restart.

## 6. Home Assistant config plugins
- **home_assistant.core**: snapshots HA YAML config files into `filesystem/home-assistant/...`, updates `live/home_assistant.yaml`, plans `sync_config_file` actions when managed files drift, and applies by backing up then copying from the twin mirror.
- **os.home_assistant_os** (optional): talks to Supervisor API to track/install/update addons and HA core, emitting actions like `install_addon` or `update_core`.

## 7. Migration path from current Bash implementation
1. Introduce a `twin/` package with core engine, CLI, schemas, and plugin templates; keep the legacy Bash script as a wrapper.
2. Implement a config loader and plugin registry (scan `plugins/*/plugin.yaml`).
3. Port existing collectors into config plugins: `packages.debian`, `services.systemd`, `cron.user`, `files.mirror`.
4. Add log plugins `logs.systemd_journal` and `logs.files`; include `logs_config.yaml` defaults during `twin init`.
5. Wire CLI commands (`snapshot`, `plan`, `apply`, `status`, `logs`) to the plugin engine.
6. Extend with `network.networkmanager`, `desktop.gnome`, and `containers.docker` plugins.
7. Add Home Assistant plugins (`logs.home_assistant`, `home_assistant.core`, optional `os.home_assistant_os`).
8. Finalize schemas/documentation and describe how to share the twin repo with external AI via GitHub.

## 8. One-paragraph handoff
Take the current `twin-sync` repo and implement the TwinSync++ design above: a per-machine repo with `state/`, `live/`, `logs/`, `plan/`, `plugins/`, `schema/`, and `config.yaml`; a `twin` CLI with init/snapshot/plan/apply/status/logs; a plugin system for config and logs (port existing dpkg/systemd/cron/files collectors); log plugins for systemd journal/files; plugins for network, desktop, containers, and Home Assistant config/logs; Git-only persistence. Keep all YAML/plan formats machine-friendly for future AI editing.
