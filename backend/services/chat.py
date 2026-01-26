"""Chat service for managing conversations and AI interactions."""

import asyncio
import logging
import re
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler

from backend.models import Event
from backend.services.ai import MessageDict, chat_with_context, send_message
from backend.services.plugin_loader import (
    get_plugin_registry,
    get_plugins_directory,
    load_plugin_from_file,
    reload_plugins,
)

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

# Patterns that indicate user wants to create a plugin
PLUGIN_CREATION_PATTERNS = [
    r"create\s+(?:a\s+)?plugin\s+for\s+(\S+)",
    r"make\s+(?:a\s+)?plugin\s+for\s+(\S+)",
    r"generate\s+(?:a\s+)?plugin\s+for\s+(\S+)",
    r"build\s+(?:a\s+)?plugin\s+for\s+(\S+)",
    r"add\s+(?:a\s+)?scraper\s+for\s+(\S+)",
    r"create\s+(?:a\s+)?scraper\s+for\s+(\S+)",
    r"scrape\s+(\S+)",
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
) -> tuple[str, list[Event]]:
    """Search for events and get AI recommendations based on user interests.

    Args:
        user_message: The user's message describing what they're looking for.
        conversation_history: Optional conversation history for context.

    Returns:
        Tuple of (AI response with recommendations, list of scraped events).
    """
    # Scrape all plugins concurrently
    events = await scrape_all_plugins()

    if not events:
        return (
            "No matching events found. There are currently no events available from our sources. Please try again later or ask me to create a plugin for a specific event source.",
            [],
        )

    # Format events as context
    events_context = format_events_for_context(events)

    # Build system prompt for event recommendation
    system_prompt = """You are an AI assistant for EventFinder that helps users discover events matching their interests.

You have access to a list of available events. Your job is to:
1. Understand what the user is looking for based on their message and conversation history
2. Rank the events by relevance to their interests
3. Recommend the most relevant events with explanations of why each matches their interests

Format your response clearly with:
- A brief acknowledgment of what they're looking for
- Commentary on the top recommended events (up to 5 most relevant)
- For each event: explain why it matches their interests

Note: The event cards with details (title, date, location, link) will be displayed separately below your response, so focus on providing valuable context about why each event is a good match.

If no events match their specific interests, suggest the closest matches or let them know no matching events were found.

Here are the available events:

""" + events_context

    # Get AI recommendation
    response = await send_message(
        message=user_message,
        conversation_history=conversation_history,
        system_prompt=system_prompt,
    )

    return response, events


def is_plugin_creation_request(message: str) -> tuple[bool, str | None]:
    """Check if a message is requesting plugin creation.

    Args:
        message: The user's message.

    Returns:
        Tuple of (is_plugin_request, extracted_url).
    """
    message_lower = message.lower()
    for pattern in PLUGIN_CREATION_PATTERNS:
        match = re.search(pattern, message_lower)
        if match:
            url = match.group(1)
            # Ensure URL has a scheme
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            return True, url
    return False, None


def extract_domain_name(url: str) -> str:
    """Extract a clean domain name for use as a plugin filename.

    Args:
        url: The URL to extract domain from.

    Returns:
        Clean domain name suitable for a filename.
    """
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split("/")[0]
    # Remove www. prefix
    if domain.startswith("www."):
        domain = domain[4:]
    # Replace dots and hyphens with underscores
    clean_name = re.sub(r"[.\-]", "_", domain)
    # Remove any non-alphanumeric characters except underscores
    clean_name = re.sub(r"[^a-z0-9_]", "", clean_name.lower())
    return clean_name


async def crawl_url_for_structure(url: str) -> str:
    """Crawl a URL to get its page structure for plugin generation.

    Args:
        url: The URL to crawl.

    Returns:
        Markdown representation of the page content.
    """
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        return result.markdown


def get_plugin_template() -> str:
    """Get the plugin template with instructions for Claude.

    Returns:
        Template string with instructions and example code.
    """
    return '''You are generating a Python scraper plugin for EventFinder.

The plugin MUST follow this exact interface:

```python
"""[Domain] event scraper plugin."""

import logging
import re
import uuid
from datetime import datetime

from backend.models import Event
from backend.plugins.base import ScraperPlugin

logger = logging.getLogger(__name__)


class [Name]Plugin(ScraperPlugin):
    """Scraper plugin for [domain] events."""

    name = "[Name]"
    source_url = "[url]"
    description = "Scrapes events from [domain]"

    async def scrape(self) -> list[Event]:
        """Scrape events from the source.

        Returns:
            List of Event objects scraped from the source.
            Returns empty list on error.
        """
        try:
            markdown = await self.crawl(self.source_url)
            return self._parse_events(markdown)
        except Exception as e:
            logger.error(f"Error scraping events: {e}")
            return []

    def _parse_events(self, markdown: str) -> list[Event]:
        """Parse event data from markdown content.

        Args:
            markdown: Markdown content from crawled page.

        Returns:
            List of Event objects parsed from content.
        """
        events: list[Event] = []
        # TODO: Implement parsing logic based on page structure
        # Look for event titles, dates, times, locations, and URLs
        # Use regex patterns to extract data from markdown

        # Example pattern for extracting events:
        # lines = markdown.split("\\n")
        # for line in lines:
        #     if event_pattern_match:
        #         events.append(Event(...))

        return events

    def _create_event(self, title: str, url: str, date_str: str | None = None,
                      time_str: str | None = None, location: str | None = None,
                      description: str | None = None) -> Event:
        """Create an Event object from parsed data.

        Args:
            title: Event title.
            url: Event URL.
            date_str: Optional date string.
            time_str: Optional time string.
            location: Optional location.
            description: Optional description.

        Returns:
            Event object.
        """
        event_date = datetime.now()
        if date_str:
            try:
                # Parse date - adjust formats as needed
                for fmt in ["%b %d", "%B %d", "%Y-%m-%d", "%m/%d/%Y"]:
                    try:
                        parsed = datetime.strptime(date_str.strip(), fmt)
                        if parsed.year == 1900:
                            parsed = parsed.replace(year=datetime.now().year)
                        event_date = parsed
                        break
                    except ValueError:
                        continue
            except Exception:
                pass

        return Event(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            date=event_date,
            time=time_str,
            location=location,
            url=url,
            source=self.name,
            tags=[],
        )
```

IMPORTANT REQUIREMENTS:
1. The class MUST inherit from ScraperPlugin
2. The class MUST have name, source_url, and description class attributes
3. The scrape() method MUST be async and return list[Event]
4. Always use try/except in scrape() and return empty list on error
5. Use the inherited self.crawl(url) method to fetch page content as markdown
6. Parse the markdown to extract event information
7. Use uuid.uuid4() for event IDs
8. The file should be self-contained with all necessary imports

Analyze the page structure provided and implement appropriate parsing logic.
Return ONLY the Python code, no explanations or markdown code blocks.
'''


async def generate_plugin_code(url: str, page_markdown: str) -> str:
    """Generate plugin code using Claude.

    Args:
        url: The source URL for the plugin.
        page_markdown: Markdown content of the page to scrape.

    Returns:
        Generated Python code for the plugin.
    """
    domain_name = extract_domain_name(url)
    plugin_name = "".join(word.capitalize() for word in domain_name.split("_"))

    template = get_plugin_template()

    # Truncate markdown if too long (keep first 8000 chars for context)
    if len(page_markdown) > 8000:
        page_markdown = page_markdown[:8000] + "\n... [truncated]"

    system_prompt = template + f"""

Generate a plugin for:
- URL: {url}
- Plugin name: {plugin_name}
- Plugin filename will be: {domain_name}.py

Here is the page structure (markdown format):

{page_markdown}
"""

    response = await send_message(
        message=f"Generate a scraper plugin for {url}. Analyze the page structure and implement parsing logic to extract events.",
        system_prompt=system_prompt,
    )

    # Clean up the response - remove markdown code blocks if present
    code = response.strip()
    if code.startswith("```python"):
        code = code[9:]
    elif code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]

    return code.strip()


def save_plugin_file(domain_name: str, code: str) -> Path:
    """Save generated plugin code to a file.

    Args:
        domain_name: Clean domain name for the filename.
        code: Python code to save.

    Returns:
        Path to the saved file.
    """
    plugins_dir = get_plugins_directory()
    file_path = plugins_dir / f"{domain_name}.py"
    file_path.write_text(code)
    return file_path


async def test_generated_plugin(file_path: Path) -> tuple[bool, str]:
    """Test a generated plugin by loading and running it.

    Args:
        file_path: Path to the plugin file.

    Returns:
        Tuple of (success, message).
    """
    try:
        # Try to load the plugin
        plugin_classes = load_plugin_from_file(file_path)

        if not plugin_classes:
            return False, "No valid ScraperPlugin class found in generated code."

        # Try to instantiate and run scrape
        plugin_class = plugin_classes[0]
        plugin_instance = plugin_class()

        logger.info(f"Testing plugin: {plugin_instance.name}")

        # Run a test scrape
        events = await plugin_instance.scrape()

        return True, f"Plugin '{plugin_instance.name}' loaded successfully. Found {len(events)} events."

    except SyntaxError as e:
        return False, f"Syntax error in generated code: {e}"
    except ImportError as e:
        return False, f"Import error in generated code: {e}"
    except Exception as e:
        return False, f"Error testing plugin: {e}"


async def create_plugin_for_url(url: str) -> str:
    """Create a new plugin for the given URL.

    Args:
        url: The URL to create a plugin for.

    Returns:
        Response message with results.
    """
    domain_name = extract_domain_name(url)

    try:
        # Step 1: Crawl the URL to get page structure
        logger.info(f"Crawling {url} for page structure...")
        page_markdown = await crawl_url_for_structure(url)

        if not page_markdown:
            return f"Failed to crawl {url}. The page might be inaccessible or empty."

        # Step 2: Generate plugin code using Claude
        logger.info("Generating plugin code with Claude...")
        plugin_code = await generate_plugin_code(url, page_markdown)

        # Step 3: Save the plugin file
        logger.info(f"Saving plugin to {domain_name}.py...")
        file_path = save_plugin_file(domain_name, plugin_code)

        # Step 4: Test the generated plugin
        logger.info("Testing generated plugin...")
        success, test_message = await test_generated_plugin(file_path)

        if success:
            # Step 5: Reload all plugins to include the new one
            reload_plugins()
            return f"Successfully created plugin for {url}!\n\n{test_message}\n\nThe plugin has been saved to `{file_path.name}` and is now ready to use."
        else:
            # Keep the file for debugging but warn about the error
            return f"Plugin generated but there was an error during testing:\n\n{test_message}\n\nThe plugin file has been saved to `{file_path.name}`. You may need to manually fix it or try again."

    except Exception as e:
        logger.error(f"Error creating plugin for {url}: {e}")
        return f"Failed to create plugin for {url}: {e}"


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


def events_to_response_format(events: list[Event]) -> list[dict[str, Any]]:
    """Convert Event objects to API response format.

    Args:
        events: List of Event objects.

    Returns:
        List of event dictionaries with ISO date strings.
    """
    return [
        {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "date": event.date.isoformat(),
            "time": event.time,
            "location": event.location,
            "url": event.url,
            "source": event.source,
            "tags": event.tags,
        }
        for event in events
    ]


async def process_chat_message(
    message: str,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    """Process a chat message and return AI response.

    Args:
        message: The user's message.
        conversation_id: Optional conversation ID for continuing a conversation.

    Returns:
        Dict with 'response' (AI response text), 'conversation_id', and optionally 'events'.
    """
    # Get or create conversation
    conv_id, messages = get_or_create_conversation(conversation_id)

    events: list[Event] = []

    # Check if this is a plugin creation request
    is_plugin_request, plugin_url = is_plugin_creation_request(message)
    if is_plugin_request and plugin_url:
        # Create a plugin for the URL
        response = await create_plugin_for_url(plugin_url)
    elif is_event_search_request(message):
        # Use event search and recommendation
        response, events = await search_and_recommend_events(
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
        "events": events_to_response_format(events),
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
