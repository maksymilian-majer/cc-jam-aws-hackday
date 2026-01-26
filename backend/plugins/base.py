"""Base class for scraper plugins."""

from abc import ABC, abstractmethod
from urllib.parse import quote_plus

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

from backend.models import Event

# Default scroll script for infinite scroll pages
DEFAULT_SCROLL_SCRIPT = """
async function scrollToBottom() {
    for (let i = 0; i < 5; i++) {
        window.scrollTo(0, document.body.scrollHeight);
        await new Promise(r => setTimeout(r, 1000));
    }
}
await scrollToBottom();
"""


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

    # Whether to scroll the page to load more content (for infinite scroll sites)
    scroll_for_more: bool = False

    # Number of scroll iterations (each ~1 second)
    scroll_count: int = 5

    # Custom JavaScript to run before scraping (optional)
    custom_js: str | None = None

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

    def _get_scroll_script(self) -> str:
        """Get the scroll script with configured scroll count."""
        return f"""
async function scrollToBottom() {{
    for (let i = 0; i < {self.scroll_count}; i++) {{
        window.scrollTo(0, document.body.scrollHeight);
        await new Promise(r => setTimeout(r, 1000));
    }}
}}
await scrollToBottom();
"""

    async def crawl(self, url: str) -> str:
        """Crawl a URL and return the markdown content.

        Waits for JavaScript content to load using networkidle.
        Optionally scrolls to load more content for infinite scroll sites.

        Args:
            url: The URL to crawl.

        Returns:
            Markdown representation of the page content.
        """
        # Build JS code: scroll script + custom JS if needed
        js_code = None
        if self.scroll_for_more:
            js_code = self._get_scroll_script()
        if self.custom_js:
            js_code = (js_code or "") + "\n" + self.custom_js

        config = CrawlerRunConfig(
            wait_until="networkidle",
            page_timeout=60000 if self.scroll_for_more else 30000,
            js_code=js_code,
        )
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, config=config)
            return result.markdown
