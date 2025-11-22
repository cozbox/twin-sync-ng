from __future__ import annotations

import shutil
import subprocess
from typing import Dict, List


class SystemdServicesPlugin:
    """Capture basic systemd unit state."""

    def detect(self, context) -> bool:  # noqa: D401
        return shutil.which("systemctl") is not None

    def dump_state(self, context) -> Dict:
        services: List[Dict[str, object]] = []
        list_units = subprocess.run(
            ["systemctl", "list-unit-files", "--type", "service", "--no-legend"],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in list_units.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            name, enabled_flag = parts[0], parts[1]
            active = subprocess.run(
                ["systemctl", "is-active", name], capture_output=True, text=True, check=False
            )
            services.append(
                {
                    "name": name,
                    "enabled": enabled_flag.lower() == "enabled",
                    "running": active.stdout.strip() == "active",
                }
            )
        return {"services": services}

    def plan(self, desired_fragment: Dict, live_fragment: Dict) -> Dict:
        desired_by_name = {svc["name"]: svc for svc in desired_fragment.get("services", [])}
        live_by_name = {svc["name"]: svc for svc in live_fragment.get("services", [])}
        actions: List[Dict[str, object]] = []
        for name, desired in desired_by_name.items():
            live = live_by_name.get(name, {"enabled": False, "running": False})
            if desired.get("enabled") and not live.get("enabled"):
                actions.append({"op": "enable", "name": name})
            if not desired.get("enabled") and live.get("enabled"):
                actions.append({"op": "disable", "name": name})
            if desired.get("running") and not live.get("running"):
                actions.append({"op": "start", "name": name})
            if not desired.get("running") and live.get("running"):
                actions.append({"op": "stop", "name": name})
        return {"services.systemd": actions}

    def apply(self, actions: List[Dict[str, object]], context) -> None:
        for action in actions:
            op = action.get("op")
            name = action.get("name")
            if op == "enable":
                subprocess.run(["sudo", "systemctl", "enable", name], check=False)
            elif op == "disable":
                subprocess.run(["sudo", "systemctl", "disable", name], check=False)
            elif op == "start":
                subprocess.run(["sudo", "systemctl", "start", name], check=False)
            elif op == "stop":
                subprocess.run(["sudo", "systemctl", "stop", name], check=False)
