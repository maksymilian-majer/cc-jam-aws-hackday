"""Luma event scraper plugin."""

import logging
import re
import uuid
from datetime import datetime

from backend.models import Event
from backend.plugins.base import ScraperPlugin

logger = logging.getLogger(__name__)


class LumaPlugin(ScraperPlugin):
    """Scraper plugin for lu.ma events."""

    name = "Luma"
    source_url = "https://lu.ma/sf"
    description = "Scrapes events from Luma SF Bay Area events page"

    async def scrape(self, query: str | None = None) -> list[Event]:
        """Scrape events from Luma SF page.

        Args:
            query: Optional search query (not currently used for Luma).

        Returns:
            List of Event objects scraped from lu.ma/sf.
            Returns empty list on error.
        """
        try:
            markdown = await self.crawl(self.source_url)
            return self._parse_events(markdown)
        except Exception as e:
            logger.error(f"Error scraping Luma events: {e}")
            return []

    def _parse_events(self, markdown: str) -> list[Event]:
        """Parse event data from markdown content.

        Args:
            markdown: Markdown content from crawled page.

        Returns:
            List of Event objects parsed from content.
        """
        events: list[Event] = []
        lines = markdown.split("\n")

        current_event: dict[str, str | None] = {}
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Look for empty event links: [ ](https://luma.com/eventid)
            # These mark the start of a new event
            link_match = re.search(r"\[\s*\]\((https://luma\.com/[a-zA-Z0-9]+)\)", line)
            if link_match:
                # Save previous event if exists
                if current_event.get("title") and current_event.get("url"):
                    event = self._create_event(current_event)
                    if event:
                        events.append(event)

                # Start new event
                current_event = {
                    "title": None,
                    "url": link_match.group(1).strip(),
                    "date": None,
                    "time": None,
                    "location": None,
                }

                # Look ahead for title, time, location
                for j in range(i + 1, min(i + 15, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line or next_line == "​":  # Skip empty/zero-width
                        continue

                    # Title is in ### heading format
                    title_match = re.match(r"^###\s+(.+)$", next_line)
                    if title_match and not current_event.get("title"):
                        current_event["title"] = title_match.group(1).strip()
                        continue

                    # Time pattern like "5:00 PM" or "6:00 PM PST"
                    time_match = re.match(
                        r"^(\d{1,2}:\d{2}\s*(AM|PM)(\s+[A-Z]{3})?)$",
                        next_line,
                        re.IGNORECASE,
                    )
                    if time_match and not current_event.get("time"):
                        current_event["time"] = time_match.group(1).strip()
                        continue

                    # Skip "By Author" lines
                    if next_line.startswith("By "):
                        continue

                    # Skip lines that look like attendee counts
                    if re.match(r"^\+\d+$", next_line):
                        continue

                    # Skip status badges
                    if next_line in ["Waitlist", "Going", "Interested"]:
                        continue

                    # Location: moderate-length text that isn't a title or time
                    if (
                        not current_event.get("location")
                        and current_event.get("title")
                        and 3 < len(next_line) < 100
                        and not next_line.startswith("#")
                        and not next_line.startswith("[")
                    ):
                        current_event["location"] = next_line
                        break  # Location is typically last, stop looking

            i += 1

        # Don't forget the last event
        if current_event.get("title") and current_event.get("url"):
            event = self._create_event(current_event)
            if event:
                events.append(event)

        return events

    def _create_event(self, data: dict[str, str | None]) -> Event | None:
        """Create an Event object from parsed data.

        Args:
            data: Dictionary with event data.

        Returns:
            Event object or None if required fields are missing.
        """
        title = data.get("title")
        url = data.get("url")

        if not title or not url:
            return None

        # Parse date or use current date as fallback
        event_date = datetime.now()
        date_str = data.get("date")
        if date_str:
            try:
                # Try to parse various date formats
                for fmt in ["%b %d", "%B %d", "%b %d, %Y", "%B %d, %Y"]:
                    try:
                        parsed = datetime.strptime(date_str.strip(), fmt)
                        # If no year, assume current or next year
                        if parsed.year == 1900:
                            current_year = datetime.now().year
                            parsed = parsed.replace(year=current_year)
                            # If date is in the past, assume next year
                            if parsed < datetime.now():
                                parsed = parsed.replace(year=current_year + 1)
                        event_date = parsed
                        break
                    except ValueError:
                        continue
            except Exception:
                pass

        return Event(
            id=str(uuid.uuid4()),
            title=title,
            description=None,
            date=event_date,
            time=data.get("time"),
            location=data.get("location"),
            url=url,
            source=self.name,
            tags=[],
        )
