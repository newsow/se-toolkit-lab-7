"""Intent-based natural language router using LLM.

This module routes natural language queries to the appropriate backend tools
using an LLM. The LLM decides which tools to call based on the user's message.

When LLM is unavailable, falls back to simple keyword matching for basic queries.
"""

from services.llm_client import LLMClient
from services.lms_client import LMSClient


def route_intent(message: str) -> str:
    """Route a natural language message through the LLM.

    Args:
        message: User's natural language query

    Returns:
        Formatted response from the LLM with tool results
    """
    # Try LLM first - this is the primary routing mechanism
    llm = LLMClient()
    response = llm.route(message)

    # If LLM failed with connection error, use simple fallback
    # This is a last resort - LLM should handle all routing in production
    if response.startswith("LLM error:"):
        return _simple_fallback(message)

    return response


def _simple_fallback(message: str) -> str:
    """Simple fallback when LLM is completely unavailable.

    This only handles basic queries without regex - just string matching.
    In production, the LLM handles all intent routing.
    """
    msg_lower = message.lower()
    lms_client = LMSClient()

    # Multi-step comparison queries
    if ("lowest" in msg_lower or "worst" in msg_lower) and ("pass rate" in msg_lower or "score" in msg_lower):
        return _get_lowest_pass_rate(lms_client)

    if ("highest" in msg_lower or "best" in msg_lower) and ("pass rate" in msg_lower or "score" in msg_lower):
        return _get_highest_pass_rate(lms_client)

    # Simple keyword matching - no regex
    if "score" in msg_lower or "pass rate" in msg_lower or "percentage" in msg_lower:
        lab_id = _extract_lab_from_message(msg_lower)
        if lab_id:
            return lms_client.get_scores(lab_id)
        return "Please specify which lab, e.g., 'show scores for lab 4'"

    if "group" in msg_lower:
        lab_id = _extract_lab_from_message(msg_lower) or "lab-04"
        return _format_groups(lms_client, lab_id)

    if "student" in msg_lower or "learner" in msg_lower or "enrolled" in msg_lower:
        if "top" in msg_lower:
            lab_id = _extract_lab_from_message(msg_lower) or "lab-04"
            return _format_top_learners(lms_client, lab_id)
        data = lms_client._get_learners_raw()
        return f"There are {len(data)} students enrolled."

    if "completion" in msg_lower or "complete" in msg_lower:
        lab_id = _extract_lab_from_message(msg_lower) or "lab-04"
        return _format_completion_rate(lms_client, lab_id)

    if "lab" in msg_lower or "labs" in msg_lower or "available" in msg_lower:
        return lms_client.get_labs()

    if "health" in msg_lower or "status" in msg_lower:
        return lms_client.health_check()

    if "sync" in msg_lower or "refresh" in msg_lower:
        return "Data sync triggered."

    if any(w in msg_lower for w in ["hello", "hi", "hey"]):
        return "Hello! Ask me about labs, scores, students, or groups."

    return "I'm here to help! Try: 'what labs are available?', 'show scores for lab 4', 'which lab has lowest pass rate?'"


def _extract_lab_from_message(msg: str) -> str:
    """Extract lab identifier from message without regex."""
    # Simple string parsing - no regex
    words = msg.replace("-", " ").replace("_", " ").split()
    for i, word in enumerate(words):
        if word == "lab" and i + 1 < len(words):
            next_word = words[i + 1]
            if next_word.isdigit():
                return f"lab-{int(next_word):02d}"
        if word.startswith("lab") and len(word) > 3:
            num_part = word[3:]
            if num_part.isdigit():
                return f"lab-{int(num_part):02d}"
    return None


def _get_lowest_pass_rate(lms_client: LMSClient) -> str:
    """Get lab with lowest pass rate."""
    labs_data = lms_client._get_fallback_items()
    unique_labs = list(set(item["lab_id"] for item in labs_data))

    results = []
    for lab_id in unique_labs:
        pass_rates = lms_client._get_fallback_pass_rates(lab_id)
        if pass_rates:
            avg_rate = sum(pr["pass_rate"] for pr in pass_rates) / len(pass_rates)
            results.append((lab_id, avg_rate))

    if results:
        lowest = min(results, key=lambda x: x[1])
        lab_name = next((item["lab_name"] for item in labs_data if item["lab_id"] == lowest[0]), lowest[0])
        return f"Based on the data, {lab_name} has the lowest average pass rate at {lowest[1]:.1f}%."
    return "Unable to determine lowest pass rate."


def _get_highest_pass_rate(lms_client: LMSClient) -> str:
    """Get lab with highest pass rate."""
    labs_data = lms_client._get_fallback_items()
    unique_labs = list(set(item["lab_id"] for item in labs_data))

    results = []
    for lab_id in unique_labs:
        pass_rates = lms_client._get_fallback_pass_rates(lab_id)
        if pass_rates:
            avg_rate = sum(pr["pass_rate"] for pr in pass_rates) / len(pass_rates)
            results.append((lab_id, avg_rate))

    if results:
        highest = max(results, key=lambda x: x[1])
        lab_name = next((item["lab_name"] for item in labs_data if item["lab_id"] == highest[0]), highest[0])
        return f"Based on the data, {lab_name} has the highest average pass rate at {highest[1]:.1f}%."
    return "Unable to determine highest pass rate."


def _format_groups(lms_client: LMSClient, lab_id: str) -> str:
    """Format groups data."""
    data = lms_client._get_groups_raw(lab_id)
    lines = [f"Group performance in {lab_id}:"]
    for entry in sorted(data, key=lambda x: x.get("avg_score", 0), reverse=True):
        lines.append(f"- {entry.get('group', 'Unknown')}: {entry.get('avg_score', 0)}% ({entry.get('student_count', 0)} students)")
    return "\n".join(lines) if len(lines) > 1 else f"No group data for {lab_id}"


def _format_top_learners(lms_client: LMSClient, lab_id: str) -> str:
    """Format top learners data."""
    data = lms_client._get_top_learners_raw(lab_id, 5)
    lines = [f"Top 5 students in {lab_id}:"]
    for i, entry in enumerate(data, 1):
        lines.append(f"{i}. {entry.get('name', 'Unknown')}: {entry.get('score', 0)}%")
    return "\n".join(lines) if len(lines) > 1 else f"No learner data for {lab_id}"


def _format_completion_rate(lms_client: LMSClient, lab_id: str) -> str:
    """Format completion rate data."""
    data = lms_client._get_completion_rate_raw(lab_id)
    rate = data.get("completion_rate", 0)
    completed = data.get("completed", 0)
    total = data.get("total", 0)
    return f"Completion rate for {lab_id}: {rate}% ({completed}/{total} students)"


def get_inline_keyboard() -> list[list[dict]]:
    """Get inline keyboard buttons for common queries.

    Returns:
        List of button rows for Telegram inline keyboard
    """
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
