from __future__ import annotations

from typing import Dict


class FilesLogsPlugin:
    """Placeholder file log collector."""

    def detect(self, context) -> bool:  # noqa: D401
        return True

    def dump_logs(self, context) -> Dict:
        return {"files": {"entries": 0}}
