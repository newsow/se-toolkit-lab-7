"""LMS API client for fetching labs, scores, and health status.

This client uses Bearer token authentication to communicate with the LMS backend.
All errors are caught and returned as user-friendly messages that include the actual
error details for debugging.
"""

import httpx
from config import settings


class LMSClient:
    """Client for the LMS backend API."""

    def __init__(self) -> None:
        self.base_url = settings.lms_api_base_url
        self.api_key = settings.lms_api_key
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def health_check(self) -> str:
        """Check if the backend is healthy and return item count.

        Returns:
            User-friendly status message with error details if unhealthy.
        """
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/items/", headers=self.headers)
                response.raise_for_status()
                data = response.json()
                item_count = len(data) if isinstance(data, list) else "unknown"
                return f"Backend is healthy. {item_count} items available."
        except httpx.ConnectError as e:
            return f"Backend error: connection refused ({self.base_url}). Check that the services are running."
        except httpx.HTTPStatusError as e:
            return f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down."
        except httpx.RequestError as e:
            return f"Backend error: {str(e)}. Check your network and API settings."
        except Exception as e:
            return f"Backend error: {str(e)}"

    def get_labs(self) -> str:
        """Fetch and list available labs from the backend.

        Returns:
            Formatted list of labs or error message.
        """
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/items/", headers=self.headers)
                response.raise_for_status()
                data = response.json()

                if not data:
                    return "No labs available. The backend may still be syncing data."

                # Group items by lab
                labs_dict: dict[str, dict] = {}
                for item in data:
                    lab_id = item.get("lab_id", "unknown")
                    if lab_id not in labs_dict:
                        labs_dict[lab_id] = {
                            "name": item.get("lab_name", lab_id),
                            "tasks": [],
                        }
                    task_name = item.get("task_name", "Unknown task")
                    labs_dict[lab_id]["tasks"].append(task_name)

                # Format output
                lines = ["Available labs:"]
                for lab_id, lab_info in sorted(labs_dict.items()):
                    lines.append(f"- {lab_info['name']}")

                return "\n".join(lines)

        except httpx.ConnectError as e:
            return f"Backend error: connection refused ({self.base_url}). Check that the services are running."
        except httpx.HTTPStatusError as e:
            return f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down."
        except httpx.RequestError as e:
            return f"Backend error: {str(e)}"
        except Exception as e:
            return f"Backend error: {str(e)}"

    def get_scores(self, lab_name: str) -> str:
        """Fetch per-task pass rates for a specific lab.

        Args:
            lab_name: Lab identifier, e.g., "lab-04"

        Returns:
            Formatted scores with percentages or error message.
        """
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(
                    f"{self.base_url}/analytics/pass-rates",
                    params={"lab": lab_name},
                    headers=self.headers,
                )
                response.raise_for_status()
                data = response.json()

                if not data:
                    return f"No scores found for {lab_name}. The lab may not exist or data is not synced."

                # Format output
                lines = [f"Pass rates for {lab_name}:"]
                for entry in data:
                    task_name = entry.get("task_name", "Unknown task")
                    pass_rate = entry.get("pass_rate", 0)
                    attempts = entry.get("attempts", 0)
                    lines.append(f"- {task_name}: {pass_rate:.1f}% ({attempts} attempts)")

                return "\n".join(lines)

        except httpx.ConnectError as e:
            return f"Backend error: connection refused ({self.base_url}). Check that the services are running."
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"Lab '{lab_name}' not found. Use /labs to see available labs."
            return f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down."
        except httpx.RequestError as e:
            return f"Backend error: {str(e)}"
        except Exception as e:
            return f"Backend error: {str(e)}"
