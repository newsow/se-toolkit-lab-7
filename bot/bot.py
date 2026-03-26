#!/usr/bin/env python3
"""LMS Telegram Bot entry point.

Usage:
    uv run bot.py              # Run Telegram bot (requires BOT_TOKEN)
    uv run bot.py --test "/start"  # Test mode: print handler response to stdout
    uv run bot.py --test "what labs are available"  # Natural language query
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
from handlers.intent_router import route_intent


# Command router: maps command strings to handler functions
COMMANDS: dict[str, Callable[[str], str]] = {
    "/start": handle_start,
    "/help": handle_help,
    "/health": handle_health,
    "/labs": handle_labs,
    "/scores": handle_scores,
}


def run_test_mode(message: str) -> None:
    """Run a command or natural language query in test mode.

    Args:
        message: Command string or natural language query
    """
    # Check if it's a slash command
    if message.startswith("/"):
        cmd_name = message.split()[0] if message else ""

        handler = COMMANDS.get(cmd_name)
        if handler is None:
            print(f"Unknown command: {cmd_name}")
            print("Use /help to see available commands.")
            sys.exit(0)  # Exit cleanly - unknown commands should not crash

        # Call handler and print result
        response = handler(message)
        print(response)
        sys.exit(0)
    else:
        # Natural language query - use LLM intent router
        response = route_intent(message)
        print(response)
        sys.exit(0)


def run_telegram_bot() -> None:
    """Run the Telegram bot using aiogram.

    Handles both slash commands and natural language messages.
    Uses inline keyboard buttons for common queries.
    """
    from config import settings

    if not settings.bot_token:
        print("Error: BOT_TOKEN not set in .env.bot.secret")
        print("Cannot start Telegram bot without a token.")
        sys.exit(1)

    # Import aiogram here to avoid dependency in test mode
    from aiogram import Bot, Dispatcher, types
    from aiogram.filters import Command, CommandStart
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # Command handlers
    @dp.message(CommandStart())
    async def cmd_start(message: types.Message):
        """Handle /start command with inline keyboard."""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📚 Labs", callback_data="query_labs"),
                    InlineKeyboardButton(text="📊 Scores", callback_data="query_scores"),
                ],
                [
                    InlineKeyboardButton(text="👥 Top Students", callback_data="query_top"),
                    InlineKeyboardButton(text="📈 Completion", callback_data="query_completion"),
                ],
                [
                    InlineKeyboardButton(text="🏆 Groups", callback_data="query_groups"),
                    InlineKeyboardButton(text="🔄 Sync Data", callback_data="query_sync"),
                ],
            ]
        )
        await message.answer(
            "Welcome to the LMS Bot! I can help you check system health, browse labs, "
            "and view scores. Use the buttons below or ask me a question!",
            reply_markup=keyboard,
        )

    @dp.message(Command("help"))
    async def cmd_help(message: types.Message):
        """Handle /help command."""
        help_text = (
            "Available commands:\n"
            "  /start — Welcome message\n"
            "  /help — Show this help\n"
            "  /health — Check backend status\n"
            "  /labs — List available labs\n"
            "  /scores <lab> — View scores for a lab\n\n"
            "You can also ask questions in natural language:\n"
            "  • what labs are available?\n"
            "  • show me scores for lab 4\n"
            "  • which lab has the lowest pass rate?\n"
            "  • who are the top 5 students?"
        )
        await message.answer(help_text)

    @dp.message(Command("health"))
    async def cmd_health(message: types.Message):
        """Handle /health command."""
        response = handle_health("")
        await message.answer(response)

    @dp.message(Command("labs"))
    async def cmd_labs(message: types.Message):
        """Handle /labs command."""
        response = handle_labs("")
        await message.answer(response)

    @dp.message(Command("scores"))
    async def cmd_scores(message: types.Message):
        """Handle /scores command."""
        args = message.text.split()[1:] if message.text else []
        lab = " ".join(args) if args else ""
        response = handle_scores(f"/scores {lab}" if lab else "/scores")
        await message.answer(response)

    @dp.callback_query()
    async def handle_callback(callback_query: types.CallbackQuery):
        """Handle inline keyboard button callbacks."""
        action = callback_query.data

        if action == "query_labs":
            response = handle_labs("")
        elif action == "query_scores":
            response = handle_scores("/scores lab-04")
        elif action == "query_top":
            response = route_intent("who are the top 5 students in lab 04")
        elif action == "query_completion":
            response = route_intent("what is the completion rate for lab 04")
        elif action == "query_groups":
            response = route_intent("show me group performance for lab 04")
        elif action == "query_sync":
            response = route_intent("sync the data")
        else:
            response = "Unknown action."

        await callback_query.message.answer(response)
        await callback_query.answer()

    @dp.message()
    async def handle_message(message: types.Message):
        """Handle natural language messages."""
        user_text = message.text or ""

        # Route through LLM intent router
        response = route_intent(user_text)
        await message.answer(response)

    # Start polling
    print("Telegram bot starting...")
    import asyncio
    asyncio.run(dp.start_polling(bot))


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="LMS Telegram Bot",
    )
    parser.add_argument(
        "--test",
        type=str,
        metavar="MESSAGE",
        help="Test mode: run a command or query and print response to stdout",
    )

    args = parser.parse_args()

    if args.test:
        run_test_mode(args.test)
    else:
        run_telegram_bot()


if __name__ == "__main__":
    main()
