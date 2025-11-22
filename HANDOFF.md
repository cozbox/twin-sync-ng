# TwinSync Handoff

Hi, I’m Hassy (niyisurvey). I’m smart, sweary, chaotic, and I want TwinSync to be **proper**, not half-baked. Here’s how to team up with me (or future humans/AIs) on this repo.

## 1. Who I am
- Linux power-user, not a professional coder.
- Love wild ideas, but I expect careful, safe execution.
- Assume the answer to “should we add this feature?” is usually **yes**.
- Still, do **not** touch the real system until I see a plan and approve it.

## 2. Collaboration rules
1. **Be playful but clear.** Warm tone, chaos allowed. When dealing with real commands/systems, switch into precise ops mode.
2. **Never assume context.** Ask me to run commands (`uname -a`, etc.) so we know exactly what environment we’re in.
3. **No placeholder commands.** Every command should be copy/paste ready.
4. **Full-file editing.** When updating files manually, I’ll paste the entire file; you return the entire new contents. No “insert this line” instructions.
5. **Step-by-step.** One command/edit at a time; wait for results before continuing.

## 3. Capabilities today
TwinSync v0.3 (Bash script `./twinsync`) can:
- Init/configure a local twin Git repo (default `~/twinsync-device`).
- Optionally create/link a private GitHub repo via API (remembers username/token, stored in `~/.config/twinsync/config`).
- Snapshot the system:
  - System info (uname, os-release, dpkg, systemctl, journalctl, crontab).
  - Filesystem roots (default `/etc` + `~/.config`, files <1 MB).
  - Git commit + optional push.
- Pull from GitHub remote (fast-forward only).
- Planner/Applier per domain:
  - Files (CREATE/REPLACE with backups).
  - Packages (apt INSTALL/REMOVE).
  - Services (systemd ENABLE/DISABLE/START/STOP).
  - Startup (user crontab replacement).
- Time Machine to reset the twin repo to an earlier commit.
- Whiptail TUI plus CLI shortcuts.

## 4. How to extend TwinSync
1. Start each session by grabbing environment facts from me:
   - `uname -a`
   - `cat /etc/os-release`
   - `git --version`
   - `systemctl --version` (if relevant)
2. Read [`TWIN_SYNC_SPEC.md`](TWIN_SYNC_SPEC.md) for architecture + data layout.
3. Stick to the collector/planner/applier/TUI structure.
4. Always show me a plan (text output, plan file preview, etc.) before running destructive operations.
5. Keep the twin repo as the source of truth; GitHub is a mirror for collaboration.
6. Document new features directly in the repo (README/spec/handoff updates as needed).

## 5. Future ideas (obvious backlog)
- Smarter include/exclude lists for filesystem snapshot, big-file handling.
- Richer startup capture (systemd timers, graphical autostart directories, etc.).
- Better logging + rollback when applying changes to the real system.
- Structured plan formats (YAML/JSON) stored under `plans/`.
- Packaging/installer (.deb, etc.) for easier distribution.

## 6. Tone + trust
I’m your chaotic co-pilot. Laugh, swear, celebrate with me — then double-check before touching real systems. TwinSync is here to give me confidence and control. Let’s keep it fun **and** safe.
