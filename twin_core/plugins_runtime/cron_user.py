"""User crontab plugin for TwinSync++."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List


class CronUserPlugin:
    """Manage user crontab entries."""

    def detect(self, context) -> bool:
        """Check if crontab command is available."""
        return shutil.which("crontab") is not None

    def dump_state(self, context) -> Dict:
        """Capture current user crontab.
        
        Returns:
            Crontab entries as a string
        """
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.returncode == 0:
                content = result.stdout
                # Parse crontab entries
                entries = []
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        entries.append(line)
                
                return {
                    "cron": {
                        "content": content,
                        "entries": entries,
                    }
                }
            else:
                # No crontab exists yet
                return {"cron": {"content": "", "entries": []}}
        except Exception as e:
            print(f"Warning: Failed to read crontab: {e}")
            return {"cron": {"content": "", "entries": []}}

    def plan(self, desired_fragment: Dict, live_fragment: Dict) -> Dict:
        """Generate crontab update plan.
        
        Actions:
        - UPDATE: Replace entire crontab if content differs
        """
        desired_cron = desired_fragment.get("cron", {})
        live_cron = live_fragment.get("cron", {})
        
        desired_content = desired_cron.get("content", "")
        live_content = live_cron.get("content", "")
        
        actions: List[Dict] = []
        
        if desired_content != live_content:
            actions.append({
                "op": "update",
                "content": desired_content,
            })
        
        return {"cron.user": actions}

    def apply(self, actions: List[Dict], context) -> None:
        """Apply crontab changes.
        
        Replaces user crontab with desired content after backing up.
        """
        for action in actions:
            op = action.get("op")
            content = action.get("content")
            
            if op == "update":
                try:
                    # Backup current crontab
                    backup_result = subprocess.run(
                        ["crontab", "-l"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    
                    if backup_result.returncode == 0:
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                        backup_file = Path.home() / f".crontab.twinbak-{timestamp}"
                        backup_file.write_text(backup_result.stdout, encoding='utf-8')
                        print(f"Backed up crontab to: {backup_file}")
                    
                    # Write new crontab
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cron') as f:
                        f.write(content)
                        temp_path = f.name
                    
                    try:
                        result = subprocess.run(
                            ["crontab", temp_path],
                            capture_output=True,
                            text=True,
                            check=True,
                        )
                        print("Crontab updated successfully")
                    finally:
                        Path(temp_path).unlink(missing_ok=True)
                        
                except subprocess.CalledProcessError as e:
                    print(f"Error: Failed to update crontab: {e.stderr}")
                except Exception as e:
                    print(f"Error: Failed to update crontab: {e}")
