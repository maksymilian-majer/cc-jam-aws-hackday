# EventFinder

AI-powered event discovery with chat-based interface and plugin-based scrapers.

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

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/plugins` | GET | List loaded plugins |
| `/api/chat` | POST | Send chat message |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (required) |
