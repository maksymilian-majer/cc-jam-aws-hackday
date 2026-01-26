"""Luma event scraper plugin."""

import logging
import re
import uuid
from datetime import datetime, timedelta

from backend.models import Event
from backend.plugins.base import ScraperPlugin

logger = logging.getLogger(__name__)


class LumaPlugin(ScraperPlugin):
    """Scraper plugin for lu.ma events."""

    name = "Luma"
    source_url = "https://lu.ma/sf"
    description = "Scrapes events from Luma SF Bay Area events page"

    # Enable scrolling to load more events (infinite scroll)
    scroll_for_more = True
    scroll_count = 5

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

    def _parse_date_header(self, line: str, next_line: str | None) -> datetime | None:
        """Parse a date from section headers like 'Today', 'Tomorrow', or 'Jan 28'.

        Args:
            line: Current line that might be a date header.
            next_line: Next line (might contain day of week).

        Returns:
            Parsed datetime or None if not a date header.
        """
        line = line.strip()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Check for "Today" or "Tomorrow"
        if line == "Today":
            return today
        if line == "Tomorrow":
            return today + timedelta(days=1)

        # Check for month-day format like "Jan 28", "Feb 5"
        month_day_match = re.match(
            r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})$",
            line,
            re.IGNORECASE,
        )
        if month_day_match:
            month_str = month_day_match.group(1)
            day = int(month_day_match.group(2))
            try:
                # Parse with current year
                parsed = datetime.strptime(f"{month_str} {day}", "%b %d")
                parsed = parsed.replace(year=today.year)
                # If date is in the past, assume next year
                if parsed < today:
                    parsed = parsed.replace(year=today.year + 1)
                return parsed
            except ValueError:
                pass

        return None

    def _parse_events(self, markdown: str) -> list[Event]:
        """Parse event data from markdown content.

        Args:
            markdown: Markdown content from crawled page.

        Returns:
            List of Event objects parsed from content.
        """
        events: list[Event] = []
        lines = markdown.split("\n")

        current_event: dict[str, str | datetime | None] = {}
        current_date: datetime | None = None
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else None

            # Check for date section headers
            parsed_date = self._parse_date_header(line, next_line)
            if parsed_date:
                current_date = parsed_date
                i += 1
                continue

            # Look for empty event links: [ ](https://luma.com/eventid)
            # These mark the start of a new event
            link_match = re.search(r"\[\s*\]\((https://luma\.com/[a-zA-Z0-9_-]+)\)", line)
            if link_match:
                # Save previous event if exists
                if current_event.get("title") and current_event.get("url"):
                    event = self._create_event(current_event)
                    if event:
                        events.append(event)

                # Start new event with current section date
                current_event = {
                    "title": None,
                    "url": link_match.group(1).strip(),
                    "date": current_date,
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
                    if next_line in ["Waitlist", "Going", "Interested", "Sold Out"]:
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

    def _create_event(self, data: dict[str, str | datetime | None]) -> Event | None:
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

        # Use provided date or fall back to current date
        event_date = datetime.now()
        date_value = data.get("date")
        if isinstance(date_value, datetime):
            event_date = date_value
        elif isinstance(date_value, str):
            # Try to parse string date formats
            for fmt in ["%b %d", "%B %d", "%b %d, %Y", "%B %d, %Y"]:
                try:
                    parsed = datetime.strptime(date_value.strip(), fmt)
                    if parsed.year == 1900:
                        current_year = datetime.now().year
                        parsed = parsed.replace(year=current_year)
                        if parsed < datetime.now():
                            parsed = parsed.replace(year=current_year + 1)
                    event_date = parsed
                    break
                except ValueError:
                    continue

        return Event(
            id=str(uuid.uuid4()),
            title=str(title),
            description=None,
            date=event_date,
            time=str(data.get("time")) if data.get("time") else None,
            location=str(data.get("location")) if data.get("location") else None,
            url=str(url),
            source=self.name,
            tags=[],
        )
