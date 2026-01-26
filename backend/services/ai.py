"""Claude AI service with tool calling for event discovery."""

import json
import logging
import os
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import anthropic

from backend.models import Event
from backend.services.mcp_client import (
    schedule_event_notification,
    send_immediate_notification,
)

logger = logging.getLogger(__name__)

# San Francisco timezone
SF_TZ = ZoneInfo("America/Los_Angeles")

# Message type for conversation history
MessageDict = dict[str, Any]

# Tool definitions for Claude
TOOLS = [
    {
        "name": "search_events",
        "description": "Search for events from all loaded scraper plugins. Use this whenever the user asks about events, wants to find activities, or is looking for things to do. Returns a list of events with IDs, titles, dates, times, locations, and URLs. After searching, use display_events to select which events to show as cards.",
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
        "name": "display_events",
        "description": "Select which events to display as interactive cards to the user. Call this after search_events to show only the most relevant events. Only display events that match what the user is looking for.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of event IDs to display as cards. Only include the most relevant events (usually 3-5).",
                },
            },
            "required": ["event_ids"],
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

SYSTEM_PROMPT_TEMPLATE = """You are Schedule Hacker, an AI assistant that helps users discover events and set up reminders.

## Current Date and Time
Today is {current_date} ({current_day}). Use this to correctly interpret relative dates like "this weekend", "next week", "tomorrow", etc.

## Your Capabilities
You have access to tools that let you:
1. **search_events** - Search for events from loaded scraper plugins
2. **display_events** - Select which events to show as interactive cards (use after search_events)
3. **create_plugin** - Create new scraper plugins for event websites
4. **schedule_event_reminder** - Schedule a push notification for an upcoming event
5. **send_notification** - Send an immediate push notification

## When to Use Tools
- When users ask about events, activities, meetups, hackathons, conferences, parties, or anything happening - use search_events, then display_events
- IMPORTANT: After search_events, ALWAYS call display_events with the IDs of only the most relevant events (3-5 events max)
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

## Event Selection
When selecting events to display with display_events:
- STRICTLY filter by the user's criteria - do not include events that don't match
- "this weekend" means ONLY Saturday and Sunday - never include Thursday, Friday, or Monday
- "next week" means Monday through Sunday of the following week
- Only select events that match BOTH the topic AND the date range
- Limit to 3-5 most relevant events that actually match
- If no events match the criteria, call display_events with an empty list and explain in your response
- DO NOT show events outside the requested date range just to have something to display

## Notification Scheduling
When scheduling reminders:
- Calculate the delay based on how far in the future the event is
- Use delay format like "30s" (seconds), "5m" (minutes), "1h" (hours), or combinations like "1h30m"
- Confirm to the user when the notification has been scheduled and when they'll receive it
- If an event starts in 30 seconds, use delay="30s"

## Important
- Always use the search_events tool to get real event data - never make up events
- Always use display_events after search_events to select relevant events
- Include direct links so users can easily click to learn more
- If no events match, suggest using create_plugin to add new sources
- Be concise but informative
- Proactively offer to schedule reminders for events the user is interested in"""


def get_system_prompt() -> str:
    """Get the system prompt with current date/time."""
    now = datetime.now(SF_TZ)
    current_date = now.strftime("%B %d, %Y")  # e.g., "January 26, 2026"
    current_day = now.strftime("%A")  # e.g., "Monday"
    return SYSTEM_PROMPT_TEMPLATE.format(
        current_date=current_date,
        current_day=current_day,
    )


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
            "id": event.id,  # Include ID so Claude can select events
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
        "message": f"Found {len(events_data)} events. Use display_events with the IDs of relevant events to show them as cards.",
    })


async def handle_tool_call(
    tool_name: str,
    tool_input: dict[str, Any],
    scrape_function: Any,
    create_plugin_function: Any,
    all_events: list[Event] | None = None,
) -> tuple[str, list[Event], list[str] | None]:
    """Handle a tool call and return the result.

    Args:
        tool_name: Name of the tool to call.
        tool_input: Input parameters for the tool.
        scrape_function: Async function to scrape events.
        create_plugin_function: Async function to create a plugin.
        all_events: List of all events from previous search (for display_events).

    Returns:
        Tuple of (tool result string, list of events if any, selected event IDs if any).
    """
    events: list[Event] = []
    selected_ids: list[str] | None = None

    if tool_name == "search_events":
        query = tool_input.get("query")
        logger.info(f"Tool call: search_events(query={query})")
        events = await scrape_function(query=query)
        return format_events_for_tool_response(events), events, None

    elif tool_name == "display_events":
        event_ids = tool_input.get("event_ids", [])
        logger.info(f"Tool call: display_events(ids={event_ids})")
        selected_ids = event_ids
        return json.dumps({"success": True, "selected_count": len(event_ids)}), [], selected_ids

    elif tool_name == "create_plugin":
        url = tool_input.get("url", "")
        logger.info(f"Tool call: create_plugin(url={url})")
        result = await create_plugin_function(url)
        return json.dumps({"result": result}), [], None

    elif tool_name == "schedule_event_reminder":
        event_title = tool_input.get("event_title", "")
        event_time = tool_input.get("event_time", "")
        delay = tool_input.get("delay", "")
        logger.info(f"Tool call: schedule_event_reminder(title={event_title}, delay={delay})")
        result = await schedule_event_notification(event_title, event_time, delay)
        return json.dumps(result), [], None

    elif tool_name == "send_notification":
        message = tool_input.get("message", "")
        title = tool_input.get("title")
        logger.info(f"Tool call: send_notification(message={message[:50]}...)")
        result = await send_immediate_notification(message, title)
        return json.dumps(result), [], None

    else:
        logger.warning(f"Unknown tool: {tool_name}")
        return json.dumps({"error": f"Unknown tool: {tool_name}"}), [], None


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
        selected_event_ids: set[str] = set()

        # Build messages list
        messages: list[dict[str, Any]] = []
        if conversation_history:
            messages.extend(conversation_history)
            logger.info(f"Loaded {len(conversation_history)} messages from history")

        # Add current user message
        messages.append({"role": "user", "content": message})
        logger.info(f"Total messages being sent to Claude: {len(messages)}")

        # Agentic loop - keep processing until we get a final response
        max_iterations = 10  # Increased to allow for search + display calls
        for _ in range(max_iterations):
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=get_system_prompt(),
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
                        tool_result, events, selected_ids = await handle_tool_call(
                            tool_name=block.name,
                            tool_input=block.input,
                            scrape_function=scrape_function,
                            create_plugin_function=create_plugin_function,
                            all_events=all_events,
                        )
                        all_events.extend(events)
                        if selected_ids:
                            selected_event_ids.update(selected_ids)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": tool_result,
                        })

                # Add tool results to messages
                messages.append({"role": "user", "content": tool_results})

            else:
                # Claude is done - extract final text response
                # Filter events to only include selected ones
                if selected_event_ids:
                    filtered_events = [e for e in all_events if e.id in selected_event_ids]
                    logger.info(f"Filtered to {len(filtered_events)} selected events from {len(all_events)} total")
                else:
                    filtered_events = []  # No events selected = no cards shown

                for block in response.content:
                    if hasattr(block, "text"):
                        return block.text, filtered_events

                return "I couldn't generate a response.", filtered_events

        logger.warning("Max iterations reached in tool calling loop")
        # Filter events even if we hit max iterations
        if selected_event_ids:
            filtered_events = [e for e in all_events if e.id in selected_event_ids]
        else:
            filtered_events = []
        return "I encountered an issue processing your request. Please try again.", filtered_events

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
