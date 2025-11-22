# TwinSync

Linux-only **digital twin** tool for your machines.

TwinSync snapshots your system’s config, packages, services, startup and logs into a local Git repo (the **twin**).
That twin can optionally be pushed to a private GitHub repo so humans or AI can inspect, edit and propose fixes.
TwinSync then shows a clear plan before safely applying those changes back to the real machine.

## TwinSync++ direction

The next major iteration ("TwinSync++") standardizes the repo layout around `state/`, `live/`, `logs/`, `plan/`, `plugins/`, and `schema/`, moves to a modular plugin system, and introduces a new `twin` CLI (`init`, `snapshot`, `plan`, `apply`, `status`, `logs`).
See [`TWIN_SYNC_PLUS_SPEC.md`](TWIN_SYNC_PLUS_SPEC.md) for the full target design, including plugin metadata, YAML data models, and Home Assistant/logging support.

## What it does (v0.3)

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
    - Compare twin’s `system/packages/dpkg.txt` vs live `dpkg-query`.
    - Plan and apply INSTALL / REMOVE via `apt-get`.
  - **Services (systemd)**
    - Twin stores `system/services/desired-state.txt` (service, enabled, running).
    - Plan and apply ENABLE / DISABLE / START / STOP via `systemctl`.
  - **Startup (user crontab)**
    - Twin stores `system/startup/user-crontab.txt`.
    - Plan and apply replacement of the user’s crontab from the twin.

- **Time Machine**
  - Uses `git log` on the twin repo.
  - Lets you pick an old snapshot and **reset the twin repo** to that commit.
  - After that you can plan/apply again to bring the system back towards that snapshot.

## Menu layout

Running `./twinsync` launches a whiptail menu that starts simple and then branches cleanly:

- **Setup**
  - Init / configure local Twin repo
  - Configure filesystem roots to mirror
  - Link or create GitHub device repo
  - Install / check dependencies (Debian/Ubuntu)
  - Update TwinSync program (respects tracked remote/branch, logs fetch/pull to `/tmp/twinsync-update.log`)
  - Show current TwinSync config
- **Snapshot & sync**
  - Take snapshot (update twin + commit + try push)
  - Pull from remote (refresh twin repo)
- **Plan & apply changes**
  - Files (plan/apply)
  - Packages (plan/apply)
  - Services (plan/apply)
  - Startup (plan/apply)
- **Time Machine / history**

You can exit from any submenu back up to the main screen. The CLI also has subcommands (see `./twinsync --help`).

## Quick start

On a Debian/Ubuntu-ish system:


- **Setup**
  - Init / configure local Twin repo
  - Configure filesystem roots to mirror
  - Link or create GitHub device repo
  - Install / check dependencies (Debian/Ubuntu)
  - Update TwinSync program (git pull with remote/branch detection + log)
  - Show current TwinSync config
- **Snapshot & sync**
  - Take snapshot (update twin + commit + try push)
  - Pull from remote (refresh twin repo)
- **Plan & apply changes**
  - Files (plan/apply)
  - Packages (plan/apply)
  - Services (plan/apply)
  - Startup (plan/apply)
- **Time Machine / history**

You can exit from any submenu back up to the main screen. The CLI also has subcommands (see `./twinsync --help`).

## Quick start

On a Debian/Ubuntu-ish system:

Running `./twinsync` launches a whiptail menu that keeps the top level tidy and then fans out:

- Setup / utilities
  - Init / configure local Twin repo (create local Git)
  - GitHub setup (remember username/token + per-device repo)
  - Install/check dependencies (Debian/Ubuntu)
  - Configure filesystem roots (directories to mirror)
  - Show current TwinSync config
- Snapshot / sync
  - Take snapshot (update twin + commit + optional push)
  - Pull from remote (update twin repo)
- Files (plan/apply)
  - Plan file changes (twin -> system)
  - Apply file changes (twin -> system)
- Packages (plan/apply)
  - Plan package changes (apt, twin -> system)
  - Apply package changes (apt, twin -> system)
- Services (plan/apply)
  - Plan service changes (systemd, twin -> system)
  - Apply service changes (systemd, twin -> system)
- Startup (plan/apply)
  - Plan startup changes (user crontab)
  - Apply startup changes (user crontab)
- Time Machine / history

You can exit from any submenu back up to the main screen. The CLI also has subcommands (see `./twinsync --help`).

## Quick start

On a Debian/Ubuntu-ish system:

```bash
sudo apt update
sudo apt install -y git whiptail curl

git clone https://github.com/niyisurvey/twin-sync.git
cd twin-sync
chmod +x twinsync
./twinsync
```

Then:

1. Go to **Setup / utilities → Init / configure local Twin repo**.
2. Optionally let it create/link a private GitHub repo and remember your credentials.
3. Take a snapshot.
4. Share the GitHub repo with humans / AI.
5. After changes in the twin, pull, then plan and apply for files/packages/services/startup.

## Reference docs

- [`TWIN_SYNC_SPEC.md`](TWIN_SYNC_SPEC.md) — architecture, components, data layout.
- [`HANDOFF.md`](HANDOFF.md) — how to collaborate with Hassy on TwinSync development.

TwinSync exists to give a controllable, inspectable, shareable Git twin of a device so AI/humans can fix and reproduce systems — with clear plans and final approval before anything real changes.
