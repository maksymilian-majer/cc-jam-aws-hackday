"""Chat service for managing conversations and AI interactions."""

import asyncio
import logging
import re
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, quote_plus

from crawl4ai import AsyncWebCrawler

from backend.models import Event
from backend.services.ai import chat_with_tools, send_message
from backend.services.plugin_loader import (
    get_plugin_registry,
    get_plugins_directory,
    load_plugin_from_file,
    reload_plugins,
)

logger = logging.getLogger(__name__)

# In-memory storage for conversations
_conversations: dict[str, list[dict[str, Any]]] = {}


async def scrape_all_plugins(query: str | None = None) -> list[Event]:
    """Scrape events from all loaded plugins concurrently.

    Args:
        query: Optional search query to pass to plugins that support searching.

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
        if plugin_instance.supports_search and query:
            scrape_tasks.append(plugin_instance.scrape(query=query))
        else:
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


def extract_domain_name(url: str) -> str:
    """Extract a clean domain name for use as a plugin filename."""
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split("/")[0]
    if domain.startswith("www."):
        domain = domain[4:]
    clean_name = re.sub(r"[.\-]", "_", domain)
    clean_name = re.sub(r"[^a-z0-9_]", "", clean_name.lower())
    return clean_name


async def crawl_url_for_structure(url: str) -> str:
    """Crawl a URL to get its page structure for plugin generation."""
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        return result.markdown


def get_plugin_template() -> str:
    """Get the plugin template with instructions for Claude."""
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

    # If the site supports search, set these:
    # search_url_template = "[url_with_{query}_placeholder]"
    # supports_search = True

    async def scrape(self, query: str | None = None) -> list[Event]:
        """Scrape events from the source.

        Args:
            query: Optional search query to filter events.

        Returns:
            List of Event objects scraped from the source.
            Returns empty list on error.
        """
        try:
            url = self.get_scrape_url(query)
            markdown = await self.crawl(url)
            return self._parse_events(markdown)
        except Exception as e:
            logger.error(f"Error scraping events: {e}")
            return []

    def _parse_events(self, markdown: str) -> list[Event]:
        """Parse event data from markdown content."""
        events: list[Event] = []
        # Implement parsing logic based on page structure
        return events

    def _create_event(self, title: str, url: str, date_str: str | None = None,
                      time_str: str | None = None, location: str | None = None,
                      description: str | None = None) -> Event:
        """Create an Event object from parsed data."""
        event_date = datetime.now()
        if date_str:
            try:
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
3. The scrape() method MUST be async, accept optional query parameter, and return list[Event]
4. If the site supports search, set search_url_template with {query} placeholder and supports_search = True
5. Use self.get_scrape_url(query) to get the URL (handles search URLs automatically)
6. Always use try/except in scrape() and return empty list on error
7. Use uuid.uuid4() for event IDs

Analyze the page structure provided and implement appropriate parsing logic.
Return ONLY the Python code, no explanations or markdown code blocks.
'''


async def generate_plugin_code(url: str, page_markdown: str) -> str:
    """Generate plugin code using Claude."""
    domain_name = extract_domain_name(url)
    plugin_name = "".join(word.capitalize() for word in domain_name.split("_"))

    template = get_plugin_template()

    # Truncate markdown if too long
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

    # Clean up response
    code = response.strip()
    if code.startswith("```python"):
        code = code[9:]
    elif code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]

    return code.strip()


def save_plugin_file(domain_name: str, code: str) -> Path:
    """Save generated plugin code to a file."""
    plugins_dir = get_plugins_directory()
    file_path = plugins_dir / f"{domain_name}.py"
    file_path.write_text(code)
    return file_path


async def test_generated_plugin(file_path: Path) -> tuple[bool, str]:
    """Test a generated plugin by loading and running it."""
    try:
        plugin_classes = load_plugin_from_file(file_path)

        if not plugin_classes:
            return False, "No valid ScraperPlugin class found in generated code."

        plugin_class = plugin_classes[0]
        plugin_instance = plugin_class()

        logger.info(f"Testing plugin: {plugin_instance.name}")
        events = await plugin_instance.scrape()

        return True, f"Plugin '{plugin_instance.name}' loaded successfully. Found {len(events)} events."

    except SyntaxError as e:
        return False, f"Syntax error in generated code: {e}"
    except ImportError as e:
        return False, f"Import error in generated code: {e}"
    except Exception as e:
        return False, f"Error testing plugin: {e}"


async def create_plugin_for_url(url: str) -> str:
    """Create a new plugin for the given URL."""
    domain_name = extract_domain_name(url)

    try:
        logger.info(f"Crawling {url} for page structure...")
        page_markdown = await crawl_url_for_structure(url)

        if not page_markdown:
            return f"Failed to crawl {url}. The page might be inaccessible or empty."

        logger.info("Generating plugin code with Claude...")
        plugin_code = await generate_plugin_code(url, page_markdown)

        logger.info(f"Saving plugin to {domain_name}.py...")
        file_path = save_plugin_file(domain_name, plugin_code)

        logger.info("Testing generated plugin...")
        success, test_message = await test_generated_plugin(file_path)

        if success:
            reload_plugins()
            return f"Successfully created plugin for {url}!\n\n{test_message}\n\nThe plugin has been saved to `{file_path.name}` and is now ready to use."
        else:
            return f"Plugin generated but there was an error during testing:\n\n{test_message}\n\nThe plugin file has been saved to `{file_path.name}`. You may need to manually fix it or try again."

    except Exception as e:
        logger.error(f"Error creating plugin for {url}: {e}")
        return f"Failed to create plugin for {url}: {e}"


def get_or_create_conversation(conversation_id: str | None) -> tuple[str, list[dict[str, Any]]]:
    """Get an existing conversation or create a new one."""
    if conversation_id and conversation_id in _conversations:
        return conversation_id, _conversations[conversation_id]

    new_id = str(uuid.uuid4())
    _conversations[new_id] = []
    return new_id, _conversations[new_id]


def events_to_response_format(events: list[Event]) -> list[dict[str, Any]]:
    """Convert Event objects to API response format."""
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

    Uses Claude's tool calling to intelligently decide when to search for
    events or create plugins based on the user's message.
    """
    conv_id, messages = get_or_create_conversation(conversation_id)

    # Use tool-based chat - Claude decides when to use tools
    response, events = await chat_with_tools(
        message=message,
        conversation_history=messages if messages else None,
        scrape_function=scrape_all_plugins,
        create_plugin_function=create_plugin_for_url,
    )

    # Store conversation history (simplified - just text for now)
    messages.append({"role": "user", "content": message})
    messages.append({"role": "assistant", "content": response})

    return {
        "response": response,
        "conversation_id": conv_id,
        "events": events_to_response_format(events),
    }


def get_conversation(conversation_id: str) -> list[dict[str, Any]] | None:
    """Get a conversation by ID."""
    return _conversations.get(conversation_id)


def clear_conversation(conversation_id: str) -> bool:
    """Clear a conversation by ID."""
    if conversation_id in _conversations:
        del _conversations[conversation_id]
        return True
    return False
