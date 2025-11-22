# TwinSync++

Linux-only **digital twin** tool for your machines.

TwinSync++ snapshots your system's config, packages, services, startup and logs into a local Git repo (the **twin**).
That twin can optionally be pushed to a private GitHub repo so humans or AI can inspect, edit and propose fixes.
TwinSync++ then shows a clear plan before safely applying those changes back to the real machine.

## 🎉 Pure Python Implementation

**Complete Python implementation with zero placeholders!** All features are fully implemented and working.

### Quick Start

```bash
# Clone the repository
git clone https://github.com/cozbox/twin-sync-ng.git
cd twin-sync-ng

# Install with pip (development mode)
pip install -e .

# Now you can use the 'twin' command anywhere
twin --help
twin init
twin snapshot
twin menu  # Interactive whiptail menus
```

### Alternative: Run without installation

```bash
# Clone and run directly
git clone https://github.com/cozbox/twin-sync-ng.git
cd twin-sync-ng
python3 -m twin_core.cli --help
python3 -m twin_core.cli menu
```

### Features
- ✅ Complete plugin system (collectors, planners, appliers)
- ✅ Interactive whiptail menus
- ✅ 15+ command-line subcommands
- ✅ GitHub integration with repo creation
- ✅ Git operations (commit, push, pull, time machine)
- ✅ Safety features (backups, permissions, confirmations)
- ✅ Zero placeholders - everything works out of the box!

## TwinSync++ Architecture

TwinSync++ standardizes the repo layout around `state/`, `live/`, `logs/`, `plan/`, `plugins/`, and `schema/`, uses a modular plugin system, and provides the `twin` CLI (`init`, `snapshot`, `plan`, `apply`, `status`, `logs`).
See [`TWIN_SYNC_PLUS_SPEC.md`](TWIN_SYNC_PLUS_SPEC.md) for the full target design, including plugin metadata, YAML data models, and Home Assistant/logging support.

## What TwinSync++ Does

- **Local Git twin per device**
  - One twin repo on each machine (local Git).
  - Optional private GitHub repo per device (auto-created + remembered).

- **Collector**
  - System info: OS, kernel, packages (`dpkg`), services (systemd), logs.
  - Filesystem config snapshot:
    - Defaults: `/etc`, `~/.config`.
    - Menu-driven picker lets you add/remove directories to mirror.
    - Copies text-ish files under 1 MB so the twin stays manageable.
  - Startup info:
    - User crontab (via `crontab -l`).

- **Planner + Applier**
  - **Files**
    - Compare `twin/filesystem/...` vs real files.
    - Plan and apply CREATE / REPLACE actions with backups.
  - **Packages (apt, Debian/Ubuntu)**
    - Compare twin's `system/packages/dpkg.txt` vs live `dpkg-query`.
    - Plan and apply INSTALL / REMOVE via `apt-get`.
  - **Services (systemd)**
    - Twin stores `system/services/desired-state.txt` (service, enabled, running).
    - Plan and apply ENABLE / DISABLE / START / STOP via `systemctl`.
  - **Startup (user crontab)**
    - Twin stores `system/startup/user-crontab.txt`.
    - Plan and apply replacement of the user's crontab from the twin.

- **Time Machine**
  - Uses `git log` on the twin repo.
  - Lets you pick an old snapshot and **reset the twin repo** to that commit.
  - After that you can plan/apply again to bring the system back towards that snapshot.

## Interactive Menu

Running `twin` or `twin menu` launches a whiptail menu:

- **Setup**
  - Init / configure local Twin repo
  - Configure filesystem roots to mirror
  - Link or create GitHub device repo
  - Install / check dependencies (Debian/Ubuntu)
  - Show current TwinSync config
- **Snapshot & sync**
  - Take snapshot (update twin + commit + try push)
  - Pull from remote (refresh twin repo)
- **Plan & apply changes**
  - Generate plan (diff state vs live)
  - Apply plan (execute changes)
  - Show status (check drift)
- **Time Machine / history**
  - Navigate git history and reset to previous snapshots

You can exit from any submenu back up to the main screen. The CLI also has direct subcommands (see `twin --help`).

## Installation & Usage

### Prerequisites

On a Debian/Ubuntu-ish system:

```bash
sudo apt update
sudo apt install -y git whiptail python3 python3-pip
```

### Install TwinSync++

```bash
# Clone the repository
git clone https://github.com/cozbox/twin-sync-ng.git
cd twin-sync-ng

# Install with pip (adds 'twin' command to PATH)
pip install -e .
```

### First-time Setup

```bash
# Launch interactive menu
twin

# Or use direct commands
twin init                  # Initialize twin repository
twin config-fs             # Configure filesystem roots
twin setup-github          # Setup GitHub integration
twin check-deps            # Verify dependencies
```

### Daily Usage

```bash
# Take a snapshot of current system state
twin snapshot

# Pull changes from GitHub
twin pull

# Generate a plan showing what would change
twin plan

# Review and apply the plan
twin apply

# Check drift status
twin status

# Navigate history (time machine)
twin time-machine
```

## Reference docs

- [`TWIN_SYNC_SPEC.md`](TWIN_SYNC_SPEC.md) — architecture, components, data layout.
- [`TWIN_SYNC_PLUS_SPEC.md`](TWIN_SYNC_PLUS_SPEC.md) — TwinSync++ design and specifications.
- [`PYTHON_IMPLEMENTATION.md`](PYTHON_IMPLEMENTATION.md) — Complete Python implementation documentation.
- [`HANDOFF.md`](HANDOFF.md) — how to collaborate on TwinSync development.

TwinSync++ exists to give a controllable, inspectable, shareable Git twin of a device so AI/humans can fix and reproduce systems — with clear plans and final approval before anything real changes.
