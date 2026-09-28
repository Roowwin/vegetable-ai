"""
AI Agent Endpoints
==================
HTTP endpoints for chatting with the AI agent.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional

from app.api.deps import DbSession
from app.agent.agent import run_agent
from app.agent.router import ModelRole

router = APIRouter(prefix="/api/agent", tags=["AI Agent"])


class ChatRequest(BaseModel):
    """Request to chat with the AI agent."""
    query: str = Field(min_length=1, max_length=2000, description="Your question for the AI")
    conversation_history: Optional[list[dict]] = Field(
        default=None,
        description="Previous messages for context (optional)"
    )
    override_model: Optional[str] = Field(
        default=None,
        description="Force a specific model: 'router', 'general', or 'advanced'"
    )


class ChatResponse(BaseModel):
    """Response from the AI agent."""
    response: str
    model_used: str
    tools_called: list[str]
    iterations: int


@router.post("/chat", response_model=ChatResponse, summary="Chat with the AI agent")
async def chat(data: ChatRequest, db: DbSession):
    """
    Ask the AI agent a question about your vegetable business.

    The agent will:
    1. Decide which tools to call (if any)
    2. Query your real database
    3. Reason about the results
    4. Generate a natural language response

    Examples:
    - "How many active lots do I have?"
    - "Why is my profit negative this month?"
    - "Which farmer is most reliable?"
    - "What items are about to expire?"
    """
    override = None
    if data.override_model:
        try:
            override = ModelRole(data.override_model)
        except ValueError:
            pass

    result = run_agent(
        user_query=data.query,
        conversation_history=data.conversation_history,
        override_model=override,
    )

    return ChatResponse(
        response=result["response"],
        model_used=result["model_used"],
        tools_called=result["tools_called"],
        iterations=len([m for m in result.get("conversation", []) if m.get("role") == "assistant"]),
    )


@router.get("/status", summary="Check AI agent status")
async def status():
    """Check if the AI agent is ready (Ollama is reachable)."""
    import httpx
    try:
        response = httpx.get("http://host.docker.internal:11434/api/tags", timeout=5)
        models = response.json().get("models", [])
        return {
            "status": "ready",
            "ollama_reachable": True,
            "available_models": [m["name"] for m in models],
        }
    except Exception as e:
        return {
            "status": "error",
            "ollama_reachable": False,
            "error": str(e),
        }
