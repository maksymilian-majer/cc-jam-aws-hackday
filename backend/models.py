"""Pydantic models for EventFinder application."""

from datetime import datetime

from pydantic import BaseModel, Field


class Event(BaseModel):
    """Standard event model for all scraper plugins."""

    id: str
    title: str
    description: str | None = None
    date: datetime
    time: str | None = None
    location: str | None = None
    url: str
    source: str
    tags: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str
    conversation_id: str
