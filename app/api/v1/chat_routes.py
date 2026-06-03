"""Chat and messaging API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status, Response
from app.core.dependencies import get_chat_service, get_current_user
from app.schemas.chat_schema import ChatRequest, ChatResponse, ConversationListResponse, MessageHistoryResponse
from app.services.chat_service import ChatService
from app.models.user_model import User

router = APIRouter(prefix="/chat", tags=["Chat"])



@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def send_message(
    request: ChatRequest,
    chat_svc: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """Send a message to the AI ChatBOT and get a SQL & visualization response."""
    return await chat_svc.process_message(
        user_id=current_user.id,
        message=request.message,
        conversation_id=request.conversation_id,
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    chat_svc: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_current_user),
) -> ConversationListResponse:
    """List all chat conversations for the current logged-in user."""
    return await chat_svc.list_conversations(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.get("/conversations/{conversation_id}", response_model=MessageHistoryResponse)
async def get_conversation_history(
    conversation_id: int,
    chat_svc: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_current_user),
) -> MessageHistoryResponse:
    """Get the full message history for a specific conversation."""
    return await chat_svc.get_conversation_history(
        user_id=current_user.id,
        conversation_id=conversation_id,
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_conversation(
    conversation_id: int,
    chat_svc: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Delete a conversation and all its messages."""
    await chat_svc.delete_conversation(
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


