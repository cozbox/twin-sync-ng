from __future__ import annotations

from typing import Dict


class SystemdJournalLogsPlugin:
    """Placeholder systemd journal logs plugin."""

    def detect(self, context) -> bool:  # noqa: D401
        return True

    def dump_logs(self, context) -> Dict:
        return {"systemd_journal": {"entries": 0}}
