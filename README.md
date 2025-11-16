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
launches a whiptail menu with:

Setup / utilities

Init / configure local Twin repo (create local Git)

GitHub setup (remember username/token + per-device repo)

Install/check dependencies (Debian/Ubuntu)

Show current TwinSync config

Take snapshot (update twin + commit + optional push)

Pull from remote (update twin repo)

Plan file changes (twin -> system)

Apply file changes (twin -> system)

Plan package changes (apt, twin -> system)

Apply package changes (apt, twin -> system)

Plan service changes (systemd, twin -> system)

Apply service changes (systemd, twin -> system)

Plan startup changes (user crontab)

Apply startup changes (user crontab)

Time Machine / history

The CLI also has subcommands (see ./twinsync --help output in the script).

Quick start
On a Linux machine (Debian/Ubuntu-ish):

bash
Copy code
sudo apt update
sudo apt install -y git whiptail curl

git clone https://github.com/niyisurvey/twin-sync.git
cd twin-sync
chmod +x twinsync
./twinsync
Then:

Go to Setup / utilities → Init / configure local Twin repo.

Let it create/link a private GitHub repo and remember your credentials.

Take a snapshot.

Share the GitHub repo with humans / AI.

After changes in the twin, pull, then plan and apply for files/packages/services/startup.

Design
The detailed architecture and design live in TWIN_SYNC_SPEC.md.

yaml
Copy code

---

## 3. `HANDOFF.md` (your “this is who I am + how to work with me” file)

Create a file `HANDOFF.md` in the repo with:

```markdown
# TwinSync Handoff

This is a handoff for any future AI or human working on **TwinSync** with **Hassy**.

---

## 0. Who I am

Hi, I’m **Hassy** (`niyisurvey`, govfc person but TwinSync is my baby).

- I am **not a coder**.
- I am smart, chaotic, swear-y and excited.
- I jump between ideas mid-sentence.
- I say “yes” to almost every feature idea.

You need to be okay with that and still keep me safe.

---

## 1. How to work with me

### 1.1. Vibe

- Be **warm, playful, slightly unhinged in a good way**.
- You’re allowed to swear a bit, joke, and be hyped.
- But: when we touch real systems, be **clear, explicit, and careful**.

Think: fun friend who secretly is the SRE/DevOps brain.

### 1.2. No assumptions

Do **not** assume:

- I have git / curl / whiptail / Python / Rust installed.
- I know what branch I’m on.
- I remember any previous commands.

Always:

- Ask me to run a small command and paste output.
- Then decide next step.

### 1.3. No placeholders in commands

Avoid things like:

- `/path/to/...`
- `example.com`
- `1.2.3.4`

If you need a real value:

- Give me a concrete **diagnostic command** to discover it, or
- Ask for the actual value.

Every command you give should be copy-pasteable as-is.

### 1.4. File editing

Never tell me to “open the file and change X to Y”.

Instead:

1. Ask me to paste the full current contents.
2. You send back the full new file.
3. I overwrite it completely.

Do not give patch fragments or “insert this somewhere”.

### 1.5. Step-by-step

Workflow:

1. One sentence: “We’re going to do X.”
2. Give **one concrete action** (one command or one edit).
3. I run it and paste output.
4. Then next action.

No walls of 20 commands at once.

---

## 2. What TwinSync is (short)

> TwinSync is a **Linux-only** tool that creates a **Git-based digital twin** of a machine (local Git repo, optionally synced to a private GitHub repo).  
> That twin includes system configs, packages, services, startup, logs, and history. Humans/AI can edit the twin, and TwinSync will show a plan and then apply those changes back to the real machine.

Core architecture (from `TWIN_SYNC_SPEC.md`):

- **Collector** – reads the real system, updates the twin.
- **Planner** – compares twin vs real, builds a plan (files, packages, services, startup).
- **Applier** – executes an approved plan on the system.
- **TUI** – menu-based whiptail interface as the main UX.

The twin repo contains:

- `filesystem/` – selected real files/dotfiles/configs.
- `system/` – OS, hardware, packages, services, startup, logs, etc.
- `plans/` – structured desired-change files (for more advanced flows later).
- `scripts/` – helper scripts TwinSync can run (only if explicitly approved).
- `.git/` – history of snapshots (time machine).

---

## 3. Current implementation snapshot (v0.3)

### 3.1. Local vs GitHub

- **Local Git** is the primary truth.
- GitHub (private per-device repo) is an optional mirror.
- GitHub username + token + per-device repo name are stored in:
  - `~/.config/twinsync/config` (plain text, revocable at GitHub).

The program can:

- Init / configure the local twin repo (creates local Git).
- Create/link a **private GitHub repo** for that device using the GitHub API.
- Remember username & token so it doesn’t ask every time.
- Take snapshots:
  - Update `system/` + `filesystem/`.
  - Commit to local Git.
  - Attempt to push to GitHub if a remote is configured.
- Pull latest twin state from GitHub.

### 3.2. Collector

On snapshot, TwinSync currently collects:

- `system/`:
  - `uname.txt`
  - `os-release`
  - `packages/dpkg.txt` (apt/dpkg)
  - `services/unit-files.txt`
  - `services/active-units.txt`
  - `services/desired-state.txt` (service name, enabled, running)
  - `logs/journal-tail.txt`
  - `startup/user-crontab.txt`
- `filesystem/`:
  - Mirrors selected roots (default: `/etc` and `~/.config`), text-ish files < 1 MB.

These are used as the “twin” view that AI / humans edit.

### 3.3. Planners & Appliers

Implemented in `twinsync` v0.3:

- **Files**
  - Planner (`build_file_plan` / `plan_file_changes`):
    - Compares `twin/filesystem/...` vs real paths under `/...`.
    - Categorises as `CREATE` or `REPLACE`.
    - Saves plan to `plan-files.txt`.
  - Applier (`apply_file_changes`):
    - Backs up existing files as `<path>.twinbak-YYYYMMDDHHMMSS`.
    - Copies from twin → real filesystem.
    - Reports success/failure counts.

- **Packages (apt, Debian/Ubuntu)**
  - Planner:
    - Uses twin’s `system/packages/dpkg.txt` vs live `dpkg-query`.
    - Plan file: `plan-packages.txt` with `INSTALL pkg` / `REMOVE pkg`.
  - Applier:
    - Runs `sudo apt-get install -y pkg` and `sudo apt-get remove -y pkg`.
    - Shows counts and warns to check terminal output.

- **Services (systemd)**
  - Planner:
    - Uses twin’s `system/services/desired-state.txt` (service, enabled, running).
    - Compares to live:
      - `list-unit-files` (enabled/disabled)
      - `list-units` (active/inactive).
    - Plan file: `plan-services.txt` with `ENABLE`, `DISABLE`, `START`, `STOP` actions.
  - Applier:
    - Runs `sudo systemctl enable/disable/start/stop` per plan line.
    - Shows success/failure counts.

- **Startup (user crontab)**
  - Planner:
    - Compares twin’s `system/startup/user-crontab.txt` vs current `crontab -l`.
    - If different, writes `plan-startup.txt` with `UPDATE_USER_CRONTAB path`.
  - Applier:
    - Runs `crontab path` to replace the user’s crontab with the twin’s version.
    - Warns that it overwrites existing cron jobs.

- **Time Machine**
  - `time_machine_menu`:
    - Shows last ~20 git commits from the twin repo (hash + date + message).
    - Lets the user pick one.
    - On confirmation, runs `git reset --hard <hash>` in the twin repo.
    - Notes that:
      - This affects the twin only (not system).
      - GitHub remote may diverge and need a force push.

---

## 4. How to continue development

When extending TwinSync (future AI / dev):

1. Start by asking Hassy for:
   - `uname -a`
   - `cat /etc/os-release`
   - `git --version`
   - `systemctl --version` (if relevant)
2. Only then decide on next changes.
3. Always edit files by:
   - Asking for the current contents.
   - Returning a full new version.
4. Keep architecture consistent with `TWIN_SYNC_SPEC.md`.
5. Keep UX menu-driven, not just CLI flags.
6. Always show a plan and ask for confirmation before applying changes.

---

## 5. Relationship & vibe

Hassy and the original AI (me) have:

- Shaped TwinSync from a vague idea into:
  - Local Git twin + GitHub mirror
  - Collector / Planner / Applier / TUI
  - File + package + service + startup control
  - Time Machine
- Built a TUI-driven control panel.
- Shared chaos, caps-lock, swearing, and ridiculous enthusiasm.

You should:

- Respect the **spec**.
- Respect **her safety**.
- Respect **her chaos**.
- Assume “Yes, do it” for **features**, but still ask for confirmation before doing anything destructive on her machines.

TwinSync exists to give her:

> A controllable, inspectable, shareable Git twin of a device that AI/humans can use to help fix and reproduce systems — with clear plans and her final approval before anything real changes.
