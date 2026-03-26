"""Intent-based natural language router using LLM.

This module routes natural language queries to the appropriate backend tools
using an LLM. The LLM decides which tools to call based on the user's message.

When LLM is unavailable, falls back to keyword-based routing for basic queries.
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
    # Try LLM first
    llm = LLMClient()
    response = llm.route(message)

    # If LLM failed, use fallback routing
    if response.startswith("LLM error:"):
        return _fallback_route(message)

    return response


def _fallback_route(message: str) -> str:
    """Fallback routing when LLM is unavailable.

    Uses simple keyword matching to determine intent.
    This is a last resort - LLM should handle most queries.
    """
    msg_lower = message.lower()
    lms_client = LMSClient()

    # Multi-step comparison queries - check FIRST (most specific)
    if "lowest" in msg_lower or "highest" in msg_lower or "best" in msg_lower or "worst" in msg_lower:
        if "pass rate" in msg_lower or "score" in msg_lower or "rate" in msg_lower:
            labs_data = lms_client._get_fallback_items()
            unique_labs = list(set(item["lab_id"] for item in labs_data))
            
            results = []
            for lab_id in unique_labs:
                pass_rates = lms_client._get_fallback_pass_rates(lab_id)
                if pass_rates:
                    avg_rate = sum(pr["pass_rate"] for pr in pass_rates) / len(pass_rates)
                    results.append((lab_id, avg_rate))
            
            if results:
                if "lowest" in msg_lower or "worst" in msg_lower:
                    lowest = min(results, key=lambda x: x[1])
                    lab_name = next((item["lab_name"] for item in labs_data if item["lab_id"] == lowest[0]), lowest[0])
                    return f"Based on the data, {lab_name} has the lowest average pass rate at {lowest[1]:.1f}%."
                else:
                    highest = max(results, key=lambda x: x[1])
                    lab_name = next((item["lab_name"] for item in labs_data if item["lab_id"] == highest[0]), highest[0])
                    return f"Based on the data, {lab_name} has the highest average pass rate at {highest[1]:.1f}%."

    # Scores/pass rates queries - check before labs (more specific)
    if any(word in msg_lower for word in ["score", "pass rate", "percentage"]):
        # Try to extract lab number
        import re
        match = re.search(r"lab[- ]?(\d+)", msg_lower)
        if match:
            lab_num = match.group(1)
            lab_id = f"lab-{lab_num.zfill(2)}"
            # Call LMS client directly with lab_id
            return lms_client.get_scores(lab_id)
        return "Please specify which lab, e.g., 'show scores for lab 4'"

    # Groups queries - check before labs (more specific)
    if "group" in msg_lower:
        import re
        match = re.search(r"lab[- ]?(\d+)", msg_lower)
        lab_id = f"lab-{match.group(1).zfill(2)}" if match else "lab-04"
        data = lms_client._get_groups_raw(lab_id)
        lines = [f"Group performance in {lab_id}:"]
        for entry in sorted(data, key=lambda x: x.get("avg_score", 0), reverse=True):
            lines.append(f"- {entry.get('group', 'Unknown')}: {entry.get('avg_score', 0)}% ({entry.get('student_count', 0)} students)")
        return "\n".join(lines)

    # Students/learners queries - check before labs (more specific)
    if any(word in msg_lower for word in ["student", "learner", "enrolled", "how many"]):
        if "top" in msg_lower:
            # Top learners
            import re
            match = re.search(r"lab[- ]?(\d+)", msg_lower)
            lab_id = f"lab-{match.group(1).zfill(2)}" if match else "lab-04"
            match_limit = re.search(r"(\d+)", msg_lower)
            limit = int(match_limit.group(1)) if match_limit else 5
            data = lms_client._get_top_learners_raw(lab_id, limit)
            lines = [f"Top {limit} students in {lab_id}:"]
            for i, entry in enumerate(data, 1):
                lines.append(f"{i}. {entry.get('name', 'Unknown')}: {entry.get('score', 0)}%")
            return "\n".join(lines)
        else:
            # Total learners
            data = lms_client._get_learners_raw()
            return f"There are {len(data)} students enrolled."

    # Completion rate queries
    if "completion" in msg_lower or "complete" in msg_lower:
        import re
        match = re.search(r"lab[- ]?(\d+)", msg_lower)
        lab_id = f"lab-{match.group(1).zfill(2)}" if match else "lab-04"
        data = lms_client._get_completion_rate_raw(lab_id)
        rate = data.get("completion_rate", 0)
        completed = data.get("completed", 0)
        total = data.get("total", 0)
        return f"Completion rate for {lab_id}: {rate}% ({completed}/{total} students)"

    # Labs-related queries - check last (least specific)
    if any(word in msg_lower for word in ["lab", "labs", "available", "list"]):
        return lms_client.get_labs()

    # Health check
    if "health" in msg_lower or "status" in msg_lower or "working" in msg_lower:
        return lms_client.health_check()

    # Sync query
    if "sync" in msg_lower or "refresh" in msg_lower:
        data = lms_client._trigger_sync_raw()
        if "error" in data:
            return f"Sync failed: {data['error']}"
        return "Data sync triggered successfully."

    # Greeting
    if any(word in msg_lower for word in ["hello", "hi", "hey", "greetings"]):
        return "Hello! I can help you with information about labs, scores, students, and more. Try asking 'what labs are available?' or 'show me scores for lab 4'."

    # Default - help message
    return (
        "I'm here to help! Try asking:\n"
        "• what labs are available?\n"
        "• show me scores for lab 4\n"
        "• who are the top 5 students?\n"
        "• which group is doing best?\n"
        "• what is the completion rate?"
    )


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
