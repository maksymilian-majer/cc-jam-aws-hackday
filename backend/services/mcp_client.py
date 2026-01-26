"""MCP client for Cronty notification scheduling."""

import logging
import os
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

logger = logging.getLogger(__name__)

# Notification topic for this app
NOTIFICATION_TOPIC = "maks-aws-hackday"


def get_mcp_client() -> Client:
    """Create an MCP client with bearer token authentication."""
    mcp_url = os.environ.get("CRONTY_MCP_URL")
    if not mcp_url:
        raise ValueError("CRONTY_MCP_URL environment variable is not set")

    token = os.environ.get("CRONTY_MCP_TOKEN")
    if not token:
        raise ValueError("CRONTY_MCP_TOKEN environment variable is not set")

    transport = StreamableHttpTransport(
        url=mcp_url,
        headers={"Authorization": f"Bearer {token}"},
    )
    return Client(transport)


async def schedule_event_notification(
    event_title: str,
    event_time: str,
    delay: str,
) -> dict[str, Any]:
    """Schedule a notification for an event.

    Args:
        event_title: Title of the event.
        event_time: When the event starts.
        delay: QStash delay format (e.g., "30s", "5m", "1h").

    Returns:
        Result from the MCP tool call.
    """
    message = f"🎉 Starting now: {event_title}\n⏰ {event_time}"

    try:
        client = get_mcp_client()
        async with client:
            result = await client.call_tool(
                "schedule_notification",
                {
                    "message": message,
                    "notification_topic": NOTIFICATION_TOPIC,
                    "delay": delay,
                },
            )
            logger.info(f"Scheduled notification: {result}")
            return {"success": True, "result": result.data if hasattr(result, 'data') else str(result)}
    except Exception as e:
        logger.error(f"Failed to schedule notification: {e}")
        return {"success": False, "error": str(e)}


async def send_immediate_notification(
    message: str,
    title: str | None = None,
) -> dict[str, Any]:
    """Send an immediate push notification.

    Args:
        message: Notification body text.
        title: Optional notification title.

    Returns:
        Result from the MCP tool call.
    """
    try:
        client = get_mcp_client()
        async with client:
            params: dict[str, Any] = {
                "message": message,
                "notification_topic": NOTIFICATION_TOPIC,
            }
            if title:
                params["title"] = title

            result = await client.call_tool("send_push_notification", params)
            logger.info(f"Sent notification: {result}")
            return {"success": True, "result": result.data if hasattr(result, 'data') else str(result)}
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        return {"success": False, "error": str(e)}


async def schedule_notification_at_time(
    message: str,
    date: str,
    time: str,
    timezone: str = "America/Los_Angeles",
) -> dict[str, Any]:
    """Schedule a notification for a specific date/time.

    Args:
        message: Notification body text.
        date: Date in YYYY-MM-DD format.
        time: Time in HH:MM format.
        timezone: IANA timezone (default: America/Los_Angeles for SF).

    Returns:
        Result from the MCP tool call.
    """
    try:
        client = get_mcp_client()
        async with client:
            result = await client.call_tool(
                "schedule_notification",
                {
                    "message": message,
                    "notification_topic": NOTIFICATION_TOPIC,
                    "date": date,
                    "time": time,
                    "timezone": timezone,
                },
            )
            logger.info(f"Scheduled notification: {result}")
            return {"success": True, "result": result.data if hasattr(result, 'data') else str(result)}
    except Exception as e:
        logger.error(f"Failed to schedule notification: {e}")
        return {"success": False, "error": str(e)}
