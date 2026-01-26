"""Chat service for managing conversations and AI interactions."""

import asyncio
import logging
import re
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, quote_plus

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

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
    """Crawl a URL to get its page structure for plugin generation.

    Uses networkidle to wait for JavaScript content to load.
    """
    config = CrawlerRunConfig(
        wait_until="networkidle",
        page_timeout=30000,
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        return result.markdown


def get_plugin_template() -> str:
    """Get the plugin template with instructions for Claude."""
    return '''You are generating a Python scraper plugin for EventFinder.

The markdown content you receive is from a web crawler that converts HTML to markdown.
Events typically appear in patterns like:

COMMON PATTERN 1 - Date header followed by linked title:
```
Jan30
### [Event Title](https://example.com/event-url)
Fri · 5:00 PM – 9:00 PM PST
Location Name, City
Description text...
```

COMMON PATTERN 2 - Linked title with metadata on following lines:
```
### [Event Title](url)
Date: January 30, 2025
Time: 5:00 PM
Location: San Francisco, CA
```

COMMON PATTERN 3 - Empty link followed by title heading (lu.ma style):
```
[ ](https://lu.ma/eventid)
### Event Title
5:00 PM
By Organizer
Location Name
```

The plugin MUST follow this interface:

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

    async def scrape(self, query: str | None = None) -> list[Event]:
        try:
            url = self.get_scrape_url(query)
            markdown = await self.crawl(url)
            return self._parse_events(markdown)
        except Exception as e:
            logger.error(f"Error scraping events: {e}")
            return []

    def _parse_events(self, markdown: str) -> list[Event]:
        """Parse events from markdown. IMPLEMENT BASED ON ACTUAL PAGE STRUCTURE."""
        events: list[Event] = []
        lines = markdown.split('\\n')

        # EXAMPLE: Look for ### [Title](url) pattern
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Match event title links: ### [Title](url) or [Title](url)
            title_match = re.search(r'###?\\s*\\[([^\\]]+)\\]\\(([^)]+)\\)', line)
            if title_match:
                title = title_match.group(1).strip()
                url = title_match.group(2).strip()

                # Skip navigation/filter links
                if any(skip in title.lower() for skip in ['sign in', 'search', 'submit', 'all events']):
                    i += 1
                    continue

                # Make URL absolute if needed
                if not url.startswith('http'):
                    url = f"https://DOMAIN{url}"

                # Look ahead for date, time, location in next few lines
                date_str = None
                time_str = None
                location = None
                description = None

                for j in range(i + 1, min(i + 6, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue

                    # Check for time pattern: "5:00 PM" or "Fri · 5:00 PM – 9:00 PM"
                    time_match = re.search(r'(\\d{1,2}:\\d{2}\\s*(?:AM|PM)(?:\\s*[–-]\\s*\\d{1,2}:\\d{2}\\s*(?:AM|PM))?(?:\\s+[A-Z]{2,4})?)', next_line, re.IGNORECASE)
                    if time_match and not time_str:
                        time_str = time_match.group(1)

                    # Check for date pattern at start of line: "Jan30" or "January 30"
                    date_match = re.match(r'^((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\\s*\\d{1,2})', next_line, re.IGNORECASE)
                    if date_match and not date_str:
                        date_str = date_match.group(1)

                    # Location often contains comma (City, State)
                    if ',' in next_line and len(next_line) < 100 and not location:
                        if not any(skip in next_line.lower() for skip in ['http', 'see more', '@']):
                            location = next_line

                    # Description is usually longer text
                    if len(next_line) > 80 and not description:
                        description = next_line[:200]

                event = self._create_event(title, url, date_str, time_str, location, description)
                events.append(event)

            i += 1

        return events

    def _create_event(self, title: str, url: str, date_str: str | None = None,
                      time_str: str | None = None, location: str | None = None,
                      description: str | None = None) -> Event:
        event_date = datetime.now()
        if date_str:
            # Clean date string
            date_clean = re.sub(r'[^a-zA-Z0-9\\s]', ' ', date_str).strip()
            for fmt in ["%b %d", "%B %d", "%b%d", "%B%d"]:
                try:
                    parsed = datetime.strptime(date_clean, fmt)
                    parsed = parsed.replace(year=datetime.now().year)
                    if parsed < datetime.now():
                        parsed = parsed.replace(year=datetime.now().year + 1)
                    event_date = parsed
                    break
                except ValueError:
                    continue

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

CRITICAL REQUIREMENTS:
1. ACTUALLY PARSE THE EVENTS from the markdown - don't just return empty list
2. Look at the page structure provided and identify the pattern used for events
3. Extract: title, URL, date, time, location from the markdown
4. Skip navigation links, filters, and non-event content
5. Make URLs absolute (prepend domain if they start with /)
6. The scrape() method MUST be async and return list[Event]

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
