# TwinSync – Linux Digital Twin Tool (Spec v1)

## 1. Overview

I want **TwinSync** to be a **Linux-only** tool that:

- Creates and maintains a **digital twin** of a machine in a **Git repo**.
- Always creates **local Git snapshots** first.
- Can optionally sync that twin to a **private GitHub repo** for sharing, troubleshooting, and reproduction.
- Lets me **review and approve a plan** before any changes are applied back to the machine.

TwinSync has four main pieces:

- **Collector** – reads the real system and updates the twin.
- **Planner** – compares twin vs real system and builds a plan.
- **Applier** – executes an approved plan on the real system.
- **TUI (menu-based)** – the main user interface, menu-driven.

---

## 2. Platforms and Scope

- Target: **Linux only**.
- Initial focus: systemd-based distros (e.g. Debian/Ubuntu).
- Everything TwinSync does must be compatible with normal Linux tools (git, systemd, package manager, cron, etc.).

---

## 3. Digital Twin Model

Each machine has a **Twin repo**:

- A **local Git repository** on the machine’s filesystem.
- Optionally synced to a **remote GitHub repo** (private, one repo per machine).

TwinSync stores:

- **Filesystem state** (selected config/script files).
- **System state** (OS info, packages, services, startup, etc.).
- **History** via Git commits (snapshots over time).

### 3.1 Repo layout

Inside the twin repo:

- `filesystem/`  
  - Contains copies of real files TwinSync manages, mirrored by path.
  - Examples: `/etc/...`, selected `~/.config/...`, important dotfiles and scripts.

- `system/`  
  - `os.json` – distro + version + kernel.  
  - `hardware.json` – CPU/RAM/disk summary.  
  - `packages/` – package list from system package manager (e.g. `apt.json`).  
  - `services/` – systemd units and their states (enabled/disabled/running).  
  - `startup/` – boot/startup config:
    - systemd services/timers enabled at boot  
    - cron `@reboot` jobs  
    - `rc.local` presence  
    - user autostart entries under `~/.config/autostart`
  - `network/` (basic info, e.g. hostname, core interfaces).  
  - `processes/` (snapshot of top processes).  
  - `logs/` – truncated snippets of key logs (last N lines).

- `plans/`  
  - Structured “desired change” files (e.g. YAML) created/edited by humans/AI.

- `scripts/`  
  - Scripts TwinSync can run as part of a plan, **only if I approve**.

- `.git/`  
  - Local Git history of all snapshots.

---

## 4. Local vs GitHub

### 4.1 Local snapshots

Every snapshot is always:

1. Collector updates `filesystem/`, `system/`, etc.  
2. Git commit in the local twin repo (e.g. `TwinSync snapshot 2025-11-16T12:34Z`).

This works even if there is no GitHub remote or the network is down.

### 4.2 GitHub sync

If a GitHub remote is configured:

- After committing locally, TwinSync **tries to push** to GitHub.
- If push succeeds:
  - The twin and its history now also live in the remote private repo.
- If push fails:
  - The snapshot still exists locally.
  - TwinSync should clearly report that it could not sync to GitHub.

**Design rule:**  
- The **digital twin lives in Git** (local).  
- GitHub is a **remote mirror** of that twin, not the only copy.

---

## 5. Architecture: Collector, Planner, Applier, TUI

### 5.1 Collector

Purpose: **read the real Linux system and update the twin repo.**

The collector:

- Reads:
  - OS and hardware info.
  - Installed packages via distro package manager (e.g. `dpkg`/`apt` for Debian/Ubuntu).
  - systemd services + states.
  - startup mechanisms (systemd boot units, cron `@reboot`, rc.local, user autostart).
  - Selected filesystem paths (`/etc`, `~/.config`, chosen app dirs).
  - Truncated logs from `journalctl` and/or `/var/log/...`.

- Writes:
  - `system/os.json`, `system/hardware.json`, `system/packages/...`, `system/services/...`, `system/startup/...`, `system/network/...`, `system/processes/...`, `system/logs/...`.
  - Mirrors selected real files into `filesystem/` with their relative paths.

- Then:
  - Stages and commits changes in the local Git repo.

The collector **never** applies changes to the system; it only reads and writes the twin.

---

### 5.2 Planner

Purpose: **compare twin vs real system and build a neutral plan.**

Inputs:

- Current **twin state** from the repo (`filesystem/`, `system/`, `plans/`).
- Current **live system state** (freshly collected or re-read).
- Any explicit instructions from `plans/*.yaml`.

Output:

- A **plan object** with actions grouped by type, e.g.:

  - Files:
    - `replace /etc/app/config.yml from filesystem/etc/app/config.yml`
  - Packages:
    - `install nginx`
    - `remove apache2`
  - Services:
    - `enable_and_restart nginx`
    - `disable some-old-service`
  - Startup:
    - `add cron @reboot job X`
    - `disable systemd unit Y`
  - Commands/scripts:
    - `run systemctl daemon-reload`
    - `run scripts/fix-perms.sh`

The planner:

- Does not execute anything.
- Outputs a structured plan that the TUI can display and the Applier can follow.

---

### 5.3 Applier

Purpose: **execute an approved plan on the Linux system.**

Inputs:

- A **plan** that has already been shown to the user and approved.

Responsibilities:

- Apply file changes:
  - Replace/create/delete files as specified.
  - Optionally create backups before overwriting critical files.

- Apply package changes:
  - Use distro package manager to install/remove packages.

- Apply service changes:
  - Use `systemctl` to enable/disable/start/stop/restart services as specified.

- Apply startup changes:
  - Update systemd units, cron, rc.local, and user autostart entries.

- Run commands/scripts:
  - Execute specified commands or scripts from `scripts/` in a controlled way.

The applier:

- Never decides what to do; it only carries out the already-defined plan.
- Reports results (success/failure) back so the TUI can display them.

---

### 5.4 TUI (menu-based control panel)

Purpose: **main user interface**, menu-driven.

Behaviour:

- Running `twinsync` **with no arguments** launches a TUI main menu.

Example main menu:

- Init / GitHub linking
- Push snapshot
- Pull & apply changes
- History & Time Machine
- Settings (paths, ignore rules, GitHub)
- Exit

Each menu item is a flow:

#### Init / GitHub linking

- Configure or test local twin repo location.
- Configure GitHub access (token, device repo name).
- Create or link a private GitHub repo.
- Optionally take a first snapshot and push it.

#### Push snapshot

- Show what will be collected.
- Confirm.
- Call Collector to update twin and create a local commit.
- If GitHub is configured, push to remote.
- Show snapshot ID / commit hash and push status.

#### Pull & apply changes

- If GitHub is configured, pull latest from remote to local twin repo.
- Refresh live system state if needed.
- Call Planner to build a plan.
- Show the plan in nested TUI screens:
  - Summary by category (files, packages, services, startup, commands).
  - Ability to inspect detailed changes (e.g. per-file).
- Final confirmation dialog:
  - “Apply these changes? Yes / No”
- If “Yes”:
  - (Optionally auto-checkpoint current state first.)
  - Call Applier.
  - Show per-step results.

#### History & Time Machine

- List git snapshots (commits) with timestamps + messages/labels.
- For a selected snapshot:
  - Show summary of what changed in that snapshot.
  - Option: “Plan revert to this snapshot”:
    - Use Planner to build a revert plan.
    - Show it and ask for confirmation.
    - If approved, call Applier.

TwinSync can also expose CLI subcommands (`twinsync push`, `twinsync pull`, etc.) for advanced users or automation, but the **primary UX is the TUI control panel**.

---

## 6. Safety and Defaults

TwinSync should:

- Focus on **config, state & structure**, not user documents/media.
- Use sane default include paths (`/etc`, `~/.config`, specific app directories).
- Use default ignore rules (e.g. avoid huge directories like `node_modules`, `.cache`, etc.).
- Limit file size and log length by default.
- Always show a plan and get explicit confirmation before applying changes.
