# PRD: Event Finder with AI-Powered Plugin Generation

## Introduction

Build a chat-based application that helps users discover relevant events (hackathons, meetups, startup events) by scraping event sources through a plugin system. The application has two core capabilities:

1. **Event Discovery**: Users describe their interests in natural language, and the AI recommends the best matching events from scraped sources
2. **Plugin Generation**: Users can request new scraper plugins for any event website, and the AI generates Python scripts that conform to a standard output format

This is a hackathon project prioritizing speed over security - plugins are trusted and loaded directly.

## Goals

- Enable users to find relevant events through conversational AI interface
- Automatically scrape multiple event sources via a plugin architecture
- Allow AI-powered generation of new scraper plugins on demand
- Provide personalized event recommendations based on user interests
- Support dynamic loading of user-generated plugins without restart

## User Stories

### US-001: Set up project structure with FastAPI backend
**Description:** As a developer, I need the basic project scaffolding so I can build features on a solid foundation.

**Acceptance Criteria:**
- [ ] FastAPI backend with `/api` prefix for all endpoints
- [ ] React frontend bootstrapped (Vite or Create React App)
- [ ] Basic health check endpoint (`GET /api/health`)
- [ ] CORS configured for local development
- [ ] Project runs with `uvicorn` (backend) and `npm run dev` (frontend)
- [ ] Typecheck/lint passes

### US-002: Define plugin interface and event schema
**Description:** As a developer, I need a standard interface for plugins so all scrapers output consistent data.

**Acceptance Criteria:**
- [ ] `Event` Pydantic model with fields: `id`, `title`, `description`, `date`, `time`, `location`, `url`, `source`, `tags` (optional)
- [ ] Plugin base class requiring async `scrape() -> list[Event]` method
- [ ] Plugin base class includes `crawl(url)` helper method using crawl4ai
- [ ] Plugin metadata: `name`, `source_url`, `description`
- [ ] Example plugin skeleton in `plugins/` directory
- [ ] Typecheck passes

### US-003: Create Luma scraper plugin
**Description:** As a user, I want events from lu.ma scraped so I can discover Luma events.

**Acceptance Criteria:**
- [ ] Plugin uses crawl4ai to scrape events from lu.ma (SF Bay Area or configurable location)
- [ ] Returns list of `Event` objects matching the schema
- [ ] Uses crawl4ai's async API with `AsyncWebCrawler`
- [ ] Parses crawl4ai Markdown output to extract event data
- [ ] Graceful error handling (returns empty list on failure, logs error)
- [ ] Typecheck passes

### US-004: Build plugin loader system
**Description:** As a developer, I need to dynamically load plugins so users can add new scrapers.

**Acceptance Criteria:**
- [ ] Scan `plugins/` directory for Python files
- [ ] Dynamically import and register plugins that implement the interface
- [ ] Reload plugins on demand (endpoint or startup)
- [ ] List loaded plugins via `GET /api/plugins`
- [ ] Typecheck passes

### US-005: Create chat API endpoint
**Description:** As a user, I want to chat with the AI to describe my event interests.

**Acceptance Criteria:**
- [ ] `POST /api/chat` accepts `{ message: string, conversation_id?: string }`
- [ ] Integrates with Claude API for responses
- [ ] Maintains conversation context per `conversation_id`
- [ ] Returns `{ response: string, conversation_id: string }`
- [ ] Typecheck passes

### US-006: Implement event search and recommendation
**Description:** As a user, I want the AI to recommend events based on my described interests.

**Acceptance Criteria:**
- [ ] When user asks for events, system scrapes all loaded plugins
- [ ] Events passed to Claude with user's interest description
- [ ] Claude ranks and explains why each event matches
- [ ] Response includes event details with links
- [ ] Handles "no matching events" gracefully
- [ ] Typecheck passes

### US-007: Build plugin generation capability
**Description:** As a user, I want to request a new scraper plugin and have the AI generate it.

**Acceptance Criteria:**
- [ ] User can say "create a plugin for [website URL]"
- [ ] AI first crawls the target URL with crawl4ai to understand the page structure
- [ ] AI generates Python code using crawl4ai and following the plugin interface
- [ ] Generated plugin saved to `plugins/` directory
- [ ] Plugin automatically loaded after generation
- [ ] AI confirms plugin creation with test run results
- [ ] Typecheck passes

### US-008: Create chat UI component
**Description:** As a user, I want a chat interface to interact with the event finder.

**Acceptance Criteria:**
- [ ] Chat input field with send button
- [ ] Message history displayed (user messages right, AI left)
- [ ] Loading indicator while AI responds
- [ ] Auto-scroll to latest message
- [ ] Responsive design (works on mobile)
- [ ] Verify in browser

### US-009: Display event cards in chat
**Description:** As a user, I want events displayed as rich cards so I can quickly scan them.

**Acceptance Criteria:**
- [ ] Event cards show: title, date/time, location, source badge
- [ ] Cards are clickable (link to event URL)
- [ ] AI explanation shown above/below cards
- [ ] Cards rendered inline in chat history
- [ ] Verify in browser

### US-010: Add plugin management UI
**Description:** As a user, I want to see loaded plugins and trigger new plugin generation.

**Acceptance Criteria:**
- [ ] Sidebar or panel showing loaded plugins with status
- [ ] "Generate Plugin" button opens prompt input
- [ ] Shows generation progress/status
- [ ] Newly generated plugins appear in list
- [ ] Verify in browser

## Functional Requirements

- FR-1: Backend must expose REST API at `/api/*` prefix
- FR-2: All plugins must implement async `scrape() -> list[Event]` interface using crawl4ai
- FR-3: Event schema must include: id, title, description, date, time, location, url, source
- FR-4: Plugin loader must scan `plugins/` directory and import valid plugins
- FR-5: Chat endpoint must maintain conversation context across requests
- FR-6: Claude API must be used for event recommendations and plugin generation
- FR-7: Generated plugins must be saved to `plugins/` and auto-loaded
- FR-8: Frontend must display chat interface with event card rendering
- FR-9: System must handle plugin failures gracefully (skip failed plugins, continue with others)

## Non-Goals

- No user authentication or accounts
- No persistent storage of conversations (in-memory only)
- No plugin sandboxing or security validation
- No rate limiting or API key management UI
- No event bookmarking or calendar integration
- No scheduled/background scraping

## Technical Considerations

- **Backend**: Python 3.11+, FastAPI, Pydantic
- **Frontend**: React 18+, TypeScript, Tailwind CSS (or similar)
- **AI**: Anthropic Claude API (claude-sonnet or claude-haiku for speed)
- **Scraping**: [crawl4ai](https://github.com/unclecode/crawl4ai) - produces LLM-ready Markdown, handles JS-heavy sites
- **Plugin Loading**: Python `importlib` for dynamic imports

### Crawl4AI Setup

```bash
pip install -U crawl4ai
crawl4ai-setup
```

### Crawl4AI Usage in Plugins

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def scrape_page(url: str) -> str:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        return result.markdown
```

Key benefits:
- Async-first design (fits well with FastAPI)
- Handles dynamic/JS content automatically
- Returns clean Markdown perfect for Claude to parse
- Schema-based extraction for structured data

### Plugin Interface

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel
from datetime import datetime
from crawl4ai import AsyncWebCrawler

class Event(BaseModel):
    id: str
    title: str
    description: str | None
    date: datetime
    time: str | None
    location: str | None
    url: str
    source: str
    tags: list[str] = []

class ScraperPlugin(ABC):
    name: str
    source_url: str
    description: str

    @abstractmethod
    async def scrape(self) -> list[Event]:
        """Scrape events using crawl4ai. Must be async."""
        pass

    async def crawl(self, url: str) -> str:
        """Helper to crawl a URL and return LLM-ready markdown."""
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            return result.markdown
```

### Directory Structure

```
/
├── backend/
│   ├── main.py           # FastAPI app
│   ├── models.py         # Pydantic models
│   ├── plugins/          # Scraper plugins
│   │   ├── __init__.py
│   │   ├── base.py       # Plugin interface
│   │   └── luma.py       # Initial plugin (others vibe-coded later)
│   ├── services/
│   │   ├── plugin_loader.py
│   │   ├── chat.py
│   │   └── ai.py         # Claude integration
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.tsx
│   │   │   ├── EventCard.tsx
│   │   │   └── PluginPanel.tsx
│   │   └── App.tsx
│   └── package.json
└── README.md
```

## Success Metrics

- User can ask "find me AI hackathons this month" and get relevant results
- User can say "create a plugin for eventbrite.com" and get a working scraper
- New plugins load without application restart
- End-to-end flow works in under 30 seconds

## Open Questions

- Should we cache scraped events to avoid hammering sources?
- What's the fallback if a website blocks scraping?
- Should generated plugins be editable in the UI?

## Future Plugins (Vibe Code Later)

Additional plugins to be generated via the plugin generation feature during demo:
- Meetup (`meetup.com/find/?location=us--ca--San+Francisco&source=EVENTS`)
- Cerebral Valley (`cerebralvalley.ai/events`)
- Eventbrite
- Others as needed
