# Schedule Hacker

**Discover events through conversation. Generate scrapers with AI.**

---

Schedule Hacker is a chat-first application that helps you find hackathons, meetups, and startup events by simply describing what you're looking for. Tell it "I want AI hackathons in SF this month" and it searches across multiple event sources to surface the best matches.

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

## Event Sources

### Scraping targets

| Source                  | URL                                       |
|-------------------------|-------------------------------------------|
| Founders Bay Newsletter | https://www.foundersbay.com/events        |
| Luma SF                 | https://luma.com/sf                       |
| Cerebral Valley Events  | https://cerebralvalley.ai/events          |
| Luma GenAI SF           | https://luma.com/genai-sf                 |
| Luma Bay Area Product   | https://luma.com/BayAreaProduct           |
| Luma Frontier Tower     | https://luma.com/frontiertower            |
| Creators Corner (Luma)  | https://luma.com/user/usr-031s41mSnC3XpXz |
| AI Collective Events    | http://aicollective.com/events            |

### Inbound email via Resend

| Source             | Email / Notes                                         |
|--------------------|-------------------------------------------------------|
| Cerebral Valley    | `team@mail.cerebralvalley.ai`                         |
| Creators Corner HQ | Newsletter from https://creatorscornerhq.beehiiv.com/ |
| Brderless          | `joinbrderless@substack.com`                          |

## Quickstart

### Prerequisites

- Python 3.11+
- Node.js 18+
- Anthropic API key

### 1. Set up the Backend

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Install Playwright browsers (required for web scraping)
playwright install

# Set your Anthropic API key
export ANTHROPIC_API_KEY="your-api-key-here"

# Start the backend server (from project root)
python3 -m uvicorn backend.main:app --reload
```

The backend runs at `http://localhost:8000`.

### 2. Set up the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend runs at `http://localhost:5173`.

### 3. Use the App

Open `http://localhost:5173` in your browser and try:

- "Find me tech events in SF"
- "Search for hackathons this weekend"
- "Create a plugin for eventbrite.com"

## Project Structure

```
├── backend/
│   ├── main.py              # FastAPI app
│   ├── models.py            # Pydantic models
│   ├── plugins/             # Scraper plugins
│   │   ├── base.py          # Plugin interface
│   │   └── luma.py          # Luma events scraper
│   └── services/
│       ├── ai.py            # Claude API integration
│       ├── chat.py          # Chat logic
│       └── plugin_loader.py # Dynamic plugin loading
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   └── components/
│   │       ├── Chat.tsx       # Chat interface
│   │       ├── EventCard.tsx  # Event display cards
│   │       └── PluginPanel.tsx # Plugin management
│   └── package.json
└── README.md
```

## API Endpoints

| Endpoint       | Method | Description         |
|----------------|--------|---------------------|
| `/api/health`  | GET    | Health check        |
| `/api/plugins` | GET    | List loaded plugins |
| `/api/chat`    | POST   | Send chat message   |

## Environment Variables

| Variable            | Description                       |
|---------------------|-----------------------------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (required) |
