"""Filesystem mirroring plugin for TwinSync++."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Dict, List

from .. import config as config_module
from .. import utils


class MirrorFilesPlugin:
    """Mirror filesystem roots into the twin repository."""

    def detect(self, context) -> bool:
        """Always available on any system."""
        return True

    def dump_state(self, context) -> Dict:
        """Collect files from configured filesystem roots.
        
        Captures:
        - File paths relative to root
        - File content (for files < 1MB)
        - File metadata (permissions, size, mtime)
        - Content hash for change detection
        """
        config = config_module.load_config(context.repo_root)
        roots = config_module.get_filesystem_roots(config)
        
        files_data: List[Dict] = []
        
        for root_str in roots:
            root = Path(root_str).expanduser().resolve()
            if not root.exists() or not root.is_dir():
                print(f"Warning: Filesystem root does not exist: {root}")
                continue
            
            # Skip root filesystem to avoid issues
            if str(root) == "/":
                print("Warning: Skipping root filesystem /")
                continue
            
            try:
                # Walk the directory and collect files
                for file_path in utils.walk_directory(root, max_size_mb=1):
                    try:
                        relative = str(file_path.relative_to(root))
                        stat = file_path.stat()
                        
                        # Read content for text files under 1MB
                        content = None
                        content_hash = None
                        try:
                            if utils.is_text_file(file_path):
                                content = file_path.read_text(encoding='utf-8', errors='ignore')
                                content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
                        except Exception:
                            pass
                        
                        files_data.append({
                            "root": str(root),
                            "path": "/" + str(file_path.relative_to("/")),
                            "relative": relative,
                            "size": stat.st_size,
                            "mode": oct(stat.st_mode)[-4:],
                            "mtime": int(stat.st_mtime),
                            "content": content,
                            "hash": content_hash,
                        })
                    except Exception as e:
                        print(f"Warning: Could not process file {file_path}: {e}")
            except Exception as e:
                print(f"Warning: Error walking {root}: {e}")
        
        return {"files": files_data}

    def plan(self, desired_fragment: Dict, live_fragment: Dict) -> Dict:
        """Generate file change plan by comparing desired state to live state.
        
        Actions:
        - CREATE: File exists in desired but not in live
        - REPLACE: File exists in both but content differs
        - DELETE: File exists in live but not in desired (optional, typically not done)
        """
        desired_files = desired_fragment.get("files", [])
        live_files = live_fragment.get("files", [])
        
        # Index by path for fast lookup
        desired_by_path = {f["path"]: f for f in desired_files}
        live_by_path = {f["path"]: f for f in live_files}
        
        actions: List[Dict] = []
        
        for path, desired in desired_by_path.items():
            if path not in live_by_path:
                # File needs to be created
                actions.append({
                    "op": "create",
                    "path": path,
                    "content": desired.get("content"),
                    "mode": desired.get("mode"),
                })
            else:
                live = live_by_path[path]
                # Check if content changed
                if desired.get("hash") != live.get("hash"):
                    actions.append({
                        "op": "replace",
                        "path": path,
                        "content": desired.get("content"),
                        "mode": desired.get("mode"),
                    })
        
        return {"files.mirror": actions}

    def apply(self, actions: List[Dict], context) -> None:
        """Apply file changes to the live system.
        
        Creates or replaces files with timestamped backups for replacements.
        """
        for action in actions:
            op = action.get("op")
            path = Path(action.get("path"))
            content = action.get("content")
            mode = action.get("mode")
            
            try:
                if op == "create":
                    # Create the file
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if content is not None:
                        path.write_text(content, encoding='utf-8')
                    if mode:
                        try:
                            os.chmod(path, int(mode, 8))
                        except Exception:
                            pass
                    print(f"Created: {path}")
                    
                elif op == "replace":
                    # Backup existing file
                    if path.exists():
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                        backup = Path(str(path) + f".twinbak-{timestamp}")
                        try:
                            import shutil
                            shutil.copy2(path, backup)
                        except Exception as e:
                            print(f"Warning: Could not backup {path}: {e}")
                    
                    # Replace the file
                    if content is not None:
                        path.write_text(content, encoding='utf-8')
                    if mode:
                        try:
                            os.chmod(path, int(mode, 8))
                        except Exception:
                            pass
                    print(f"Replaced: {path}")
                    
            except PermissionError:
                print(f"Error: Permission denied for {path} (may need sudo)")
            except Exception as e:
                print(f"Error: Failed to {op} {path}: {e}")
