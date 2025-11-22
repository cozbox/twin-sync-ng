from __future__ import annotations

from typing import Dict, List


class DockerContainersPlugin:
    """Placeholder Docker containers plugin."""

    def detect(self, context) -> bool:  # noqa: D401
        return True

    def dump_state(self, context) -> Dict:
        return {"containers": {"backend": "docker", "services": []}}

    def plan(self, desired_fragment: Dict, live_fragment: Dict) -> Dict:
        return {"containers.docker": []}

    def apply(self, actions: List[Dict], context) -> None:
        return None
