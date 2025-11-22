"""TwinSync++ GUI using tkinter."""
from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

from . import config as config_module
from . import core
from . import paths
from . import utils


class TwinSyncGUI:
    """Main GUI window for TwinSync++."""

    def __init__(self, root: tk.Tk):
        """Initialize the GUI.
        
        Args:
            root: The tkinter root window
        """
        self.root = root
        self.root.title("TwinSync++ - Device Configuration Manager")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Configure grid weights for responsive layout
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="TwinSync++ Device Configuration Manager",
            font=("TkDefaultFont", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Status frame
        self.create_status_frame(main_frame)
        
        # Action buttons frame
        self.create_action_buttons(main_frame)
        
        # Output/log frame
        self.create_output_frame(main_frame)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Load initial status
        self.refresh_status()
        
    def create_status_frame(self, parent: ttk.Frame) -> None:
        """Create the status display frame.
        
        Args:
            parent: Parent frame to attach to
        """
        status_frame = ttk.LabelFrame(parent, text="Status", padding="10")
        status_frame.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W), pady=(0, 10))
        status_frame.grid_columnconfigure(1, weight=1)
        
        # Repository location
        ttk.Label(status_frame, text="Repository:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.repo_label = ttk.Label(status_frame, text="Not initialized", foreground="gray")
        self.repo_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Last snapshot
        ttk.Label(status_frame, text="Last Snapshot:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.snapshot_label = ttk.Label(status_frame, text="No snapshots", foreground="gray")
        self.snapshot_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Sync status
        ttk.Label(status_frame, text="GitHub Sync:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.sync_label = ttk.Label(status_frame, text="Not configured", foreground="gray")
        self.sync_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Drift status
        ttk.Label(status_frame, text="Drift Status:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.drift_label = ttk.Label(status_frame, text="Unknown", foreground="gray")
        self.drift_label.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
    def create_action_buttons(self, parent: ttk.Frame) -> None:
        """Create action buttons frame.
        
        Args:
            parent: Parent frame to attach to
        """
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, pady=(0, 10))
        
        # Primary actions
        ttk.Button(
            button_frame,
            text="Capture Snapshot",
            command=self.capture_snapshot,
            width=20
        ).grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="View History",
            command=self.view_history,
            width=20
        ).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="Settings",
            command=self.open_settings,
            width=20
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Secondary actions
        ttk.Button(
            button_frame,
            text="Generate Plan",
            command=self.generate_plan,
            width=20
        ).grid(row=1, column=0, padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="Apply Changes",
            command=self.apply_changes,
            width=20
        ).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="Refresh Status",
            command=self.refresh_status,
            width=20
        ).grid(row=1, column=2, padx=5, pady=5)
        
    def create_output_frame(self, parent: ttk.Frame) -> None:
        """Create output/log display frame.
        
        Args:
            parent: Parent frame to attach to
        """
        output_frame = ttk.LabelFrame(parent, text="Output", padding="5")
        output_frame.grid(row=3, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        output_frame.grid_rowconfigure(0, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            height=10,
            state=tk.DISABLED,
            font=("TkFixedFont", 9)
        )
        self.output_text.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        
    def log_output(self, message: str) -> None:
        """Log a message to the output area.
        
        Args:
            message: Message to log
        """
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.output_text.configure(state=tk.DISABLED)
        self.root.update_idletasks()
        
    def set_status(self, message: str) -> None:
        """Update the status bar.
        
        Args:
            message: Status message
        """
        self.status_var.set(message)
        self.root.update_idletasks()
        
    def refresh_status(self) -> None:
        """Refresh all status displays."""
        self.set_status("Refreshing status...")
        self.log_output("=" * 60)
        self.log_output("Refreshing status...")
        
        try:
            # Check repository
            config = config_module.load_config()
            repo_path = config.get("twin_repo", str(Path.home() / "twinsync-device"))
            
            if Path(repo_path).exists() and (Path(repo_path) / ".git").exists():
                self.repo_label.configure(text=repo_path, foreground="black")
                self.log_output(f"Repository: {repo_path}")
                
                # Get last snapshot from git log
                try:
                    history = core.get_git_history(Path(repo_path), limit=1)
                    if history:
                        last_commit = history[0]
                        snapshot_text = f"{last_commit['date']} - {last_commit['message']}"
                        self.snapshot_label.configure(text=snapshot_text, foreground="black")
                        self.log_output(f"Last snapshot: {snapshot_text}")
                    else:
                        self.snapshot_label.configure(text="No snapshots yet", foreground="gray")
                        self.log_output("No snapshots found")
                except Exception as e:
                    self.snapshot_label.configure(text="Error reading history", foreground="red")
                    self.log_output(f"Error reading history: {e}")
                
                # Check GitHub sync
                github_config = config.get("github", {})
                if github_config.get("user") and github_config.get("device_repo"):
                    user = github_config["user"]
                    repo = github_config["device_repo"]
                    sync_text = f"Configured: {user}/{repo}"
                    self.sync_label.configure(text=sync_text, foreground="green")
                    self.log_output(f"GitHub sync: {sync_text}")
                else:
                    self.sync_label.configure(text="Not configured", foreground="gray")
                    self.log_output("GitHub sync: Not configured")
                
                # Check drift
                try:
                    status = core.run_status(Path(repo_path))
                    drifted = sum(1 for v in status.values() if v)
                    in_sync = sum(1 for v in status.values() if not v)
                    
                    if drifted > 0:
                        drift_text = f"{drifted} drifted, {in_sync} in sync"
                        self.drift_label.configure(text=drift_text, foreground="orange")
                        self.log_output(f"Drift: {drift_text}")
                    else:
                        drift_text = f"All in sync ({in_sync} items)"
                        self.drift_label.configure(text=drift_text, foreground="green")
                        self.log_output(f"Drift: {drift_text}")
                except Exception as e:
                    self.drift_label.configure(text="Error checking drift", foreground="red")
                    self.log_output(f"Error checking drift: {e}")
            else:
                self.repo_label.configure(text="Not initialized", foreground="red")
                self.snapshot_label.configure(text="No snapshots", foreground="gray")
                self.sync_label.configure(text="Not configured", foreground="gray")
                self.drift_label.configure(text="Repository not initialized", foreground="gray")
                self.log_output("Repository not initialized. Use Settings to initialize.")
            
            self.set_status("Ready")
            self.log_output("Status refresh complete")
            
        except Exception as e:
            error_msg = f"Error refreshing status: {e}"
            self.log_output(error_msg)
            self.set_status("Error refreshing status")
            messagebox.showerror("Status Error", error_msg)
    
    def capture_snapshot(self) -> None:
        """Capture a snapshot of the current system state."""
        self.set_status("Capturing snapshot...")
        self.log_output("=" * 60)
        self.log_output("Starting snapshot capture...")
        
        try:
            # Check if repository is initialized
            config = config_module.load_config()
            repo_path = Path(config.get("twin_repo", str(Path.home() / "twinsync-device")))
            
            if not repo_path.exists() or not (repo_path / ".git").exists():
                if messagebox.askyesno(
                    "Repository Not Initialized",
                    "Twin repository is not initialized. Initialize now?"
                ):
                    self.log_output("Initializing repository...")
                    core.init_twin_repo(repo_path)
                    self.log_output(f"Repository initialized at: {repo_path}")
                else:
                    self.set_status("Snapshot cancelled")
                    return
            
            # Capture snapshot
            self.log_output("Capturing system state...")
            core.run_snapshot(repo_path, commit=True, push=False)
            self.log_output("Snapshot captured and committed")
            
            # Ask about pushing
            github_config = config.get("github", {})
            if github_config.get("user") and github_config.get("device_repo"):
                if messagebox.askyesno("Push to GitHub", "Snapshot captured. Push to GitHub?"):
                    self.log_output("Pushing to GitHub...")
                    success, msg = core.run_push(repo_path)
                    if success:
                        self.log_output("Successfully pushed to GitHub")
                        messagebox.showinfo("Success", "Snapshot captured and pushed to GitHub")
                    else:
                        self.log_output(f"Push failed: {msg}")
                        messagebox.showwarning("Push Failed", f"Snapshot saved locally but push failed:\n{msg}")
                else:
                    messagebox.showinfo("Success", "Snapshot captured and saved locally")
            else:
                messagebox.showinfo("Success", "Snapshot captured and saved locally")
            
            self.set_status("Snapshot complete")
            self.refresh_status()
            
        except Exception as e:
            error_msg = f"Snapshot failed: {e}"
            self.log_output(error_msg)
            self.set_status("Snapshot failed")
            messagebox.showerror("Snapshot Error", error_msg)
    
    def view_history(self) -> None:
        """View snapshot history."""
        self.set_status("Loading history...")
        self.log_output("=" * 60)
        self.log_output("Loading snapshot history...")
        
        try:
            config = config_module.load_config()
            repo_path = Path(config.get("twin_repo", str(Path.home() / "twinsync-device")))
            
            if not repo_path.exists() or not (repo_path / ".git").exists():
                messagebox.showwarning(
                    "No Repository",
                    "Twin repository is not initialized. Initialize in Settings first."
                )
                self.set_status("Ready")
                return
            
            # Get history
            history = core.get_git_history(repo_path, limit=50)
            
            if not history:
                messagebox.showinfo("No History", "No snapshots found. Capture a snapshot first.")
                self.set_status("Ready")
                return
            
            # Create history window
            history_window = tk.Toplevel(self.root)
            history_window.title("Snapshot History")
            history_window.geometry("700x500")
            
            # Title
            ttk.Label(
                history_window,
                text="Snapshot History - Time Machine",
                font=("TkDefaultFont", 12, "bold")
            ).pack(pady=10)
            
            # Info label
            ttk.Label(
                history_window,
                text="Select a snapshot to view details or restore to that state"
            ).pack(pady=(0, 10))
            
            # Listbox with scrollbar
            list_frame = ttk.Frame(history_window)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
            
            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("TkFixedFont", 9))
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=listbox.yview)
            
            # Populate listbox
            for entry in history:
                display_text = f"{entry['date']} | {entry['hash'][:8]} | {entry['message']}"
                listbox.insert(tk.END, display_text)
            
            # Buttons
            button_frame = ttk.Frame(history_window)
            button_frame.pack(pady=(0, 10))
            
            def restore_selected():
                selection = listbox.curselection()
                if not selection:
                    messagebox.showwarning("No Selection", "Please select a snapshot to restore")
                    return
                
                idx = selection[0]
                commit_hash = history[idx]["hash"]
                commit_msg = history[idx]["message"]
                
                if messagebox.askyesno(
                    "Confirm Restore",
                    f"Restore twin repository to:\n\n{commit_msg}\n\nCommit: {commit_hash}\n\n"
                    "This will reset the twin repository. You can then generate and apply "
                    "a plan to bring your system to this state.\n\nContinue?"
                ):
                    try:
                        if core.reset_to_commit(commit_hash, repo_path):
                            self.log_output(f"Restored to commit: {commit_hash}")
                            messagebox.showinfo(
                                "Success",
                                "Twin repository restored. Generate and apply a plan to restore system state."
                            )
                            history_window.destroy()
                            self.refresh_status()
                    except Exception as e:
                        messagebox.showerror("Restore Error", f"Failed to restore: {e}")
            
            ttk.Button(button_frame, text="Restore Selected", command=restore_selected, width=20).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Close", command=history_window.destroy, width=20).pack(side=tk.LEFT, padx=5)
            
            self.log_output(f"Loaded {len(history)} snapshots")
            self.set_status("Ready")
            
        except Exception as e:
            error_msg = f"Error loading history: {e}"
            self.log_output(error_msg)
            self.set_status("Error")
            messagebox.showerror("History Error", error_msg)
    
    def open_settings(self) -> None:
        """Open settings dialog."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("TwinSync++ Settings")
        settings_window.geometry("600x500")
        
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Repository tab
        repo_tab = ttk.Frame(notebook, padding="10")
        notebook.add(repo_tab, text="Repository")
        
        config = config_module.load_config()
        
        ttk.Label(repo_tab, text="Twin Repository Path:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        repo_path_var = tk.StringVar(value=config.get("twin_repo", str(Path.home() / "twinsync-device")))
        repo_entry = ttk.Entry(repo_tab, textvariable=repo_path_var, width=60)
        repo_entry.pack(fill=tk.X, pady=(0, 10))
        
        def init_repo():
            path = repo_path_var.get()
            if not path:
                messagebox.showwarning("Invalid Path", "Please enter a repository path")
                return
            
            try:
                config["twin_repo"] = path
                config_module.save_config(config)
                
                repo_root = Path(path)
                if not repo_root.exists() or not (repo_root / ".git").exists():
                    if messagebox.askyesno("Initialize Repository", f"Initialize twin repository at:\n{path}?"):
                        self.log_output("=" * 60)
                        self.log_output(f"Initializing repository at {path}...")
                        core.init_twin_repo(repo_root)
                        self.log_output("Repository initialized successfully")
                        messagebox.showinfo("Success", f"Repository initialized at:\n{path}")
                        self.refresh_status()
                else:
                    messagebox.showinfo("Already Initialized", f"Repository already exists at:\n{path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to initialize repository:\n{e}")
        
        ttk.Button(repo_tab, text="Initialize / Update Repository", command=init_repo).pack(pady=(0, 20))
        
        # GitHub tab
        github_tab = ttk.Frame(notebook, padding="10")
        notebook.add(github_tab, text="GitHub Sync")
        
        github_config = config.get("github", {})
        
        ttk.Label(github_tab, text="GitHub Username:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        github_user_var = tk.StringVar(value=github_config.get("user", ""))
        ttk.Entry(github_tab, textvariable=github_user_var, width=40).pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(github_tab, text="GitHub Token:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        github_token_var = tk.StringVar(value=github_config.get("token", ""))
        ttk.Entry(github_tab, textvariable=github_token_var, width=40, show="*").pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(github_tab, text="Repository Name:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        hostname = utils.get_hostname()
        github_repo_var = tk.StringVar(value=github_config.get("device_repo", f"twin-{hostname}"))
        ttk.Entry(github_tab, textvariable=github_repo_var, width=40).pack(fill=tk.X, pady=(0, 10))
        
        def setup_github():
            user = github_user_var.get().strip()
            token = github_token_var.get().strip()
            repo_name = github_repo_var.get().strip()
            
            if not user or not token or not repo_name:
                messagebox.showwarning("Missing Information", "Please fill in all GitHub fields")
                return
            
            try:
                self.log_output("=" * 60)
                self.log_output("Setting up GitHub integration...")
                success, msg = core.setup_github_remote(user, token, repo_name)
                self.log_output(msg)
                
                if success:
                    messagebox.showinfo("Success", msg)
                    self.refresh_status()
                else:
                    messagebox.showerror("Error", msg)
            except Exception as e:
                error_msg = f"GitHub setup failed: {e}"
                self.log_output(error_msg)
                messagebox.showerror("Error", error_msg)
        
        ttk.Button(github_tab, text="Setup GitHub Integration", command=setup_github).pack(pady=(0, 10))
        
        ttk.Label(
            github_tab,
            text="Note: Token needs 'repo' scope. Create at:\ngithub.com/settings/tokens",
            foreground="gray"
        ).pack(pady=(10, 0))
        
        # About tab
        about_tab = ttk.Frame(notebook, padding="10")
        notebook.add(about_tab, text="About")
        
        about_text = scrolledtext.ScrolledText(about_tab, wrap=tk.WORD, height=15)
        about_text.pack(fill=tk.BOTH, expand=True)
        
        about_content = """TwinSync++ - Device Configuration Manager

Version: 0.0.0

TwinSync++ is a Git-backed device configuration management tool that:

• Captures snapshots of your system configuration
• Stores them in a local Git repository  
• Optionally syncs to GitHub for backup and collaboration
• Generates plans showing configuration drift
• Safely applies changes to restore desired state

Features:
- System info, packages, services tracking
- Filesystem mirroring with selective roots
- Cron job management
- Time machine (restore to previous snapshots)
- GitHub integration for remote backup
- Safe change application with backups

For more information, visit:
https://github.com/cozbox/twin-sync-ng

License: MIT
"""
        about_text.insert(tk.END, about_content)
        about_text.configure(state=tk.DISABLED)
        
        # Close button
        ttk.Button(settings_window, text="Close", command=settings_window.destroy, width=15).pack(pady=10)
    
    def generate_plan(self) -> None:
        """Generate a drift plan."""
        self.set_status("Generating plan...")
        self.log_output("=" * 60)
        self.log_output("Generating plan...")
        
        try:
            config = config_module.load_config()
            repo_path = Path(config.get("twin_repo", str(Path.home() / "twinsync-device")))
            
            if not repo_path.exists() or not (repo_path / ".git").exists():
                messagebox.showwarning(
                    "No Repository",
                    "Twin repository is not initialized. Initialize in Settings first."
                )
                self.set_status("Ready")
                return
            
            plan = core.run_plan(repo_path)
            
            total_actions = sum(len(actions) for actions in plan.values())
            
            if total_actions == 0:
                self.log_output("No changes needed - system matches desired state")
                messagebox.showinfo("Plan Complete", "No changes needed.\n\nSystem matches desired state.")
            else:
                self.log_output(f"Plan generated with {total_actions} total action(s):")
                for plugin_name, actions in plan.items():
                    if actions:
                        self.log_output(f"  {plugin_name}: {len(actions)} action(s)")
                
                plan_file = paths.get_plan_dir(repo_path) / 'latest.yaml'
                messagebox.showinfo(
                    "Plan Complete",
                    f"Plan generated with {total_actions} action(s)\n\n"
                    f"Review plan at:\n{plan_file}\n\n"
                    "Use 'Apply Changes' to execute the plan."
                )
            
            self.set_status("Plan complete")
            self.refresh_status()
            
        except Exception as e:
            error_msg = f"Plan generation failed: {e}"
            self.log_output(error_msg)
            self.set_status("Plan failed")
            messagebox.showerror("Plan Error", error_msg)
    
    def apply_changes(self) -> None:
        """Apply the latest plan."""
        self.set_status("Checking plan...")
        self.log_output("=" * 60)
        self.log_output("Preparing to apply plan...")
        
        try:
            config = config_module.load_config()
            repo_path = Path(config.get("twin_repo", str(Path.home() / "twinsync-device")))
            
            if not repo_path.exists() or not (repo_path / ".git").exists():
                messagebox.showwarning(
                    "No Repository",
                    "Twin repository is not initialized. Initialize in Settings first."
                )
                self.set_status("Ready")
                return
            
            plan_path = paths.get_plan_dir(repo_path) / "latest.yaml"
            if not plan_path.exists():
                messagebox.showwarning(
                    "No Plan",
                    "No plan found. Generate a plan first using 'Generate Plan' button."
                )
                self.set_status("Ready")
                return
            
            # Load and check plan
            plan = utils.load_yaml(plan_path)
            total_actions = sum(len(actions) for actions in plan.values())
            
            if total_actions == 0:
                messagebox.showinfo("No Changes", "Plan is empty, nothing to apply.")
                self.set_status("Ready")
                return
            
            # Confirm with user
            if not messagebox.askyesno(
                "Confirm Apply",
                f"Apply plan with {total_actions} action(s)?\n\n"
                "This will modify your system.\n"
                "Backups will be created where appropriate.\n\n"
                "Continue?"
            ):
                self.log_output("Apply cancelled by user")
                self.set_status("Ready")
                return
            
            # Apply the plan
            self.log_output("Applying plan...")
            core.run_apply(repo_path)
            self.log_output("Plan applied successfully")
            
            messagebox.showinfo(
                "Apply Complete",
                f"Plan with {total_actions} action(s) applied successfully.\n\n"
                "Check the output log for details."
            )
            
            self.set_status("Apply complete")
            self.refresh_status()
            
        except Exception as e:
            error_msg = f"Apply failed: {e}"
            self.log_output(error_msg)
            self.set_status("Apply failed")
            messagebox.showerror("Apply Error", error_msg)


def launch_gui() -> None:
    """Launch the TwinSync++ GUI."""
    try:
        root = tk.Tk()
        app = TwinSyncGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Failed to launch GUI: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    launch_gui()
