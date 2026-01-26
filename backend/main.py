"""FastAPI backend for EventFinder application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter

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


# Include the API router
app.include_router(api_router)
