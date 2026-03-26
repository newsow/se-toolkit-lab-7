"""Intent-based natural language router using LLM."""

from services.llm_client import LLMClient

def route_intent(message: str) -> str:
    """Route a natural language message through the LLM.
    The LLM decides which tools to call based on the user's message.
    """
    llm = LLMClient()
    return llm.route(message)

def get_inline_keyboard() -> list[list[dict]]:
    """Get inline keyboard buttons for common queries."""
    return [
        [
            {"text": "📚 Labs", "callback_data": "query_labs"},
            {"text": "📊 Scores", "callback_data": "query_scores"},
        ],
        [
            {"text": "👥 Top Students", "callback_data": "query_top"},
            {"text": "📈 Completion", "callback_data": "query_completion"},
        ],
        [
            {"text": "🏆 Groups", "callback_data": "query_groups"},
            {"text": "🔄 Sync Data", "callback_data": "query_sync"},
        ],
    ]
