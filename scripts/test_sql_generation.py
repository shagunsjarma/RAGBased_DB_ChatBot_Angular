"""Script to test SQL generation directly with Gemini."""

from __future__ import annotations

import asyncio
import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import get_settings
from app.services.llm_service import LLMService
from app.agents.sql_generation_agent import SQLGenerationAgent
from app.agents.sql_validation_agent import SQLValidationAgent


async def test_sql_gen(query: str, schema_context: str | None = None) -> None:
    settings = get_settings()
    
    print(f"Testing SQL generation for query: {query!r}\n")
    
    llm = LLMService(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_MODEL,
        embedding_model=settings.EMBEDDING_MODEL,
    )
    
    agent = SQLGenerationAgent(llm_service=llm)
    validator = SQLValidationAgent()

    if not schema_context:
        schema_context = """
DATABASE SCHEMA CONTEXT:
========================================
Table: users
Columns:
  - id (INTEGER, PRIMARY KEY)
  - email (VARCHAR(255), UNIQUE)
  - role (VARCHAR(20), DEFAULT='user')
  - is_active (BOOLEAN)
  - created_at (TIMESTAMP)
----------------------------------------
Table: sales
Columns:
  - id (INTEGER, PRIMARY KEY)
  - user_id (INTEGER, FOREIGN KEY -> users.id)
  - amount (DECIMAL(10,2))
  - region (VARCHAR(50))
  - created_at (TIMESTAMP)
----------------------------------------
"""

    print("Generating SQL query via Gemini SQL Agent...")
    result = await agent.generate_sql(query, schema_context)
    print("-" * 50)
    print("Generated SQL Query:")
    print(result.sql_query)
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Explanation: {result.explanation}")
    print("-" * 50)

    print("\nValidating SQL query safety & syntax...")
    validation = await validator.validate(result.sql_query)
    print(f"Is Valid:   {validation.is_valid}")
    if validation.errors:
        print(f"Errors:     {validation.errors}")
    if validation.warnings:
        print(f"Warnings:   {validation.warnings}")
    if validation.sanitized_sql:
        print(f"Sanitized SQL:\n{validation.sanitized_sql}")
    print("-" * 50)


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Total sales amount in West region by active users"
    asyncio.run(test_sql_gen(query))
