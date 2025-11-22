from __future__ import annotations

from typing import Dict, List


class NetworkManagerPlugin:
    """Placeholder NetworkManager plugin."""

    def detect(self, context) -> bool:  # noqa: D401
        return True

    def dump_state(self, context) -> Dict:
        return {"network": {"profiles": []}}

    def plan(self, desired_fragment: Dict, live_fragment: Dict) -> Dict:
        return {"network.networkmanager": []}

    def apply(self, actions: List[Dict], context) -> None:
        return None
