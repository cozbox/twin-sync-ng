"""TwinSync++ CLI with whiptail menu and command-line interface."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from . import config as config_module
from . import core
from . import paths
from . import utils


def run_whiptail(args: List[str]) -> Tuple[int, str]:
    """Run whiptail and return exit code and output."""
    try:
        # Whiptail needs direct terminal access - use /dev/tty for stdin
        # and capture stderr for the actual output (whiptail writes to stderr by design)
        try:
            tty_in = open('/dev/tty', 'r')
        except (FileNotFoundError, OSError) as e:
            print("ERROR: Cannot access /dev/tty. Whiptail menus require a terminal.", file=sys.stderr)
            print(f"Details: {e}", file=sys.stderr)
            return 1, "no terminal available"
        
        try:
            result = subprocess.run(
                ["whiptail"] + args,
                stdin=tty_in,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            # Whiptail outputs selection to stderr by design
            return result.returncode, result.stderr.strip()
        finally:
            tty_in.close()
    except FileNotFoundError:
        print("ERROR: whiptail not found. Install it with: sudo apt-get install whiptail", file=sys.stderr)
        return 1, "whiptail not found"
    except Exception as e:
        print(f"ERROR running whiptail: {e}", file=sys.stderr)
        return 1, str(e)


def msgbox(title: str, text: str, height: int = 12, width: int = 70) -> None:
    """Display a message box."""
    run_whiptail(["--title", title, "--msgbox", text, str(height), str(width)])


def yesno(title: str, text: str, height: int = 12, width: int = 70) -> bool:
    """Display a yes/no dialog."""
    code, _ = run_whiptail(["--title", title, "--yesno", text, str(height), str(width)])
    return code == 0


def inputbox(title: str, text: str, default: str = "", height: int = 10, width: int = 70) -> Optional[str]:
    """Display an input box."""
    code, output = run_whiptail(["--title", title, "--inputbox", text, str(height), str(width), default])
    if code == 0:
        return output
    return None


def passwordbox(title: str, text: str, height: int = 12, width: int = 70) -> Optional[str]:
    """Display a password input box."""
    code, output = run_whiptail(["--title", title, "--passwordbox", text, str(height), str(width)])
    if code == 0:
        return output
    return None


def menu(title: str, text: str, choices: List[Tuple[str, str]], height: int = 20, width: int = 70) -> Optional[str]:
    """Display a menu."""
    args = ["--title", title, "--menu", text, str(height), str(width), str(len(choices))]
    for key, desc in choices:
        args.extend([key, desc])
    code, output = run_whiptail(args)
    if code == 0:
        return output
    return None


def checklist(title: str, text: str, choices: List[Tuple[str, str, bool]], 
              height: int = 20, width: int = 70) -> List[str]:
    """Display a checklist."""
    args = ["--title", title, "--separate-output", "--checklist", text, 
            str(height), str(width), str(len(choices))]
    for key, desc, checked in choices:
        args.extend([key, desc, "ON" if checked else "OFF"])
    code, output = run_whiptail(args)
    if code == 0:
        return [line.strip() for line in output.splitlines() if line.strip()]
    return []


# Menu handlers

def init_menu() -> None:
    """Initialize twin repository."""
    config = config_module.load_config()
    repo_path = config.get("twin_repo", str(Path.home() / "twinsync-device"))
    
    new_path = inputbox("Initialize Twin Repository", 
                       "Enter path for twin repository:", 
                       default=repo_path)
    if not new_path:
        return
    
    config["twin_repo"] = new_path
    config_module.save_config(config)
    
    try:
        repo_root = core.init_twin_repo(Path(new_path))
        msgbox("Success", f"Twin repository initialized at:\n{repo_root}\n\nRepository layout created with state/, live/, logs/, plan/, plugins/, schema/")
    except Exception as e:
        msgbox("Error", f"Failed to initialize repository:\n{e}")


def snapshot_menu() -> None:
    """Take a snapshot of the system."""
    if yesno("Take Snapshot", "Capture current system state to twin repository?\n\nThis will collect:\n- System info\n- Installed packages\n- Services state\n- Filesystem roots\n- Crontab\n- Logs"):
        try:
            core.run_snapshot(commit=True, push=False)
            
            if yesno("Snapshot Complete", "Snapshot committed locally.\n\nPush to GitHub remote?"):
                success, msg = core.run_push()
                if success:
                    msgbox("Success", "Snapshot pushed to GitHub")
                else:
                    msgbox("Push Info", f"Push status:\n{msg}")
            else:
                msgbox("Success", "Snapshot saved locally")
        except Exception as e:
            msgbox("Error", f"Snapshot failed:\n{e}")


def pull_menu() -> None:
    """Pull changes from remote."""
    if yesno("Pull from Remote", "Pull latest changes from GitHub?\n\nThis will update the twin repository with remote changes (fast-forward only)."):
        try:
            success, msg = core.run_pull()
            if success:
                msgbox("Success", "Successfully pulled from remote")
            else:
                msgbox("Pull Failed", f"Could not pull from remote:\n{msg}\n\nYou may need to resolve conflicts manually.")
        except Exception as e:
            msgbox("Error", f"Pull failed:\n{e}")


def plan_menu() -> None:
    """Generate a plan."""
    try:
        plan = core.run_plan()
        
        # Count actions
        total_actions = sum(len(actions) for actions in plan.values())
        
        if total_actions == 0:
            msgbox("Plan Complete", "No changes needed.\n\nSystem matches desired state.")
            return
        
        # Show plan summary
        summary = ["Plan generated with the following changes:\n"]
        for plugin_name, actions in plan.items():
            if actions:
                summary.append(f"{plugin_name}: {len(actions)} action(s)")
        
        # Get plan directory
        repo_root = paths.get_device_repo_root()
        plan_file = paths.get_plan_dir(repo_root) / 'latest.yaml'
        msgbox("Plan Complete", "\n".join(summary) + f"\n\nTotal: {total_actions} action(s)\n\nReview plan at: {plan_file}")
    except Exception as e:
        msgbox("Error", f"Planning failed:\n{e}")


def apply_menu() -> None:
    """Apply the latest plan."""
    try:
        repo_root = paths.get_device_repo_root()
        plan_path = paths.get_plan_dir(repo_root) / "latest.yaml"
        if not plan_path.exists():
            msgbox("No Plan", "No plan found.\n\nRun 'Plan' first to generate a plan.")
            return
        
        plan = utils.load_yaml(plan_path)
        total_actions = sum(len(actions) for actions in plan.values())
        
        if total_actions == 0:
            msgbox("No Changes", "Plan is empty, nothing to apply.")
            return
        
        if not yesno("Apply Plan", f"Apply plan with {total_actions} action(s)?\n\nThis will modify your system.\n\nBackups will be created where appropriate.\n\nContinue?"):
            return
        
        core.run_apply()
        msgbox("Apply Complete", f"Plan applied.\n\nCheck logs for details.")
    except Exception as e:
        msgbox("Error", f"Apply failed:\n{e}")


def status_menu() -> None:
    """Show system status."""
    try:
        status = core.run_status()
        
        in_sync = sum(1 for v in status.values() if not v)
        drifted = sum(1 for v in status.values() if v)
        
        summary = ["System Status:\n"]
        for name, has_drift in status.items():
            summary.append(f"{name}: {'DRIFT' if has_drift else 'in sync'}")
        
        summary.append(f"\nTotal: {in_sync} in sync, {drifted} drifted")
        msgbox("Status", "\n".join(summary))
    except Exception as e:
        msgbox("Error", f"Status check failed:\n{e}")


def config_display_menu() -> None:
    """Show current configuration."""
    try:
        config_text = core.get_config_display()
        msgbox("Configuration", config_text, height=20, width=80)
    except Exception as e:
        msgbox("Error", f"Failed to load configuration:\n{e}")


def configure_filesystem_roots_menu() -> None:
    """Configure filesystem roots to mirror."""
    config = config_module.load_config()
    current_roots = config_module.get_filesystem_roots(config)
    
    # Common candidates
    candidates = [
        "/etc",
        str(Path.home() / ".config"),
        str(Path.home() / ".ssh"),
        str(Path.home() / ".local"),
        "/usr/local/etc",
        "/var/www",
    ]
    
    # Build checklist
    choices = []
    for candidate in candidates:
        is_selected = candidate in current_roots
        choices.append((candidate, candidate, is_selected))
    
    selected = checklist(
        "Configure Filesystem Roots",
        "Select directories to mirror into twin:\n\nFiles over 1MB will be skipped.\n\nSpace to toggle, Enter to confirm.",
        choices,
        height=20,
        width=80
    )
    
    if selected:
        config_module.set_filesystem_roots(selected)
        msgbox("Success", f"Configured {len(selected)} filesystem root(s):\n" + "\n".join(selected))


def setup_github_menu() -> None:
    """Setup GitHub integration."""
    config = config_module.load_config()
    github_config = config.get("github", {})
    
    user = inputbox("GitHub Username", "Enter your GitHub username:", 
                   default=github_config.get("user", ""))
    if not user:
        return
    
    token = passwordbox("GitHub Token", 
                       "Enter GitHub personal access token:\n\n(Needs 'repo' scope)\n\nToken will be stored in config")
    if not token:
        return
    
    hostname = utils.get_hostname()
    default_repo = github_config.get("device_repo", f"twin-{hostname}")
    repo_name = inputbox("Repository Name", 
                        "Enter name for this device's repository:", 
                        default=default_repo)
    if not repo_name:
        return
    
    try:
        success, msg = core.setup_github_remote(user, token, repo_name)
        if success:
            msgbox("Success", msg)
        else:
            msgbox("Error", msg)
    except Exception as e:
        msgbox("Error", f"GitHub setup failed:\n{e}")


def time_machine_menu() -> None:
    """Time machine - navigate git history."""
    try:
        history = core.get_git_history(limit=20)
        
        if not history:
            msgbox("No History", "No git history found.\n\nTake a snapshot first.")
            return
        
        choices = [(entry["hash"], f"{entry['date']} - {entry['message']}") 
                  for entry in history]
        
        selected = menu("Time Machine", 
                       "Select a snapshot to reset to:\n\nWarning: This will reset your twin repository to the selected snapshot.",
                       choices,
                       height=22,
                       width=90)
        
        if selected:
            if yesno("Confirm Reset", 
                    f"Reset twin repository to commit {selected}?\n\nThis will change the twin repo history.\n\nYou can then plan/apply to bring the system to this state.\n\nContinue?"):
                if core.reset_to_commit(selected):
                    msgbox("Success", f"Twin repository reset to {selected}\n\nYou can now plan and apply to restore this state.")
    except Exception as e:
        msgbox("Error", f"Time machine failed:\n{e}")


def check_dependencies_menu() -> None:
    """Check system dependencies."""
    deps = core.check_system_dependencies()
    
    lines = ["Dependency Check:\n"]
    all_ok = True
    for cmd, available in deps.items():
        status = "✓" if available else "✗"
        lines.append(f"{status} {cmd}: {'installed' if available else 'MISSING'}")
        if not available:
            all_ok = False
    
    if not all_ok:
        lines.append("\nSome dependencies are missing.")
        lines.append("Install with: sudo apt-get install git whiptail")
    else:
        lines.append("\nAll dependencies satisfied!")
    
    msgbox("Dependencies", "\n".join(lines))


def setup_menu() -> None:
    """Setup submenu."""
    while True:
        choice = menu(
            "TwinSync++ Setup",
            "Configure TwinSync++ settings:",
            [
                ("1", "Initialize / configure twin repository"),
                ("2", "Configure filesystem roots"),
                ("3", "Setup GitHub integration"),
                ("4", "Check dependencies"),
                ("5", "Show current configuration"),
                ("6", "Back to main menu"),
            ]
        )
        
        if choice == "1":
            init_menu()
        elif choice == "2":
            configure_filesystem_roots_menu()
        elif choice == "3":
            setup_github_menu()
        elif choice == "4":
            check_dependencies_menu()
        elif choice == "5":
            config_display_menu()
        elif choice == "6" or choice is None:
            break


def snapshot_sync_menu() -> None:
    """Snapshot and sync submenu."""
    while True:
        choice = menu(
            "Snapshot & Sync",
            "Capture and synchronize system state:",
            [
                ("1", "Take snapshot (collect current state)"),
                ("2", "Pull from remote (get twin updates)"),
                ("3", "Back to main menu"),
            ]
        )
        
        if choice == "1":
            snapshot_menu()
        elif choice == "2":
            pull_menu()
        elif choice == "3" or choice is None:
            break


def plan_apply_menu() -> None:
    """Plan and apply submenu."""
    while True:
        choice = menu(
            "Plan & Apply",
            "Generate and execute change plans:",
            [
                ("1", "Generate plan (diff state vs live)"),
                ("2", "Apply plan (execute changes)"),
                ("3", "Show status (check drift)"),
                ("4", "Back to main menu"),
            ]
        )
        
        if choice == "1":
            plan_menu()
        elif choice == "2":
            apply_menu()
        elif choice == "3":
            status_menu()
        elif choice == "4" or choice is None:
            break


def main_menu() -> None:
    """Main TwinSync++ menu."""
    try:
        while True:
            choice = menu(
                "TwinSync++",
                "Linux device twin with Git-backed configuration management.\n\nChoose an option:",
                [
                    ("1", "Setup (init, config, GitHub, dependencies)"),
                    ("2", "Snapshot & Sync (collect and push/pull)"),
                    ("3", "Plan & Apply (diff and execute changes)"),
                    ("4", "Time Machine (git history navigation)"),
                    ("5", "Exit"),
                ],
                height=18,
                width=75
            )
            
            if choice == "1":
                setup_menu()
            elif choice == "2":
                snapshot_sync_menu()
            elif choice == "3":
                plan_apply_menu()
            elif choice == "4":
                time_machine_menu()
            elif choice == "5" or choice is None:
                break
    except KeyboardInterrupt:
        print("\nExiting TwinSync++", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: Menu failed: {e}", file=sys.stderr)
        print("Try running with a specific command instead: twin --help", file=sys.stderr)
        sys.exit(1)


def _build_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="twin",
        description="TwinSync++ - Git-backed device configuration management"
    )
    
    subparsers = parser.add_subparsers(dest="command")

    # Core commands
    subparsers.add_parser("init", help="Initialize a twin repository")
    subparsers.add_parser("snapshot", help="Capture live state and logs")
    
    snap_parser = subparsers.add_parser("snap", help="Alias for snapshot")
    snap_parser.add_argument("--push", action="store_true", help="Push after snapshot")
    
    subparsers.add_parser("pull", help="Pull from remote (fast-forward only)")
    subparsers.add_parser("push", help="Push to remote")
    subparsers.add_parser("plan", help="Calculate drift and generate action plan")
    subparsers.add_parser("apply", help="Apply the latest plan")
    subparsers.add_parser("status", help="Show drift status")
    subparsers.add_parser("logs", help="Show log summary")
    
    # Configuration
    subparsers.add_parser("config", help="Show current configuration")
    
    fs_parser = subparsers.add_parser("config-fs", help="Configure filesystem roots")
    
    gh_parser = subparsers.add_parser("setup-github", help="Setup GitHub integration")
    gh_parser.add_argument("--user", help="GitHub username")
    gh_parser.add_argument("--token", help="GitHub token")
    gh_parser.add_argument("--repo", help="Repository name")
    
    # Time machine
    tm_parser = subparsers.add_parser("time-machine", help="Navigate git history")
    tm_parser.add_argument("--commit", help="Commit hash to reset to")
    
    # Interactive menu
    subparsers.add_parser("menu", help="Launch interactive whiptail menu")
    
    # Dependencies
    subparsers.add_parser("check-deps", help="Check system dependencies")
    
    return parser


def main(argv: list[str] | None = None) -> None:
    """Main CLI entry point."""
    # Check if whiptail is available
    has_whiptail = utils.check_command_exists("whiptail")
    
    # If no arguments and whiptail available, launch menu
    if (argv is None and len(sys.argv) == 1) or (argv is not None and len(argv) == 0):
        if has_whiptail:
            main_menu()
            return
        else:
            print("Whiptail not found. Use command-line interface:")
            print("  twin --help")
            return
    
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        if has_whiptail:
            main_menu()
        else:
            parser.print_help()
        return

    # Execute commands
    try:
        if args.command == "init":
            core.init_twin_repo()
            
        elif args.command in ("snapshot", "snap"):
            push = getattr(args, "push", False)
            core.run_snapshot(commit=True, push=push)
            
        elif args.command == "pull":
            success, msg = core.run_pull()
            if not success:
                print(f"Pull failed: {msg}", file=sys.stderr)
                sys.exit(1)
                
        elif args.command == "push":
            success, msg = core.run_push()
            if not success:
                print(f"Push failed: {msg}", file=sys.stderr)
                sys.exit(1)
                
        elif args.command == "plan":
            core.run_plan()
            
        elif args.command == "apply":
            core.run_apply()
            
        elif args.command == "status":
            core.run_status()
            
        elif args.command == "logs":
            core.run_logs()
            
        elif args.command == "config":
            print(core.get_config_display())
            
        elif args.command == "config-fs":
            if has_whiptail:
                configure_filesystem_roots_menu()
            else:
                print("Whiptail required for interactive configuration")
                sys.exit(1)
                
        elif args.command == "setup-github":
            if has_whiptail and not (args.user and args.token and args.repo):
                setup_github_menu()
            elif args.user and args.token and args.repo:
                success, msg = core.setup_github_remote(args.user, args.token, args.repo)
                print(msg)
                if not success:
                    sys.exit(1)
            else:
                print("Provide --user, --token, and --repo, or use whiptail menu")
                sys.exit(1)
                
        elif args.command == "time-machine":
            if has_whiptail and not args.commit:
                time_machine_menu()
            elif args.commit:
                if not core.reset_to_commit(args.commit):
                    sys.exit(1)
            else:
                print("Provide --commit hash, or use whiptail menu")
                sys.exit(1)
                
        elif args.command == "menu":
            if has_whiptail:
                main_menu()
            else:
                print("Whiptail not installed")
                sys.exit(1)
                
        elif args.command == "check-deps":
            deps = core.check_system_dependencies()
            all_ok = True
            for cmd, available in deps.items():
                status = "✓" if available else "✗"
                print(f"{status} {cmd}: {'installed' if available else 'MISSING'}")
                if not available:
                    all_ok = False
            if not all_ok:
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
