"""Base class for scraper plugins."""

from abc import ABC, abstractmethod

from crawl4ai import AsyncWebCrawler

from backend.models import Event


class ScraperPlugin(ABC):
    """Abstract base class for all scraper plugins."""

    name: str
    source_url: str
    description: str

    @abstractmethod
    async def scrape(self) -> list[Event]:
        """Scrape events from the source.

        Returns:
            List of Event objects scraped from the source.
            Returns empty list on error.
        """
        pass

    async def crawl(self, url: str) -> str:
        """Crawl a URL and return the markdown content.

        Args:
            url: The URL to crawl.

        Returns:
            Markdown representation of the page content.
        """
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            return result.markdown
