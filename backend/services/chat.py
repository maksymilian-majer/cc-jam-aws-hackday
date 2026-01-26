"""Chat service for managing conversations and AI interactions."""

import uuid
from typing import Any

from backend.services.ai import MessageDict, chat_with_context

# In-memory storage for conversations
# Maps conversation_id -> list of messages
_conversations: dict[str, list[MessageDict]] = {}


def get_or_create_conversation(conversation_id: str | None) -> tuple[str, list[MessageDict]]:
    """Get an existing conversation or create a new one.

    Args:
        conversation_id: Optional existing conversation ID.

    Returns:
        Tuple of (conversation_id, messages list).
    """
    if conversation_id and conversation_id in _conversations:
        return conversation_id, _conversations[conversation_id]

    # Generate new conversation ID
    new_id = str(uuid.uuid4())
    _conversations[new_id] = []
    return new_id, _conversations[new_id]


async def process_chat_message(
    message: str,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    """Process a chat message and return AI response.

    Args:
        message: The user's message.
        conversation_id: Optional conversation ID for continuing a conversation.

    Returns:
        Dict with 'response' (AI response text) and 'conversation_id'.
    """
    # Get or create conversation
    conv_id, messages = get_or_create_conversation(conversation_id)

    # Get AI response using conversation history
    response = await chat_with_context(
        message=message,
        conversation_history=messages if messages else None,
    )

    # Store the user message and AI response in conversation history
    messages.append({"role": "user", "content": message})
    messages.append({"role": "assistant", "content": response})

    return {
        "response": response,
        "conversation_id": conv_id,
    }


def get_conversation(conversation_id: str) -> list[MessageDict] | None:
    """Get a conversation by ID.

    Args:
        conversation_id: The conversation ID.

    Returns:
        List of messages or None if not found.
    """
    return _conversations.get(conversation_id)


def clear_conversation(conversation_id: str) -> bool:
    """Clear a conversation by ID.

    Args:
        conversation_id: The conversation ID.

    Returns:
        True if conversation was cleared, False if not found.
    """
    if conversation_id in _conversations:
        del _conversations[conversation_id]
        return True
    return False
