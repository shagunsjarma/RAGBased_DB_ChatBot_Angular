"""SQL operations API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_sql_service, get_current_user
from app.schemas.sql_schema import QueryExecutionResult, SQLExplainRequest, SQLExplainResponse
from app.services.sql_service import SQLService
from app.models.user_model import User

router = APIRouter(prefix="/sql", tags=["SQL Operations"])


@router.post("/execute", response_model=QueryExecutionResult)
async def execute_query(
    request: SQLExplainRequest,
    sql_svc: SQLService = Depends(get_sql_service),
    current_user: User = Depends(get_current_user),
) -> QueryExecutionResult:
    """Directly execute a SQL query (Admin only)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrator accounts can execute raw queries directly.",
        )
    return await sql_svc.execute_query(request.sql_query)


@router.get("/schema")
async def get_schema(
    sql_svc: SQLService = Depends(get_sql_service),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Retrieve schema definitions (tables and columns) of the MySQL database."""
    return await sql_svc.get_schema_info()


@router.post("/explain", response_model=SQLExplainResponse)
async def explain_query(
    request: SQLExplainRequest,
    sql_svc: SQLService = Depends(get_sql_service),
    current_user: User = Depends(get_current_user),
) -> SQLExplainResponse:
    """Explain a SQL query and retrieve its execution plan."""
    plan = await sql_svc.explain_query(request.sql_query)
    return SQLExplainResponse(
        explanation="Query execution plan retrieved from MySQL database.",
        execution_plan=plan,
    )
