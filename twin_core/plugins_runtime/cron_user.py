from __future__ import annotations

from typing import Dict, List


class CronUserPlugin:
    """Placeholder cron plugin."""

    def detect(self, context) -> bool:  # noqa: D401
        return True

    def dump_state(self, context) -> Dict:
        return {"cron": {"entries": []}}

    def plan(self, desired_fragment: Dict, live_fragment: Dict) -> Dict:
        return {"cron.user": []}

    def apply(self, actions: List[Dict], context) -> None:
        return None
