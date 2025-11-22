from __future__ import annotations

from typing import Dict, List


class MirrorFilesPlugin:
    """Placeholder for filesystem mirroring plugin."""

    def detect(self, context) -> bool:  # noqa: D401
        return True

    def dump_state(self, context) -> Dict:
        return {"files": []}

    def plan(self, desired_fragment: Dict, live_fragment: Dict) -> Dict:
        return {"files.mirror": []}

    def apply(self, actions: List[Dict], context) -> None:
        return None
