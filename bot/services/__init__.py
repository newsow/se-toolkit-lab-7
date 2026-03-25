"""Services for the LMS Telegram bot.

Services handle external API communication (LMS backend, LLM, etc.).
"""

from .lms_client import LMSClient

__all__ = ["LMSClient"]
