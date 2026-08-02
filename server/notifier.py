"""
Webhook notification module for CanaryFile Engine.
Asynchronously sends alert notifications to Slack, Discord, or generic endpoints.
"""

import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("canaryfile.notifier")


class WebhookNotifier:
    """Sends webhook alerts when canary tokens are triggered."""

    def __init__(self, webhook_url: Optional[str] = None, platform: str = "generic", timeout: float = 5.0):
        self.webhook_url = webhook_url
        self.platform = platform.lower()
        self.timeout = timeout

    async def send_alert(self, hit_data: Dict[str, Any], token_metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send an asynchronous alert to configured webhook URL.
        Returns True if successful, False otherwise.
        """
        if not self.webhook_url:
            logger.info("Webhook alert skipped: No webhook URL configured.")
            return False

        payload = self._build_payload(hit_data, token_metadata)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                logger.info(f"Webhook alert dispatched successfully to {self.webhook_url}")
                return True
        except Exception as e:
            logger.error(f"Failed to dispatch webhook alert: {e}")
            return False

    def _build_payload(self, hit_data: Dict[str, Any], token_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format the payload depending on target platform (Slack, Discord, Generic)."""
        token_id = hit_data.get("token_id", "Unknown")
        src_ip = hit_data.get("src_ip", "Unknown IP")
        user_agent = hit_data.get("user_agent", "Unknown UA")
        timestamp = hit_data.get("timestamp", "")
        label = token_metadata.get("label", "N/A") if token_metadata else "N/A"
        file_type = token_metadata.get("file_type", "N/A") if token_metadata else "N/A"

        if self.platform == "discord":
            return {
                "embeds": [
                    {
                        "title": "🚨 CANARY TOKEN TRIGGERED!",
                        "color": 15158332,  # Red
                        "fields": [
                            {"name": "Token ID", "value": f"`{token_id}`", "inline": True},
                            {"name": "Label / Memo", "value": label, "inline": True},
                            {"name": "File Type", "value": file_type, "inline": True},
                            {"name": "Source IP", "value": f"`{src_ip}`", "inline": True},
                            {"name": "Timestamp", "value": timestamp, "inline": True},
                            {"name": "User Agent", "value": f"```{user_agent}```", "inline": False},
                        ],
                        "footer": {"text": "CanaryFile Engine Active Defense Alert"}
                    }
                ]
            }

        elif self.platform == "slack":
            return {
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": "🚨 Canary Token Triggered!", "emoji": True}
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Token ID:*\n`{token_id}`"},
                            {"type": "mrkdwn", "text": f"*Label:*\n{label}"},
                            {"type": "mrkdwn", "text": f"*Source IP:*\n`{src_ip}`"},
                            {"type": "mrkdwn", "text": f"*File Type:*\n{file_type}"},
                            {"type": "mrkdwn", "text": f"*Timestamp:*\n{timestamp}"}
                        ]
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*User Agent:*\n```{user_agent}```"}
                    }
                ]
            }

        else:
            # Generic HTTP JSON Webhook
            return {
                "event": "canary_token_triggered",
                "token_id": token_id,
                "label": label,
                "file_type": file_type,
                "source_ip": src_ip,
                "user_agent": user_agent,
                "timestamp": timestamp,
                "request_method": hit_data.get("request_method", "GET"),
                "query_params": hit_data.get("query_params", "")
            }
