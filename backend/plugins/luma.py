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

    async def scrape(self) -> list[Event]:
        """Scrape events from Luma SF page.

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

        # Split by lines and look for event patterns
        lines = markdown.split("\n")

        current_event: dict[str, str | None] = {}
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Look for event links - typically formatted as [Title](url)
            link_match = re.search(r"\[([^\]]+)\]\((https?://lu\.ma/[^\)]+)\)", line)
            if link_match:
                # If we have a previous event, save it
                if current_event.get("title"):
                    event = self._create_event(current_event)
                    if event:
                        events.append(event)

                # Start new event
                current_event = {
                    "title": link_match.group(1).strip(),
                    "url": link_match.group(2).strip(),
                    "date": None,
                    "time": None,
                    "location": None,
                }

                # Look ahead for date/time/location in nearby lines
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue

                    # Try to extract date patterns
                    date_match = re.search(
                        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}",
                        next_line,
                        re.IGNORECASE,
                    )
                    if date_match and not current_event.get("date"):
                        current_event["date"] = next_line

                    # Try to extract time patterns
                    time_match = re.search(
                        r"\d{1,2}:\d{2}\s*(AM|PM|am|pm)?", next_line
                    )
                    if time_match and not current_event.get("time"):
                        current_event["time"] = time_match.group(0)

                    # Location often contains address-like text
                    if (
                        not current_event.get("location")
                        and not date_match
                        and not time_match
                        and len(next_line) > 5
                        and len(next_line) < 100
                    ):
                        # Likely a location if it's a moderate-length string
                        # that doesn't look like a date or time
                        if not re.match(r"^\d+$", next_line):
                            current_event["location"] = next_line

            i += 1

        # Don't forget the last event
        if current_event.get("title"):
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
