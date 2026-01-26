"""Base class for scraper plugins."""

from abc import ABC, abstractmethod
from urllib.parse import quote_plus

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

from backend.models import Event


class ScraperPlugin(ABC):
    """Abstract base class for all scraper plugins."""

    name: str
    source_url: str
    description: str

    # Optional: URL template with {query} placeholder for searchable plugins
    # Example: "https://example.com/search?q={query}"
    search_url_template: str | None = None

    # Whether this plugin supports search queries
    supports_search: bool = False

    @abstractmethod
    async def scrape(self, query: str | None = None) -> list[Event]:
        """Scrape events from the source.

        Args:
            query: Optional search query to filter events.

        Returns:
            List of Event objects scraped from the source.
            Returns empty list on error.
        """
        pass

    def get_scrape_url(self, query: str | None = None) -> str:
        """Get the URL to scrape, optionally with a search query.

        Args:
            query: Optional search query.

        Returns:
            URL to scrape.
        """
        if query and self.search_url_template:
            return self.search_url_template.format(query=quote_plus(query))
        return self.source_url

    async def crawl(self, url: str) -> str:
        """Crawl a URL and return the markdown content.

        Waits for JavaScript content to load using networkidle.

        Args:
            url: The URL to crawl.

        Returns:
            Markdown representation of the page content.
        """
        config = CrawlerRunConfig(
            wait_until="networkidle",
            page_timeout=30000,
        )
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, config=config)
            return result.markdown
