"""Integration tests for Chat API endpoints using TestClient."""

from __future__ import annotations

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.core.dependencies import get_chat_service, get_current_user
from app.schemas.chat_schema import ChatResponse
from app.models.user_model import User


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_chat_endpoint_unauthorized(client: TestClient) -> None:
    # No Auth headers -> should return 401
    response = client.post("/api/v1/chat", json={"message": "Show sales"})
    assert response.status_code == 401
    assert "detail" in response.json()


def test_chat_endpoint_authorized(client: TestClient) -> None:
    # Mock current user
    mock_user = User(
        id=42,
        email="test@example.com",
        role="user",
        is_active=True,
    )
    
    # Mock chat service
    mock_chat_svc = AsyncMock()
    mock_chat_svc.process_message.return_value = ChatResponse(
        message="Here is the breakdown of sales",
        conversation_id=99,
        sql_query="SELECT region, SUM(sales) FROM sales GROUP BY region",
        query_results=[{"region": "North", "sales": 100}],
    )

    # Override dependencies
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_chat_service] = lambda: mock_chat_svc

    try:
        response = client.post("/api/v1/chat", json={"message": "Show sales", "conversation_id": 99})
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Here is the breakdown of sales"
        assert data["conversation_id"] == 99
        assert data["sql_query"] == "SELECT region, SUM(sales) FROM sales GROUP BY region"
        assert data["query_results"] == [{"region": "North", "sales": 100}]
        
    finally:
        # Clear overrides
        app.dependency_overrides.clear()
