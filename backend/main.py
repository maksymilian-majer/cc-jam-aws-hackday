"""FastAPI backend for EventFinder application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter

from backend.models import ChatRequest, ChatResponse
from backend.services.chat import process_chat_message
from backend.services.plugin_loader import get_plugin_info, load_all_plugins

# Create the main FastAPI app
app = FastAPI(
    title="EventFinder API",
    description="AI-powered event discovery with plugin-based scrapers",
    version="0.1.0",
)

# Configure CORS for Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create API router with /api prefix
api_router = APIRouter(prefix="/api")


@api_router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@api_router.get("/plugins")
async def list_plugins() -> list[dict[str, str]]:
    """List all loaded scraper plugins.

    Returns:
        List of plugin information (name, source_url, description).
    """
    return get_plugin_info()


@api_router.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat with the AI assistant.

    Args:
        request: Chat request with message and optional conversation_id.

    Returns:
        Chat response with AI response and conversation_id.
    """
    result = await process_chat_message(
        message=request.message,
        conversation_id=request.conversation_id,
    )
    return ChatResponse(
        response=result["response"],
        conversation_id=result["conversation_id"],
    )


# Load plugins on startup
@app.on_event("startup")
async def startup_event() -> None:
    """Load plugins when the application starts."""
    load_all_plugins()


# Include the API router
app.include_router(api_router)
