from __future__ import annotations

import subprocess
import shutil
from typing import Dict, List


class DebianPackagesPlugin:
    """Manage Debian packages using dpkg/apt."""

    def detect(self, context) -> bool:  # noqa: D401
        return shutil.which("dpkg-query") is not None

    def dump_state(self, context) -> Dict:
        result = subprocess.run(
            ["dpkg-query", "-W", "-f=${Package}\t${Version}\n"],
            check=False,
            capture_output=True,
            text=True,
        )
        packages: List[Dict[str, str]] = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            try:
                name, version = line.split("\t", 1)
            except ValueError:
                continue
            packages.append(
                {
                    "name": name,
                    "source": "apt",
                    "installed": True,
                    "version": version.strip(),
                }
            )
        return {"packages": packages}

    def plan(self, desired_fragment: Dict, live_fragment: Dict) -> Dict:
        desired_by_name = {pkg["name"]: pkg for pkg in desired_fragment.get("packages", [])}
        live_by_name = {pkg["name"]: pkg for pkg in live_fragment.get("packages", [])}
        actions: List[Dict[str, str]] = []
        for name, desired in desired_by_name.items():
            ensure = desired.get("ensure", "present")
            installed = name in live_by_name
            if ensure == "present" and not installed:
                actions.append({"op": "install", "name": name})
            elif ensure == "absent" and installed:
                actions.append({"op": "remove", "name": name})
        for name in live_by_name:
            if name not in desired_by_name:
                actions.append({"op": "remove", "name": name})
        return {"packages.debian": actions}

    def apply(self, actions: List[Dict[str, str]], context) -> None:
        for action in actions:
            op = action.get("op")
            name = action.get("name")
            if op == "install":
                subprocess.run(["sudo", "apt-get", "install", "-y", name], check=False)
            elif op == "remove":
                subprocess.run(["sudo", "apt-get", "remove", "-y", name], check=False)
