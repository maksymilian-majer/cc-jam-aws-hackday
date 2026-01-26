"""Claude AI service for chat and recommendations."""

import logging
import os
from typing import Any

import anthropic

logger = logging.getLogger(__name__)

# Message type for conversation history
MessageDict = dict[str, str]


def get_anthropic_client() -> anthropic.Anthropic:
    """Get the Anthropic client with API key from environment.

    Returns:
        Configured Anthropic client.

    Raises:
        ValueError: If ANTHROPIC_API_KEY environment variable is not set.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
    return anthropic.Anthropic(api_key=api_key)


async def send_message(
    message: str,
    conversation_history: list[MessageDict] | None = None,
    system_prompt: str | None = None,
) -> str:
    """Send a message to Claude and get a response.

    Args:
        message: The user's message to send.
        conversation_history: Optional list of previous messages in the conversation.
            Each message should have 'role' ('user' or 'assistant') and 'content' keys.
        system_prompt: Optional system prompt to guide Claude's behavior.

    Returns:
        Claude's response text.

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set.
        anthropic.APIError: If the API request fails.
    """
    try:
        client = get_anthropic_client()

        # Build messages list
        messages: list[dict[str, Any]] = []

        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        # Add the current message
        messages.append({
            "role": "user",
            "content": message,
        })

        # Build request kwargs
        request_kwargs: dict[str, Any] = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": messages,
        }

        # Add system prompt if provided
        if system_prompt:
            request_kwargs["system"] = system_prompt

        # Make the API call
        response = client.messages.create(**request_kwargs)

        # Extract text from response
        if response.content and len(response.content) > 0:
            content_block = response.content[0]
            if hasattr(content_block, "text"):
                return content_block.text
            return str(content_block)

        logger.warning("Empty response from Claude API")
        return "I apologize, but I couldn't generate a response. Please try again."

    except anthropic.AuthenticationError as e:
        logger.error(f"Authentication error with Claude API: {e}")
        raise ValueError("Invalid ANTHROPIC_API_KEY. Please check your API key.") from e

    except anthropic.RateLimitError as e:
        logger.error(f"Rate limit exceeded for Claude API: {e}")
        return "I'm currently experiencing high demand. Please try again in a moment."

    except anthropic.APIStatusError as e:
        logger.error(f"Claude API status error: {e}")
        return f"I encountered an error communicating with the AI service. Please try again later."

    except anthropic.APIError as e:
        logger.error(f"Claude API error: {e}")
        return "I encountered an unexpected error. Please try again later."

    except Exception as e:
        logger.error(f"Unexpected error in send_message: {e}")
        return "I encountered an unexpected error. Please try again later."


async def chat_with_context(
    message: str,
    conversation_history: list[MessageDict] | None = None,
    context: str | None = None,
) -> str:
    """Send a chat message with optional context (like event data).

    This is a convenience wrapper around send_message that formats
    context appropriately for the AI.

    Args:
        message: The user's message to send.
        conversation_history: Optional list of previous messages.
        context: Optional context to include (e.g., event data).

    Returns:
        Claude's response text.
    """
    system_prompt = """You are a helpful assistant for EventFinder, an application that helps users discover events.
You help users find events that match their interests and can provide recommendations based on available event data.
Be concise, friendly, and helpful in your responses."""

    if context:
        system_prompt += f"\n\nHere is relevant context for this conversation:\n{context}"

    return await send_message(
        message=message,
        conversation_history=conversation_history,
        system_prompt=system_prompt,
    )
