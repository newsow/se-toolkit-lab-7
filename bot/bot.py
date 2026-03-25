#!/usr/bin/env python3
"""LMS Telegram Bot entry point.

Usage:
    uv run bot.py              # Run Telegram bot (requires BOT_TOKEN)
    uv run bot.py --test "/start"  # Test mode: print handler response to stdout
"""

import argparse
import sys
from typing import Callable

from handlers import (
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
    handle_start,
)


# Command router: maps command strings to handler functions
COMMANDS: dict[str, Callable[[str], str]] = {
    "/start": handle_start,
    "/help": handle_help,
    "/health": handle_health,
    "/labs": handle_labs,
    "/scores": handle_scores,
}


def run_test_mode(command: str) -> None:
    """Run a command in test mode — call handler directly and print result.
    
    Args:
        command: Command string, e.g., "/start" or "/scores lab-04"
    """
    # Extract command name (first word)
    cmd_name = command.split()[0] if command else ""
    
    handler = COMMANDS.get(cmd_name)
    if handler is None:
        print(f"Unknown command: {cmd_name}")
        print("Use /help to see available commands.")
        sys.exit(1)
    
    # Call handler and print result
    response = handler(command)
    print(response)
    sys.exit(0)


def run_telegram_bot() -> None:
    """Run the Telegram bot using aiogram.
    
    This will be implemented in Task 2 when we connect to Telegram.
    """
    from config import settings

    if not settings.bot_token:
        print("Error: BOT_TOKEN not set in .env.bot.secret")
        print("Cannot start Telegram bot without a token.")
        sys.exit(1)

    # Task 2: Initialize aiogram and start polling
    print("Telegram bot starting... (placeholder)")
    print("This will be implemented in Task 2.")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="LMS Telegram Bot",
    )
    parser.add_argument(
        "--test",
        type=str,
        metavar="COMMAND",
        help="Test mode: run a command and print response to stdout",
    )

    args = parser.parse_args()

    if args.test:
        run_test_mode(args.test)
    else:
        run_telegram_bot()


if __name__ == "__main__":
    main()
