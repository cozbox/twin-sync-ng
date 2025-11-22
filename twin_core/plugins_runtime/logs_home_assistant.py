from __future__ import annotations

from typing import Dict


class HomeAssistantLogsPlugin:
    """Placeholder Home Assistant logs plugin."""

    def detect(self, context) -> bool:  # noqa: D401
        return True

    def dump_logs(self, context) -> Dict:
        return {"home_assistant": {"entries": 0}}
