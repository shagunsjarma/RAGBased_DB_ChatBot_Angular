"""LangGraph state definition for the orchestration pipeline."""

from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict, total=False):
    # Inputs
    user_message: str
    user_id: int
    conversation_id: int
    chat_history: Optional[List[Dict[str, str]]]
    
    # State tracking
    intent_type: Optional[str]
    intent_confidence: Optional[float]
    schema_context: Optional[str]
    
    # SQL Generation & Validation
    sql_query: Optional[str]
    tables_used: Optional[List[str]]
    validation_errors: Optional[List[str]]
    validation_warnings: Optional[List[str]]
    is_valid_sql: Optional[bool]
    
    # Execution & Results
    query_results: Optional[List[Dict[str, Any]]]
    query_columns: Optional[List[str]]
    row_count: Optional[int]
    execution_error: Optional[str]
    
    # Artifacts
    visualizations: Optional[List[Dict[str, Any]]]
    insights: Optional[Dict[str, Any]]
    
    # Outputs
    final_message: Optional[str]
    follow_up_suggestions: Optional[List[str]]
