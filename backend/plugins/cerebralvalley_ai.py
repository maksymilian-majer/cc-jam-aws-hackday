"""CerebralvalleyAi event scraper plugin."""

import logging
import re
import uuid
from datetime import datetime

from backend.models import Event
from backend.plugins.base import ScraperPlugin

logger = logging.getLogger(__name__)


class CerebralvalleyAiPlugin(ScraperPlugin):
    """Scraper plugin for cerebralvalley.ai events."""

    name = "CerebralvalleyAi"
    source_url = "https://cerebralvalley.ai/events"
    description = "Scrapes events from cerebralvalley.ai"

    # Enable scrolling for infinite scroll pages (loads more events)
    scroll_for_more = True
    scroll_count = 5

    async def scrape(self, query: str | None = None) -> list[Event]:
        try:
            url = self.get_scrape_url(query)
            markdown = await self.crawl(url)
            return self._parse_events(markdown)
        except Exception as e:
            logger.error(f"Error scraping events: {e}")
            return []

    def _parse_events(self, markdown: str) -> list[Event]:
        """Parse events from markdown based on cerebralvalley.ai structure."""
        events: list[Event] = []
        lines = markdown.split('\n')

        i = 0
        current_date = None
        
        while i < len(lines):
            line = lines[i].strip()

            # Look for date headers like "Jan30", "Jan27", etc.
            date_header_match = re.match(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{1,2})$', line, re.IGNORECASE)
            if date_header_match:
                month = date_header_match.group(1)
                day = date_header_match.group(2)
                current_date = f"{month} {day}"
                i += 1
                continue

            # Look for section headers like "## Today", "## Tomorrow"
            if re.match(r'^##\s+(Today|Tomorrow)', line):
                i += 1
                continue

            # Match event title links: ### [Title](url)
            title_match = re.search(r'###\s*\[([^\]]+)\]\(([^)]+)\)', line)
            if title_match:
                title = title_match.group(1).strip()
                url = title_match.group(2).strip()

                # Skip navigation/filter links
                if any(skip in title.lower() for skip in ['sign in', 'search', 'submit', 'all events', 'events']):
                    i += 1
                    continue

                # Make URL absolute if needed
                if not url.startswith('http'):
                    if url.startswith('/'):
                        url = f"https://cerebralvalley.ai{url}"
                    else:
                        url = f"https://cerebralvalley.ai/{url}"

                # Look ahead for time, location, description in next few lines
                time_str = None
                location = None
                description = None

                for j in range(i + 1, min(i + 8, len(lines))):
                    if j >= len(lines):
                        break
                    next_line = lines[j].strip()
                    if not next_line:
                        continue

                    # Stop if we hit another event title
                    if re.search(r'###\s*\[', next_line):
                        break

                    # Check for time pattern: "Fri · 5:00 PM – 9:00 PM PST"
                    time_match = re.search(r'([A-Za-z]{3}\s*·\s*)?(\d{1,2}:\d{2}\s*(?:AM|PM)(?:\s*[–-]\s*\d{1,2}:\d{2}\s*(?:AM|PM))?(?:\s+[A-Z]{2,4})?)', next_line, re.IGNORECASE)
                    if time_match and not time_str:
                        time_str = time_match.group(2) if time_match.group(2) else time_match.group(0)

                    # Location often appears after time and contains comma or address
                    if (',' in next_line or any(addr in next_line for addr in ['Ave', 'St', 'Dr', 'CA', 'SF', 'San Francisco', 'Palo Alto', 'Menlo Park'])) and not location:
                        if not any(skip in next_line.lower() for skip in ['http', 'see more', '@', 'utm_']) and len(next_line) < 150:
                            location = next_line

                    # Description is usually longer text (but not "see more" lines)
                    if len(next_line) > 100 and 'see more' not in next_line.lower() and not description:
                        if not any(skip in next_line.lower() for skip in ['http', 'utm_']):
                            description = next_line[:300]

                event = self._create_event(title, url, current_date, time_str, location, description)
                events.append(event)

            i += 1

        return events

    def _create_event(self, title: str, url: str, date_str: str | None = None,
                      time_str: str | None = None, location: str | None = None,
                      description: str | None = None) -> Event:
        event_date = datetime.now()
        if date_str:
            # Clean date string and parse
            date_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', date_str).strip()
            for fmt in ["%b %d", "%B %d"]:
                try:
                    parsed = datetime.strptime(date_clean, fmt)
                    parsed = parsed.replace(year=datetime.now().year)
                    # If parsed date is in the past, assume next year
                    if parsed.date() < datetime.now().date():
                        parsed = parsed.replace(year=datetime.now().year + 1)
                    event_date = parsed
                    break
                except ValueError:
                    continue

        # Clean up time string if present
        if time_str:
            # Remove day prefix like "Fri · " 
            time_str = re.sub(r'^[A-Za-z]{3}\s*·\s*', '', time_str).strip()

        # Clean up location
        if location:
            # Remove trailing comma and whitespace
            location = location.rstrip(', ').strip()

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