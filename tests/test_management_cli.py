"""
Tests for the management command CLI.
"""

import importlib
import sys
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, contains_string, equal_to, greater_than, has_length

from src.management.cli import discover_commands, list_commands, main, parse_args


def test_discover_commands():
    """Test that discover_commands finds available commands."""
    commands = discover_commands()

    # Verify we have at least one command
    assert_that(commands, has_length(greater_than(0)))
    assert_that("cleanup_mcp_tokens" in commands, equal_to(True))
    assert_that(
        commands["cleanup_mcp_tokens"],
        equal_to("src.management.commands.cleanup_mcp_tokens"),
    )


@patch("src.management.cli.discover_commands")
@patch("builtins.print")
def test_list_commands(mock_print, mock_discover):
    """Test the list_commands function."""
    # Mock the discovery of commands
    mock_discover.return_value = {
        "process_jobs": "src.management.commands.process_jobs"
    }

    # Call the function
    list_commands()

    # Verify output
    mock_print.assert_any_call("Available commands:")
    # The second call should contain "process_jobs" in the output
    assert_that("process_jobs" in str(mock_print.call_args_list[1]), equal_to(True))


@patch("sys.argv", ["manage.py", "process_jobs", "--single-run", "--interval", "5"])
def test_parse_args_command_with_options():
    """Test parsing a command with options."""
    command, args = parse_args()

    assert_that(command, equal_to("process_jobs"))
    assert_that(args.get("single_run"), equal_to(True))
    assert_that(args.get("interval"), equal_to(5))


@patch("src.management.cli.parse_args")
@patch("src.management.cli.discover_commands")
@patch("builtins.print")
@patch("src.management.cli.list_commands")
def test_main_unknown_command(mock_list, mock_print, mock_discover, mock_parse):
    """Test main function when an unknown command is provided."""
    # Mock parsed arguments for unknown command
    mock_parse.return_value = ("unknown_command", {})

    # Mock command discovery with only process_jobs
    mock_discover.return_value = {
        "process_jobs": "src.management.commands.process_jobs"
    }

    # Call main
    result = main()

    # Verify the result
    assert_that(result, equal_to(1))  # Should exit with error
    mock_print.assert_any_call("Unknown command: unknown_command")
    mock_list.assert_called_once()  # Should list available commands
