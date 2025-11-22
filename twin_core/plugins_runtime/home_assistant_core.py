from __future__ import annotations

from typing import Dict, List


class HomeAssistantCorePlugin:
    """Placeholder Home Assistant core config plugin."""

    def detect(self, context) -> bool:  # noqa: D401
        return True

    def dump_state(self, context) -> Dict:
        return {"home_assistant": {"config_files": []}}

    def plan(self, desired_fragment: Dict, live_fragment: Dict) -> Dict:
        return {"home_assistant.core": []}

    def apply(self, actions: List[Dict], context) -> None:
        return None
