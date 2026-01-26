"""Chat service for managing conversations and AI interactions."""

import asyncio
import logging
import uuid
from typing import Any

from backend.models import Event
from backend.services.ai import MessageDict, chat_with_context, send_message
from backend.services.plugin_loader import get_plugin_registry

logger = logging.getLogger(__name__)

# In-memory storage for conversations
# Maps conversation_id -> list of messages
_conversations: dict[str, list[MessageDict]] = {}

# Keywords that indicate user is asking for events
EVENT_SEARCH_KEYWORDS = [
    "find",
    "search",
    "events",
    "hackathons",
    "meetups",
    "conferences",
    "workshops",
    "looking for",
    "show me",
    "what's happening",
    "happening",
    "recommend",
    "suggestions",
]


def is_event_search_request(message: str) -> bool:
    """Check if a message is requesting event search.

    Args:
        message: The user's message.

    Returns:
        True if the message appears to be asking for events.
    """
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in EVENT_SEARCH_KEYWORDS)


async def scrape_all_plugins() -> list[Event]:
    """Scrape events from all loaded plugins concurrently.

    Returns:
        Combined list of events from all plugins.
    """
    registry = get_plugin_registry()
    if not registry:
        logger.warning("No plugins loaded in registry")
        return []

    # Create plugin instances and scrape concurrently
    scrape_tasks = []
    for plugin_class in registry.values():
        plugin_instance = plugin_class()
        scrape_tasks.append(plugin_instance.scrape())

    # Run all scrapes concurrently
    results = await asyncio.gather(*scrape_tasks, return_exceptions=True)

    # Collect all events, logging any errors
    all_events: list[Event] = []
    for plugin_name, result in zip(registry.keys(), results):
        if isinstance(result, Exception):
            logger.error(f"Error scraping {plugin_name}: {result}")
        elif isinstance(result, list):
            all_events.extend(result)
            logger.info(f"Scraped {len(result)} events from {plugin_name}")

    return all_events


def format_events_for_context(events: list[Event]) -> str:
    """Format events as context for Claude prompt.

    Args:
        events: List of events to format.

    Returns:
        Formatted string describing events for AI context.
    """
    if not events:
        return "No events are currently available."

    event_descriptions = []
    for event in events:
        parts = [f"- **{event.title}**"]
        if event.date:
            parts.append(f"  Date: {event.date.strftime('%Y-%m-%d')}")
        if event.time:
            parts.append(f"  Time: {event.time}")
        if event.location:
            parts.append(f"  Location: {event.location}")
        if event.description:
            parts.append(f"  Description: {event.description}")
        parts.append(f"  Source: {event.source}")
        parts.append(f"  URL: {event.url}")
        if event.tags:
            parts.append(f"  Tags: {', '.join(event.tags)}")
        event_descriptions.append("\n".join(parts))

    return f"Available events ({len(events)} total):\n\n" + "\n\n".join(event_descriptions)


async def search_and_recommend_events(
    user_message: str,
    conversation_history: list[MessageDict] | None = None,
) -> str:
    """Search for events and get AI recommendations based on user interests.

    Args:
        user_message: The user's message describing what they're looking for.
        conversation_history: Optional conversation history for context.

    Returns:
        AI response with ranked and recommended events.
    """
    # Scrape all plugins concurrently
    events = await scrape_all_plugins()

    if not events:
        return "No matching events found. There are currently no events available from our sources. Please try again later or ask me to create a plugin for a specific event source."

    # Format events as context
    events_context = format_events_for_context(events)

    # Build system prompt for event recommendation
    system_prompt = """You are an AI assistant for EventFinder that helps users discover events matching their interests.

You have access to a list of available events. Your job is to:
1. Understand what the user is looking for based on their message and conversation history
2. Rank the events by relevance to their interests
3. Recommend the most relevant events with explanations of why each matches their interests
4. Include clickable URLs for each recommended event

Format your response clearly with:
- A brief acknowledgment of what they're looking for
- Top recommended events (up to 5 most relevant)
- For each event: title, date/time, location, why it matches their interests, and the URL

If no events match their specific interests, suggest the closest matches or let them know no matching events were found.

Here are the available events:

""" + events_context

    # Get AI recommendation
    response = await send_message(
        message=user_message,
        conversation_history=conversation_history,
        system_prompt=system_prompt,
    )

    return response


def get_or_create_conversation(conversation_id: str | None) -> tuple[str, list[MessageDict]]:
    """Get an existing conversation or create a new one.

    Args:
        conversation_id: Optional existing conversation ID.

    Returns:
        Tuple of (conversation_id, messages list).
    """
    if conversation_id and conversation_id in _conversations:
        return conversation_id, _conversations[conversation_id]

    # Generate new conversation ID
    new_id = str(uuid.uuid4())
    _conversations[new_id] = []
    return new_id, _conversations[new_id]


async def process_chat_message(
    message: str,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    """Process a chat message and return AI response.

    Args:
        message: The user's message.
        conversation_id: Optional conversation ID for continuing a conversation.

    Returns:
        Dict with 'response' (AI response text) and 'conversation_id'.
    """
    # Get or create conversation
    conv_id, messages = get_or_create_conversation(conversation_id)

    # Check if this is an event search request
    if is_event_search_request(message):
        # Use event search and recommendation
        response = await search_and_recommend_events(
            user_message=message,
            conversation_history=messages if messages else None,
        )
    else:
        # Regular chat - use standard AI conversation
        response = await chat_with_context(
            message=message,
            conversation_history=messages if messages else None,
        )

    # Store the user message and AI response in conversation history
    messages.append({"role": "user", "content": message})
    messages.append({"role": "assistant", "content": response})

    return {
        "response": response,
        "conversation_id": conv_id,
    }


def get_conversation(conversation_id: str) -> list[MessageDict] | None:
    """Get a conversation by ID.

    Args:
        conversation_id: The conversation ID.

    Returns:
        List of messages or None if not found.
    """
    return _conversations.get(conversation_id)


def clear_conversation(conversation_id: str) -> bool:
    """Clear a conversation by ID.

    Args:
        conversation_id: The conversation ID.

    Returns:
        True if conversation was cleared, False if not found.
    """
    if conversation_id in _conversations:
        del _conversations[conversation_id]
        return True
    return False
