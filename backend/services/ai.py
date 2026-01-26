"""Claude AI service with tool calling for event discovery."""

import json
import logging
import os
from typing import Any

import anthropic

from backend.models import Event
from backend.services.mcp_client import (
    schedule_event_notification,
    send_immediate_notification,
)

logger = logging.getLogger(__name__)

# Message type for conversation history
MessageDict = dict[str, Any]

# Tool definitions for Claude
TOOLS = [
    {
        "name": "search_events",
        "description": "Search for events from all loaded scraper plugins. Use this whenever the user asks about events, wants to find activities, or is looking for things to do. Returns a list of events with titles, dates, times, locations, and URLs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Optional search query to filter events (e.g., 'afternoon tea', 'hackathon', 'AI meetup'). Leave empty to get all available events.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "create_plugin",
        "description": "Create a new scraper plugin to fetch events from a specific website. Use this when the user wants to add a new event source or asks to scrape events from a URL that isn't already supported.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the events page to create a scraper for (e.g., 'https://meetup.com/find/?location=sf').",
                }
            },
            "required": ["url"],
        },
    },
    {
        "name": "schedule_event_reminder",
        "description": "Schedule a push notification reminder for an event. Use this when the user wants to be notified or reminded about an event. The notification will be sent to their device at the specified time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_title": {
                    "type": "string",
                    "description": "The title of the event to remind about.",
                },
                "event_time": {
                    "type": "string",
                    "description": "When the event starts (e.g., '2:30 PM PST').",
                },
                "delay": {
                    "type": "string",
                    "description": "How long from now to send the notification. Format: QStash delay (e.g., '30s' for 30 seconds, '5m' for 5 minutes, '1h' for 1 hour, '1h30m' for 1.5 hours).",
                },
            },
            "required": ["event_title", "event_time", "delay"],
        },
    },
    {
        "name": "send_notification",
        "description": "Send an immediate push notification to the user's device. Use this for urgent alerts or when the user wants to test notifications.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The notification message body.",
                },
                "title": {
                    "type": "string",
                    "description": "Optional notification title.",
                },
            },
            "required": ["message"],
        },
    },
]

SYSTEM_PROMPT = """You are Schedule Hacker, an AI assistant that helps users discover events and set up reminders.

## Your Capabilities
You have access to tools that let you:
1. **search_events** - Search for events from loaded scraper plugins
2. **create_plugin** - Create new scraper plugins for event websites
3. **schedule_event_reminder** - Schedule a push notification for an upcoming event
4. **send_notification** - Send an immediate push notification

## When to Use Tools
- When users ask about events, activities, meetups, hackathons, conferences, parties, or anything happening - use search_events
- When users want to add a new event source or mention a website URL - use create_plugin
- When users want to be reminded about an event, get notified, or schedule an alert - use schedule_event_reminder
- When users want to test notifications or need an immediate alert - use send_notification

## Response Guidelines
When presenting events to users, ALWAYS include:
- **Event title** as a clickable markdown link: [Event Title](url)
- **Date and time** using the exact day name from the data (the "day" field tells you the correct day)
- **Location** if available
- Brief description of why this event matches their interests

Example format:
### [SF AI Builders Meetup](https://lu.ma/abc123)
📅 Monday, Jan 26 • 6:00 PM
📍 San Francisco, CA
Great for networking with AI enthusiasts and builders.

IMPORTANT: Use the "day" field from event data for the day name (e.g., "Monday", "Tuesday"). Never calculate or guess the day of week yourself.

## Notification Scheduling
When scheduling reminders:
- Calculate the delay based on how far in the future the event is
- Use delay format like "30s" (seconds), "5m" (minutes), "1h" (hours), or combinations like "1h30m"
- Confirm to the user when the notification has been scheduled and when they'll receive it
- If an event starts in 30 seconds, use delay="30s"

## Important
- Always use the search_events tool to get real event data - never make up events
- Include direct links so users can easily click to learn more
- If no events match, suggest using create_plugin to add new sources
- Be concise but informative
- Proactively offer to schedule reminders for events the user is interested in"""


def get_anthropic_client() -> anthropic.Anthropic:
    """Get the Anthropic client with API key from environment."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
    return anthropic.Anthropic(api_key=api_key)


def format_events_for_tool_response(events: list[Event]) -> str:
    """Format events as a structured response for the tool result."""
    if not events:
        return json.dumps({"events": [], "message": "No events found from current sources."})

    events_data = []
    for event in events:
        # Include both date and day name so the AI doesn't have to guess
        date_str = None
        day_name = None
        if event.date:
            date_str = event.date.strftime("%Y-%m-%d")
            day_name = event.date.strftime("%A")  # e.g., "Monday"

        event_dict = {
            "title": event.title,
            "url": event.url,
            "date": date_str,
            "day": day_name,
            "time": event.time,
            "location": event.location,
            "description": event.description,
            "source": event.source,
        }
        events_data.append(event_dict)

    return json.dumps({
        "events": events_data,
        "count": len(events_data),
        "message": f"Found {len(events_data)} events.",
    })


async def handle_tool_call(
    tool_name: str,
    tool_input: dict[str, Any],
    scrape_function: Any,
    create_plugin_function: Any,
) -> tuple[str, list[Event]]:
    """Handle a tool call and return the result.

    Args:
        tool_name: Name of the tool to call.
        tool_input: Input parameters for the tool.
        scrape_function: Async function to scrape events.
        create_plugin_function: Async function to create a plugin.

    Returns:
        Tuple of (tool result string, list of events if any).
    """
    events: list[Event] = []

    if tool_name == "search_events":
        query = tool_input.get("query")
        logger.info(f"Tool call: search_events(query={query})")
        events = await scrape_function(query=query)
        return format_events_for_tool_response(events), events

    elif tool_name == "create_plugin":
        url = tool_input.get("url", "")
        logger.info(f"Tool call: create_plugin(url={url})")
        result = await create_plugin_function(url)
        return json.dumps({"result": result}), []

    elif tool_name == "schedule_event_reminder":
        event_title = tool_input.get("event_title", "")
        event_time = tool_input.get("event_time", "")
        delay = tool_input.get("delay", "")
        logger.info(f"Tool call: schedule_event_reminder(title={event_title}, delay={delay})")
        result = await schedule_event_notification(event_title, event_time, delay)
        return json.dumps(result), []

    elif tool_name == "send_notification":
        message = tool_input.get("message", "")
        title = tool_input.get("title")
        logger.info(f"Tool call: send_notification(message={message[:50]}...)")
        result = await send_immediate_notification(message, title)
        return json.dumps(result), []

    else:
        logger.warning(f"Unknown tool: {tool_name}")
        return json.dumps({"error": f"Unknown tool: {tool_name}"}), []


async def chat_with_tools(
    message: str,
    conversation_history: list[MessageDict] | None = None,
    scrape_function: Any = None,
    create_plugin_function: Any = None,
) -> tuple[str, list[Event]]:
    """Send a message to Claude with tool calling support.

    Args:
        message: The user's message.
        conversation_history: Optional conversation history.
        scrape_function: Async function to scrape events.
        create_plugin_function: Async function to create plugins.

    Returns:
        Tuple of (AI response text, list of events).
    """
    try:
        client = get_anthropic_client()
        all_events: list[Event] = []

        # Build messages list
        messages: list[dict[str, Any]] = []
        if conversation_history:
            messages.extend(conversation_history)
            logger.info(f"Loaded {len(conversation_history)} messages from history")

        # Add current user message
        messages.append({"role": "user", "content": message})
        logger.info(f"Total messages being sent to Claude: {len(messages)}")

        # Agentic loop - keep processing until we get a final response
        max_iterations = 5
        for _ in range(max_iterations):
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            # Check if Claude wants to use a tool
            if response.stop_reason == "tool_use":
                # Process all tool uses in the response
                assistant_content = response.content
                messages.append({"role": "assistant", "content": assistant_content})

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_result, events = await handle_tool_call(
                            tool_name=block.name,
                            tool_input=block.input,
                            scrape_function=scrape_function,
                            create_plugin_function=create_plugin_function,
                        )
                        all_events.extend(events)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": tool_result,
                        })

                # Add tool results to messages
                messages.append({"role": "user", "content": tool_results})

            else:
                # Claude is done - extract final text response
                for block in response.content:
                    if hasattr(block, "text"):
                        return block.text, all_events

                return "I couldn't generate a response.", all_events

        logger.warning("Max iterations reached in tool calling loop")
        return "I encountered an issue processing your request. Please try again.", all_events

    except anthropic.AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise ValueError("Invalid ANTHROPIC_API_KEY") from e

    except anthropic.RateLimitError:
        return "I'm experiencing high demand. Please try again in a moment.", []

    except anthropic.APIError as e:
        logger.error(f"API error: {e}")
        return "I encountered an error. Please try again later.", []

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return f"I encountered an unexpected error: {e}", []


async def send_message(
    message: str,
    conversation_history: list[MessageDict] | None = None,
    system_prompt: str | None = None,
) -> str:
    """Send a simple message to Claude without tools.

    Args:
        message: The user's message.
        conversation_history: Optional conversation history.
        system_prompt: Optional system prompt.

    Returns:
        Claude's response text.
    """
    try:
        client = get_anthropic_client()

        messages: list[dict[str, Any]] = []
        if conversation_history:
            for msg in conversation_history:
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": message})

        request_kwargs: dict[str, Any] = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": messages,
        }

        if system_prompt:
            request_kwargs["system"] = system_prompt

        response = client.messages.create(**request_kwargs)

        if response.content:
            block = response.content[0]
            if hasattr(block, "text"):
                return block.text
            return str(block)

        return "I couldn't generate a response."

    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        return f"I encountered an error: {e}"
