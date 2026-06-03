"""Chat service – conversation management and pipeline orchestration."""

from __future__ import annotations

from app.agents.orchestration_agent import OrchestrationAgent
from app.agents.summarization_agent import SummarizationAgent
from app.core.exceptions import NotFoundError
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat_schema import (
    ChatResponse, ConversationListResponse, ConversationResponse,
    MessageHistoryResponse, MessageResponse,
)


class ChatService:
    def __init__(self, chat_repo: ChatRepository,
                 orchestration_agent: OrchestrationAgent,
                 summarization_agent: SummarizationAgent) -> None:
        self._repo = chat_repo
        self._orchestrator = orchestration_agent
        self._summarizer = summarization_agent

    async def process_message(self, user_id: int, message: str,
                               conversation_id: int | None = None) -> ChatResponse:
        # Create or fetch conversation
        if conversation_id:
            conv = await self._repo.get_conversation(conversation_id, user_id)
            if not conv:
                raise NotFoundError("Conversation not found")
        else:
            title = await self._summarizer.generate_title(message)
            conv = await self._repo.create_conversation(user_id, title=title)
            conversation_id = conv.id

        # Save user message
        await self._repo.add_message(conversation_id, role="user", content=message)

        # Get recent history for context
        recent = await self._repo.get_recent_messages(conversation_id, limit=10)
        chat_history = [{"role": m.role, "content": m.content} for m in recent]

        # Run the pipeline
        response = await self._orchestrator.process_message(
            user_message=message, user_id=user_id,
            conversation_id=conversation_id, chat_history=chat_history,
        )

        # Save assistant response
        await self._repo.add_message(
            conversation_id, role="assistant", content=response.message,
            metadata_json={"sql_query": response.sql_query} if response.sql_query else None,
        )

        response.conversation_id = conversation_id
        return response

    async def list_conversations(self, user_id: int, page: int = 1,
                                  page_size: int = 20) -> ConversationListResponse:
        skip = (page - 1) * page_size
        convs, total = await self._repo.list_conversations(user_id, skip=skip, limit=page_size)
        items = []
        for c in convs:
            count = await self._repo.get_message_count(c.id)
            items.append(ConversationResponse(
                id=c.id, title=c.title, message_count=count,
                created_at=c.created_at, updated_at=c.updated_at,
            ))
        return ConversationListResponse(conversations=items, total=total)

    async def get_conversation_history(self, user_id: int,
                                        conversation_id: int) -> MessageHistoryResponse:
        conv = await self._repo.get_conversation(conversation_id, user_id)
        if not conv:
            raise NotFoundError("Conversation not found")
        msgs = await self._repo.get_messages(conversation_id)
        return MessageHistoryResponse(
            conversation_id=conversation_id, title=conv.title,
            messages=[MessageResponse.model_validate(m) for m in msgs],
        )

    async def delete_conversation(self, user_id: int, conversation_id: int) -> bool:
        deleted = await self._repo.delete_conversation(conversation_id, user_id)
        if not deleted:
            raise NotFoundError("Conversation not found")
        return True
