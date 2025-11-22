"""System information collector plugin for TwinSync++."""
from __future__ import annotations

import platform
import subprocess
from pathlib import Path
from typing import Dict, List


class SystemInfoPlugin:
    """Collect basic system information (uname, os-release, hostname)."""

    def detect(self, context) -> bool:
        """Always available on Linux systems."""
        return platform.system() == "Linux"

    def dump_state(self, context) -> Dict:
        """Collect system information.
        
        Captures:
        - uname output
        - hostname
        - /etc/os-release contents
        - kernel version
        """
        system_info = {}
        
        # Get uname
        try:
            result = subprocess.run(
                ["uname", "-a"],
                capture_output=True,
                text=True,
                check=True,
            )
            system_info["uname"] = result.stdout.strip()
        except Exception:
            system_info["uname"] = ""
        
        # Get hostname
        try:
            result = subprocess.run(
                ["hostname"],
                capture_output=True,
                text=True,
                check=True,
            )
            system_info["hostname"] = result.stdout.strip()
        except Exception:
            system_info["hostname"] = platform.node()
        
        # Parse /etc/os-release
        os_release = {}
        os_release_path = Path("/etc/os-release")
        if os_release_path.exists():
            try:
                content = os_release_path.read_text(encoding='utf-8')
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        # Remove quotes
                        value = value.strip().strip('"').strip("'")
                        os_release[key] = value
            except Exception:
                pass
        system_info["os_release"] = os_release
        
        # Get kernel version
        system_info["kernel"] = platform.release()
        
        return {"system": system_info}

    def plan(self, desired_fragment: Dict, live_fragment: Dict) -> Dict:
        """System info is read-only, no planning needed."""
        # System information is typically read-only and not applied
        return {"system.info": []}

    def apply(self, actions: List[Dict], context) -> None:
        """System info is read-only, no apply action."""
        # System information cannot be applied
        pass
