from __future__ import annotations

from typing import Dict, List


class GnomeDesktopPlugin:
    """Placeholder GNOME desktop plugin."""

    def detect(self, context) -> bool:  # noqa: D401
        return True

    def dump_state(self, context) -> Dict:
        return {"desktop": {"backend": "gnome", "settings": {}}}

    def plan(self, desired_fragment: Dict, live_fragment: Dict) -> Dict:
        return {"desktop.gnome": []}

    def apply(self, actions: List[Dict], context) -> None:
        return None
