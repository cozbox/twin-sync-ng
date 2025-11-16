# TwinSync

Linux-only **digital twin** tool for your machines.

TwinSync snapshots your system’s config, packages, services, startup and logs into a local Git repo (the **twin**).  
That twin can optionally be pushed to a private GitHub repo so humans or AI can inspect, edit and propose fixes.  
TwinSync then shows a clear plan before safely applying those changes back to the real machine.

## What it does (v0.3)

- **Local Git twin per device**
  - One twin repo on each machine (local Git).
  - Optional private GitHub repo per device (auto-created + remembered).

- **Collector**
  - System info: OS, kernel, packages (`dpkg`), services (systemd), logs.
  - Filesystem config snapshot:
    - `/etc`
    - `~/.config`
    - (text-ish files under 1 MB)
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

Running:

```bash
./twinsync
