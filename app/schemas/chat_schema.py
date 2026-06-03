"""Chat request/response schemas."""

from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: int | None = None


class VisualizationData(BaseModel):
    chart_type: str
    chart_config: dict[str, Any]
    title: str | None = None


class InsightData(BaseModel):
    summary: str
    trends: list[str] = []
    anomalies: list[str] = []
    recommendations: list[str] = []


class ChatResponse(BaseModel):
    message: str
    conversation_id: int
    sql_query: str | None = None
    query_results: list[dict[str, Any]] | None = None
    visualizations: list[VisualizationData] | None = None
    insights: InsightData | None = None
    follow_up_suggestions: list[str] | None = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None = None
    message_count: int = 0
    created_at: dt.datetime
    updated_at: dt.datetime | None = None


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
    total: int


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    metadata_json: dict[str, Any] | None = None
    created_at: dt.datetime


class MessageHistoryResponse(BaseModel):
    conversation_id: int
    title: str | None = None
    messages: list[MessageResponse]
