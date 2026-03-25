"""Command handlers that call the LMS backend.

Each handler is a pure function: it takes input and returns text.
No Telegram dependency — handlers work from --test mode, unit tests, or Telegram.
"""

import sys
from pathlib import Path

# Add bot/ to path so imports work from subdirectory
bot_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(bot_root))

from services.lms_client import LMSClient


def handle_start(command: str) -> str:
    """Handle /start command — welcome message."""
    return (
        "Welcome to the LMS Bot! I can help you check system health, browse labs, "
        "and view scores. Use /help to see all available commands."
    )


def handle_help(command: str) -> str:
    """Handle /help command — list available commands."""
    return (
        "Available commands:\n"
        "  /start — Welcome message\n"
        "  /help — Show this help\n"
        "  /health — Check backend status\n"
        "  /labs — List available labs\n"
        "  /scores <lab> — View scores for a lab (e.g., /scores lab-04)"
    )


def handle_health(command: str) -> str:
    """Handle /health command — backend status check."""
    client = LMSClient()
    return client.health_check()


def handle_labs(command: str) -> str:
    """Handle /labs command — list available labs."""
    client = LMSClient()
    return client.get_labs()


def handle_scores(command: str) -> str:
    """Handle /scores command — view scores for a lab.

    Args:
        command: Full command string, e.g., "/scores lab-04"
    """
    parts = command.split()
    if len(parts) < 2:
        return "Please specify a lab: /scores <lab-name> (e.g., /scores lab-04)"

    lab_name = parts[1]
    client = LMSClient()
    return client.get_scores(lab_name)
