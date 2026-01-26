"""Demo plugin for Claude Code Hack Day at Amazon."""

import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.models import Event
from backend.plugins.base import ScraperPlugin

# San Francisco timezone
SF_TZ = ZoneInfo("America/Los_Angeles")

EVENT_DESCRIPTION = """This isn't a typical hackathon.

Hack Day is a focused, single-day build designed around one clear problem and one shared direction. Everyone in the room is working toward the same goal — exploring what's possible when strong builders are given the right tools, the right constraints, and uninterrupted time.

You won't be juggling ideas or chasing prompts.
You'll be building something specific, intentional, and surprisingly powerful.

Throughout the day, you'll work hands-on with advanced AI tooling, refine your approach through iteration, and push a project from concept to something tangible. No fluff. No distractions. Just deep work, thoughtful experimentation, and quiet momentum.

As the day winds down, the room opens up — projects surface, patterns emerge, and what started as an idea becomes something shared.

What you build isn't fully revealed ahead of time.
That's part of the point.

Come curious. Leave with something real."""


class HackDayDemoPlugin(ScraperPlugin):
    """Demo plugin for Claude Code Hack Day event."""

    name = "HackDayDemo"
    source_url = "https://luma.com/amazon-hack-day-1-26-2026"
    description = "Demo event for Claude Code Hack Day at Amazon"

    async def scrape(self, query: str | None = None) -> list[Event]:
        """Return the demo event with start time 30 seconds from now."""
        # Get current time in San Francisco
        now_sf = datetime.now(SF_TZ)

        # Event starts 30 seconds from now
        event_start = now_sf + timedelta(seconds=30)

        # Format time string
        time_str = event_start.strftime("%-I:%M %p %Z")

        return [
            Event(
                id=str(uuid.uuid4()),
                title="Claude Code Hack Day at Amazon with Jam.dev",
                description=EVENT_DESCRIPTION,
                date=event_start.replace(tzinfo=None),  # Store as naive datetime
                time=time_str,
                location="Amazon, San Francisco",
                url="https://lu.ma/hackday-amazon",
                source=self.name,
                tags=["hackathon", "ai", "claude", "amazon"],
            )
        ]
