# Schedule Hacker

**Discover events through conversation. Generate scrapers with AI.**

---

Event Finder is a chat-first application that helps you find hackathons, meetups, and startup events by simply describing what you're looking for. Tell it "I want AI hackathons in SF this month" and it searches across multiple event sources to surface the best matches.

The magic? Ask it to scrape any event website and it will generate a working plugin on the fly. Say "create a plugin for eventbrite.com" and watch it crawl the site, understand its structure, and write a Python scraper—no restart required.

**Tech Stack:**
- FastAPI + React/TypeScript
- Claude API for recommendations & code generation
- crawl4ai for intelligent web scraping
- Dynamic plugin architecture with hot-reload

**Key Features:**
- Natural language event search
- AI-powered event ranking & explanations
- On-demand scraper generation
- Extensible plugin system
