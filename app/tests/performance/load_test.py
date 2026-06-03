"""Locust performance load test for the RAG chatbot APIs."""

from __future__ import annotations

import json
from locust import HttpUser, task, between


class ChatBotLoadUser(HttpUser):
    wait_time = between(1, 3)
    
    # Placeholders for session state
    token = None
    headers = {}

    def on_start(self) -> None:
        """Register/Login standard user on test startup."""
        email = "performance_user@ragchatbot.com"
        password = "PerformanceSecurePassword123!"
        
        # Try registering first
        self.client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "full_name": "Performance Tester",
        })
        
        # Get authentication token
        response = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password,
        })
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def send_chat_message(self) -> None:
        """Simulate chat messaging flow."""
        self.client.post(
            "/api/v1/chat",
            json={"message": "Show total sales by region"},
            headers=self.headers,
            name="/api/v1/chat"
        )

    @task(2)
    def view_dashboards(self) -> None:
        """Simulate listing dashboard widgets."""
        self.client.get(
            "/api/v1/dashboards",
            headers=self.headers,
            name="/api/v1/dashboards"
        )

    @task(1)
    def check_health(self) -> None:
        """Public health status check."""
        self.client.get("/api/v1/health")
