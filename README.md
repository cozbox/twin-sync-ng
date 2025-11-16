# TwinSync

Linux-only digital twin tool for your machines.

TwinSync snapshots your system’s config, packages, services, startup and logs into a local Git repo (the "twin"). That twin can optionally be pushed to a private GitHub repo so humans or AI can inspect, edit, and propose fixes. TwinSync then shows a clear plan before safely applying those changes back to the real machine.

For the full architecture and design, see **TWIN_SYNC_SPEC.md**.
