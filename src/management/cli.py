"""
Command-line interface for TaskManagement management commands.
"""

import argparse
import importlib
import logging
import os
import pkgutil
import sys
import traceback
from typing import Any, Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def discover_commands() -> Dict[str, str]:
    """
    Discover available commands in the commands package.

    Returns:
        Dict[str, str]: Dictionary mapping command names to module paths
    """
    from src.management import commands

    available_commands = {}

    package_path = os.path.dirname(commands.__file__)
    for _, name, is_pkg in pkgutil.iter_modules([package_path]):
        if not is_pkg and not name.startswith("_"):
            available_commands[name] = f"src.management.commands.{name}"

    return available_commands


def list_commands() -> None:
    """List all available commands with their help text."""
    commands = discover_commands()

    print("Available commands:")
    for name, module_path in commands.items():
        try:
            module = importlib.import_module(module_path)
            help_text = (
                module.get_help()
                if hasattr(module, "get_help")
                else "No description available"
            )
            print(f"  {name} - {help_text}")
        except ImportError as e:
            print(f"  {name} - [Error loading command: {str(e)}]")


def parse_args() -> Tuple[str, Dict[str, Any]]:
    """
    Parse command-line arguments.

    Returns:
        Tuple[str, Dict[str, Any]]: Command name and arguments dictionary
    """
    parser = argparse.ArgumentParser(description="TaskManagement management commands")
    parser.add_argument("command", nargs="?", help="Command to run")
    parser.add_argument("--list", action="store_true", help="List available commands")

    # Add common arguments
    parser.add_argument(
        "--interval",
        type=int,
        help="Interval between operations (for long-running commands)",
    )
    parser.add_argument(
        "--single-run",
        action="store_true",
        help="Only run once (for commands that normally run continuously)",
    )

    args, unknown = parser.parse_known_args()

    # Convert args to dictionary
    args_dict = vars(args).copy()
    command = args_dict.pop("command")
    args_dict.pop("list")  # Remove the list flag

    return command, args_dict


def main() -> int:
    """
    Main entry point for the CLI.

    Returns:
        int: Exit code
    """
    command_name, args = parse_args()

    # Handle --list flag
    if args.get("list"):
        list_commands()
        return 0

    # Show help if no command specified
    if not command_name:
        list_commands()
        return 0

    # Find and execute the command
    commands = discover_commands()
    if command_name not in commands:
        print(f"Unknown command: {command_name}")
        list_commands()
        return 1

    try:
        module_path = commands[command_name]
        print(f"Attempting to load module: {module_path}")
        module = importlib.import_module(module_path)
        if hasattr(module, "execute"):
            print(f"Executing command: {command_name}")
            return module.execute(args) or 0
        else:
            print(f"Command {command_name} has no execute function")
            return 1
    except ImportError as e:
        print(f"Error loading command {command_name}: {str(e)}")
        print("--- Traceback --- BGN ---")
        traceback.print_exc()
        print("--- Traceback --- END ---")
        return 1
    except Exception as e:
        print(f"Error executing command {command_name}: {str(e)}")
        print("--- Traceback --- BGN ---")
        traceback.print_exc()
        print("--- Traceback --- END ---")
        return 1


if __name__ == "__main__":
    sys.exit(main())
