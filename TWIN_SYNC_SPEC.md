# TwinSync Specification

## 1. Purpose
TwinSync creates a Git-based **digital twin** of a Linux device so humans or AI assistants can inspect, edit, and apply system changes safely. The twin lives locally (primary source of truth) and can optionally be mirrored to a private GitHub repo.

## 2. High-level architecture
TwinSync is a Bash program (`./twinsync`) with four pillars:

1. **Collector** – snapshots the live system into the twin repo.
2. **Planner** – compares the twin vs live system and writes plan files.
3. **Applier** – executes plan files (only after explicit confirmation).
4. **TUI** – a whiptail-driven control panel that orchestrates everything.

## 3. Data layout of a twin repo
```
<twin repo>/
├── filesystem/          # mirrored real files (e.g. /etc, ~/.config)
├── system/
│   ├── uname.txt        # `uname -a`
│   ├── os-release       # `/etc/os-release`
│   ├── packages/
│   │   └── dpkg.txt     # `dpkg-query -W`
│   ├── services/
│   │   ├── unit-files.txt     # `systemctl list-unit-files`
│   │   ├── active-units.txt   # `systemctl list-units`
│   │   └── desired-state.txt  # service, enabled, running
│   ├── logs/journal-tail.txt  # `journalctl -n 200`
│   └── startup/user-crontab.txt # `crontab -l`
├── plan-files.txt
├── plan-packages.txt
├── plan-services.txt
└── plan-startup.txt
```

Additional plans or metadata can be stored under `plans/` or other files as the tool grows.

## 4. Collector details
- **System info**
  - `uname -a` → `system/uname.txt`
  - `/etc/os-release` → `system/os-release`
  - `dpkg-query -W -f='${Package} ${Version}\n'` → `system/packages/dpkg.txt`
  - `systemctl list-unit-files` and `systemctl list-units` → `system/services/*.txt`
  - Derived `desired-state.txt` merges enablement + runtime state per service.
  - `journalctl -n 200 --no-pager` → `system/logs/journal-tail.txt`.
  - `crontab -l` → `system/startup/user-crontab.txt` (if available).
- **Filesystem snapshot**
  - Configurable roots (default `/etc` and `~/.config`).
  - Copies regular files under 1 MB into `filesystem/...` using the same relative paths.
  - Avoids copying `/` wholesale and skips missing roots.

Each snapshot run stages (`git add .`) and commits (`TwinSync snapshot <timestamp>`) inside the twin repo, followed by an optional `git push` if a remote exists.

## 5. Planner logic
Every planner writes a plain-text plan file with one action per line.

### 5.1 Files (`plan-files.txt`)
- Compare every tracked file under `filesystem/` with the corresponding real path.
- Emit `CREATE <sys_path> <twin_file>` if missing on the system.
- Emit `REPLACE <sys_path> <twin_file>` if contents differ.

### 5.2 Packages (`plan-packages.txt`)
- Use desired list from `system/packages/dpkg.txt`.
- Compare with the live `dpkg-query` package list.
- Emit `INSTALL pkg` for packages present in twin but not in system.
- Emit `REMOVE pkg` for packages installed locally but absent from the twin list.

### 5.3 Services (`plan-services.txt`)
- Desired state from `system/services/desired-state.txt`.
- Live enablement from `systemctl list-unit-files`, runtime state from `systemctl list-units`.
- Emit `ENABLE` / `DISABLE` when enablement differs.
- Emit `START` / `STOP` when runtime state differs.

### 5.4 Startup (`plan-startup.txt`)
- Compare `system/startup/user-crontab.txt` vs current `crontab -l` output.
- Emit a single `UPDATE_USER_CRONTAB <path>` action if they differ.

## 6. Applier logic
- **Files** – confirm via whiptail, back up replaced files as `<path>.twinbak-<timestamp>`, then copy from twin to system (creating directories as needed).
- **Packages** – confirm, then run `sudo apt-get install -y` or `sudo apt-get remove -y` per plan entry.
- **Services** – confirm, then run `sudo systemctl enable/disable/start/stop` per plan entry.
- **Startup** – confirm, then run `crontab <desired_file>` for the user.

All appliers count successes/failures and display the summary.

## 7. User interface
- **Whiptail main menu** – setup, snapshot/sync, a dedicated Plan & Apply hub (routes to files/packages/services/startup), and Time Machine.
- **Setup submenu** – init local twin repo, choose filesystem roots, link/create GitHub device repo, install dependencies, update the TwinSync program from GitHub (uses the tracked remote/branch when available, falls back to a detected remote branch, and logs fetch/pull output to `/tmp/twinsync-update.log`), view config.
- **CLI shortcuts** – `./twinsync plan-files`, `./twinsync snapshot`, etc. for advanced use or scripting.

## 8. GitHub integration
- Stores config in `~/.config/twinsync/config` (repo path, GitHub user/token, device repo name, filesystem roots).
- Uses GitHub REST API (via curl) to create a private repo per device and configures `origin` remote.
- Snapshot runs push automatically if a remote exists.

## 9. Time Machine
- Menu lists last ~20 `git log` entries from the twin repo.
- After confirmation, runs `git reset --hard <hash>` to roll the twin back.
- User must manually push/force-push if they mirror to GitHub.

