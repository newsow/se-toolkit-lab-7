"""LLM client with tool calling for intent-based routing.

This client wraps the OpenAI-compatible API and provides tool definitions
for all 9 backend endpoints. The LLM decides which tools to call based
on the user's natural language query.
"""

import json
import sys
from typing import Any

from openai import OpenAI

from config import settings
from services.lms_client import LMSClient


class LLMClient:
    """LLM client with tool calling support."""

    def __init__(self) -> None:
        self.client = OpenAI(
            base_url=settings.llm_api_base_url,
            api_key=settings.llm_api_key,
        )
        self.model = settings.llm_api_model
        self.lms_client = LMSClient()

        # Define all 9 backend endpoints as LLM tools
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_items",
                    "description": "Get list of all labs and tasks available in the system",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_learners",
                    "description": "Get list of enrolled students and their groups",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_scores",
                    "description": "Get score distribution (4 buckets) for a specific lab",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_pass_rates",
                    "description": "Get per-task average pass rates and attempt counts for a lab",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_timeline",
                    "description": "Get submission timeline (submissions per day) for a lab",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_groups",
                    "description": "Get per-group performance scores and student counts for a lab",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_top_learners",
                    "description": "Get top N learners by score for a specific lab",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of top learners to return, e.g., 5, 10",
                            },
                        },
                        "required": ["lab", "limit"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_completion_rate",
                    "description": "Get completion rate percentage for a specific lab",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g., 'lab-01', 'lab-04'",
                            }
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "trigger_sync",
                    "description": "Trigger ETL sync to refresh data from the autochecker",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
        ]

        # System prompt for the LLM
        self.system_prompt = """You are an assistant for an LMS (Learning Management System). 
You have access to backend tools that provide data about labs, students, scores, and analytics.

When the user asks a question, use the available tools to fetch the data and provide a helpful answer.
Always call the tools first, then use the results to answer the user's question.

Available capabilities:
- List available labs and tasks
- Show pass rates and scores for specific labs
- Compare group performance
- Find top learners
- Check completion rates
- View submission timelines

If the user asks about a lab without specifying which one, ask for clarification or show all labs.
If the user's message is unclear or seems like gibberish, provide a helpful response explaining what you can do.
"""

    def _execute_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool and return the result as a string.

        Args:
            name: Tool name (e.g., 'get_items', 'get_pass_rates')
            arguments: Tool arguments as a dictionary

        Returns:
            Tool result as a formatted string
        """
        try:
            if name == "get_items":
                # Call backend directly to get real data
                data = self.lms_client._get_items_raw()
                return json.dumps(data, ensure_ascii=False)

            elif name == "get_learners":
                data = self.lms_client._get_learners_raw()
                return json.dumps(data, ensure_ascii=False)

            elif name == "get_scores":
                lab = arguments.get("lab", "")
                data = self.lms_client._get_scores_raw(lab)
                return json.dumps(data, ensure_ascii=False)

            elif name == "get_pass_rates":
                lab = arguments.get("lab", "")
                data = self.lms_client._get_pass_rates_raw(lab)
                return json.dumps(data, ensure_ascii=False)

            elif name == "get_timeline":
                lab = arguments.get("lab", "")
                data = self.lms_client._get_timeline_raw(lab)
                return json.dumps(data, ensure_ascii=False)

            elif name == "get_groups":
                lab = arguments.get("lab", "")
                data = self.lms_client._get_groups_raw(lab)
                return json.dumps(data, ensure_ascii=False)

            elif name == "get_top_learners":
                lab = arguments.get("lab", "")
                limit = arguments.get("limit", 5)
                data = self.lms_client._get_top_learners_raw(lab, limit)
                return json.dumps(data, ensure_ascii=False)

            elif name == "get_completion_rate":
                lab = arguments.get("lab", "")
                data = self.lms_client._get_completion_rate_raw(lab)
                return json.dumps(data, ensure_ascii=False)

            elif name == "trigger_sync":
                data = self.lms_client._trigger_sync_raw()
                return json.dumps(data, ensure_ascii=False)

            else:
                return f"Unknown tool: {name}"

        except Exception as e:
            return f"Error executing {name}: {str(e)}"

    def route(self, user_message: str) -> str:
        """Route a user message through the LLM with tool calling.

        Args:
            user_message: The user's natural language query

        Returns:
            Formatted response from the LLM
        """
        # Initialize conversation with system prompt and user message
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]

        max_iterations = 5  # Prevent infinite loops
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            try:
                # Call LLM with tools
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                )

                assistant_message = response.choices[0].message

                # Check if LLM wants to call tools
                if assistant_message.tool_calls:
                    # Execute each tool call
                    tool_results = []
                    for tool_call in assistant_message.tool_calls:
                        func_name = tool_call.function.name
                        func_args = json.loads(tool_call.function.arguments)

                        # Debug output to stderr
                        print(
                            f"[tool] LLM called: {func_name}({func_args})",
                            file=sys.stderr,
                        )

                        # Execute the tool
                        result = self._execute_tool(func_name, func_args)
                        tool_results.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": func_name,
                                "content": result,
                            }
                        )

                        # Debug output
                        preview = result[:100] + "..." if len(result) > 100 else result
                        print(f"[tool] Result: {preview}", file=sys.stderr)

                    # Add assistant message and tool results to conversation
                    messages.append(assistant_message)
                    for tool_result in tool_results:
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_result["tool_call_id"],
                                "content": tool_result["content"],
                            }
                        )

                    print(
                        f"[summary] Feeding {len(tool_results)} tool result(s) back to LLM",
                        file=sys.stderr,
                    )

                    # Continue the loop - LLM will now see tool results and respond
                    continue

                else:
                    # No tool calls - LLM has the final answer
                    final_response = assistant_message.content
                    return final_response or "I'm not sure how to help with that. Try asking about labs, scores, or students."

            except Exception as e:
                return f"LLM error: {str(e)}"

        return "I had trouble processing your request. Please try rephrasing your question."
