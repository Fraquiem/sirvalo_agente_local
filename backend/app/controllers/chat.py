from __future__ import annotations

from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.agents.cocktail_agent import build_agent_graph
from app.dependencies import AuthenticatedUser, current_user
from app.services.vectorstore import get_conversation, list_conversations, list_messages, list_recent_messages

router = APIRouter(tags=["chat", "conversations"])
_graph = build_agent_graph()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: UUID | None = None

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question must not be blank")
        return value


class ChatResponse(BaseModel):
    conversation_id: UUID
    answer: str
    context_sufficient: bool
    sources: list[dict] = Field(default_factory=list)


@router.post("/chat/query", response_model=ChatResponse)
async def query_agent(request: ChatRequest, user: AuthenticatedUser = Depends(current_user)) -> ChatResponse:
    history: list[dict] = []
    if request.conversation_id:
        try:
            conversation = await get_conversation(conversation_id=str(request.conversation_id), token=user.access_token)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            history = await list_recent_messages(
                conversation_id=str(request.conversation_id),
                token=user.access_token,
                limit=8,
            )
        except HTTPException:
            raise
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=503, detail="Conversation store unavailable") from exc
    try:
        result = await _graph.ainvoke(
            {
                "question": request.question,
                "user_id": user.id,
                "access_token": user.access_token,
                "conversation_id": str(request.conversation_id) if request.conversation_id else None,
                "conversation_history": history,
            }
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Chat provider unavailable") from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Chat provider unavailable") from exc
    return ChatResponse(
        conversation_id=UUID(str(result["conversation_id"])),
        answer=result["response"],
        context_sufficient=bool(result.get("is_context_sufficient")),
        sources=result.get("sources", []),
    )


@router.get("/conversations")
async def conversations(user: AuthenticatedUser = Depends(current_user)) -> dict:
    try:
        return {"items": await list_conversations(token=user.access_token)}
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Conversation store unavailable") from exc


@router.get("/conversations/{conversation_id}/messages")
async def conversation_messages(conversation_id: UUID, user: AuthenticatedUser = Depends(current_user)) -> dict:
    try:
        conversation = await get_conversation(conversation_id=str(conversation_id), token=user.access_token)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"conversation_id": conversation_id, "items": await list_messages(conversation_id=str(conversation_id), token=user.access_token)}
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Conversation store unavailable") from exc
