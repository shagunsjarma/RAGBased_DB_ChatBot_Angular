"""Orchestration agent – central pipeline coordinator using LangGraph."""

from __future__ import annotations

import json
import time
import asyncio
from typing import Any, Literal

from langgraph.graph import StateGraph, END
from app.agents.graph_state import AgentState
from app.agents.intent_agent import IntentAgent, IntentResult
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.sql_generation_agent import SQLGenerationAgent
from app.agents.sql_validation_agent import SQLValidationAgent
from app.agents.visualization_agent import VisualizationAgent
from app.agents.insight_agent import InsightAgent
from app.agents.summarization_agent import SummarizationAgent
from app.core.constants import IntentType
from app.schemas.chat_schema import ChatResponse, VisualizationData
from app.core.logger import get_logger
from app.observability.eval import PipelineEvaluator

logger = get_logger(__name__)


class OrchestrationAgent:
    """Routes user messages through the full agent pipeline using LangGraph."""

    def __init__(
        self,
        intent_agent: IntentAgent,
        retrieval_agent: RetrievalAgent,
        sql_generation_agent: SQLGenerationAgent,
        sql_validation_agent: SQLValidationAgent,
        visualization_agent: VisualizationAgent,
        insight_agent: InsightAgent,
        summarization_agent: SummarizationAgent,
        sql_service,
        cache_service,
    ) -> None:
        self._intent = intent_agent
        self._retrieval = retrieval_agent
        self._sql_gen = sql_generation_agent
        self._sql_val = sql_validation_agent
        self._viz = visualization_agent
        self._insight = insight_agent
        self._summary = summarization_agent
        self._sql_svc = sql_service
        self._cache_svc = cache_service
        self._evaluator = PipelineEvaluator()

        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("classify_intent", self.node_classify_intent)
        workflow.add_node("retrieve_context", self.node_retrieve_context)
        workflow.add_node("generate_sql", self.node_generate_sql)
        workflow.add_node("validate_sql", self.node_validate_sql)
        workflow.add_node("execute_query", self.node_execute_query)
        workflow.add_node("generate_visualizations", self.node_generate_visualizations)
        workflow.add_node("generate_insights", self.node_generate_insights)
        workflow.add_node("summarize_response", self.node_summarize_response)

        # Edges
        workflow.set_entry_point("classify_intent")

        workflow.add_conditional_edges(
            "classify_intent",
            self.route_after_intent,
            {
                "SQL_GENERATION": "retrieve_context",
                "GENERAL_QUESTION": "summarize_response"
            }
        )
        
        workflow.add_edge("retrieve_context", "generate_sql")
        workflow.add_edge("generate_sql", "validate_sql")

        workflow.add_conditional_edges(
            "validate_sql",
            self.route_after_validation,
            {
                "VALID": "execute_query",
                "INVALID": "summarize_response",
                "RETRY": "generate_sql"
            }
        )

        workflow.add_conditional_edges(
            "execute_query",
            self.route_after_execution,
            {
                "SUCCESS": "generate_visualizations",
                "ERROR": "summarize_response"
            }
        )

        workflow.add_edge("generate_visualizations", "generate_insights")
        workflow.add_edge("generate_insights", "summarize_response")
        workflow.add_edge("summarize_response", END)

        return workflow.compile()

    # --- Nodes ---

    async def node_classify_intent(self, state: AgentState) -> AgentState:
        intent = await self._intent.classify_intent(state["user_message"], state.get("chat_history"))
        logger.info("intent_classified", intent=intent.intent_type.value, confidence=intent.confidence)
        return {"intent_type": intent.intent_type.value, "intent_confidence": intent.confidence}

    async def node_retrieve_context(self, state: AgentState) -> AgentState:
        # Mock IntentResult for retrieval signature compatibility
        class MockIntent:
            intent_type = IntentType(state["intent_type"])
            confidence = state["intent_confidence"]
        
        schema_context = await self._retrieval.retrieve_context(MockIntent(), state.get("chat_history"))
        return {"schema_context": schema_context}

    async def node_generate_sql(self, state: AgentState) -> AgentState:
        user_msg = state["user_message"]
        if state.get("validation_errors"):
            user_msg += f"\n\nPrevious attempt failed. Errors: {'; '.join(state['validation_errors'])}"
            
        sql_result = await self._sql_gen.generate_sql(
            user_msg, state["schema_context"], state.get("chat_history")
        )
        return {"sql_query": sql_result.sql_query, "tables_used": sql_result.tables_used}

    async def node_validate_sql(self, state: AgentState) -> AgentState:
        if not state.get("sql_query"):
            return {"is_valid_sql": False, "validation_errors": ["No SQL query generated."]}
            
        validation = await self._sql_val.validate(state["sql_query"])
        return {
            "is_valid_sql": validation.is_valid,
            "validation_errors": validation.errors,
            "validation_warnings": validation.warnings,
            "sql_query": validation.sanitized_sql or state["sql_query"]
        }

    async def node_execute_query(self, state: AgentState) -> AgentState:
        try:
            exec_result = await self._sql_svc.execute_query(state["sql_query"])
            return {
                "query_results": exec_result.rows,
                "query_columns": exec_result.columns,
                "row_count": exec_result.row_count
            }
        except Exception as exc:
            logger.error("sql_execution_failed", error=str(exc))
            return {"execution_error": str(exc), "query_results": [], "query_columns": [], "row_count": 0}

    async def node_generate_visualizations(self, state: AgentState) -> AgentState:
        if not state.get("query_results"):
            return {"visualizations": []}
            
        try:
            viz_configs = await self._viz.select_visualizations(
                state["user_message"], state["query_columns"], 
                state["query_results"][:100], state["row_count"]
            )
            visualizations = [
                VisualizationData(
                    chart_type=v.get("chart_type", "bar"),
                    chart_config=v,
                    title=v.get("title"),
                ).model_dump()
                for v in viz_configs
            ]
            return {"visualizations": visualizations}
        except Exception as exc:
            logger.warning("visualization_failed", error=str(exc))
            return {"visualizations": []}

    async def node_generate_insights(self, state: AgentState) -> AgentState:
        if not state.get("query_results"):
            return {"insights": {}}
            
        try:
            insights = await self._insight.generate_insights(
                state["user_message"], state["query_columns"], 
                state["query_results"], state["sql_query"]
            )
            return {"insights": insights.model_dump()}
        except Exception as exc:
            logger.warning("insight_generation_failed", error=str(exc))
            return {"insights": {}}

    async def node_summarize_response(self, state: AgentState) -> AgentState:
        if state.get("intent_type") in (IntentType.GENERAL_QUESTION.value, IntentType.CLARIFICATION.value):
            reply = await self._summary.summarize_response(
                sql="", results_summary=state["user_message"],
                insights={}, chart_descriptions=[]
            )
            return {"final_message": reply}

        if not state.get("is_valid_sql") and state.get("sql_query") == "":
            return {"final_message": "I couldn't generate a SQL query for your request. Could you rephrase?"}
            
        if state.get("validation_errors") and not state.get("is_valid_sql"):
            error_detail = "; ".join(state["validation_errors"])
            return {"final_message": f"Generated SQL failed validation: {error_detail}"}

        if state.get("execution_error"):
            return {"final_message": f"SQL execution failed: {state['execution_error']}"}

        results_summary = (
            f"Query returned {state.get('row_count', 0)} rows with columns: "
            f"{', '.join(state.get('query_columns', []))}."
        )
        
        visualizations = state.get("visualizations", [])
        chart_descs = [v.get("title") or v.get("chart_type") for v in visualizations]

        message = await self._summary.summarize_response(
            sql=state.get("sql_query", ""),
            results_summary=results_summary,
            insights=state.get("insights", {}),
            chart_descriptions=chart_descs,
        )

        follow_ups = await self._summary.generate_follow_ups(
            state["user_message"], results_summary, state.get("chat_history")
        )

        return {"final_message": message, "follow_up_suggestions": follow_ups}

    # --- Routers ---

    def route_after_intent(self, state: AgentState) -> str:
        if state["intent_type"] in (IntentType.GENERAL_QUESTION.value, IntentType.CLARIFICATION.value):
            return "GENERAL_QUESTION"
        return "SQL_GENERATION"

    def route_after_validation(self, state: AgentState) -> str:
        if state.get("is_valid_sql"):
            return "VALID"
        # Optional: implement retry logic based on a counter in state. For now, fail out.
        return "INVALID"

    def route_after_execution(self, state: AgentState) -> str:
        if state.get("execution_error"):
            return "ERROR"
        return "SUCCESS"

    async def process_message(
        self,
        user_message: str,
        user_id: int,
        conversation_id: int = 0,
        chat_history: list[dict[str, str]] | None = None,
    ) -> ChatResponse:
        t0 = time.perf_counter()
        
        # Check cache before running graph
        if self._cache_svc:
            cached = await self._cache_svc.get_cached_result(user_message)
            if cached:
                logger.info("cache_hit", query=user_message[:80])
                return ChatResponse(**cached, conversation_id=conversation_id)

        initial_state: AgentState = {
            "user_message": user_message,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "chat_history": chat_history,
            "validation_errors": [],
            "visualizations": [],
            "insights": {},
            "query_results": []
        }

        # Execute LangGraph
        final_state = await self.graph.ainvoke(initial_state)

        elapsed = round((time.perf_counter() - t0) * 1000, 1)
        logger.info("pipeline_complete", duration_ms=elapsed)

        # Convert visualizations dicts back to VisualizationData objects for ChatResponse
        viz_data = None
        if final_state.get("visualizations"):
            viz_data = [VisualizationData(**v) for v in final_state["visualizations"]]
            
        # Insights is returned as a dict, we can pass it directly since ChatResponse schemas accept it or we might need to parse.
        # Assuming ChatResponse schema accepts dict for insights.

        response = ChatResponse(
            message=final_state.get("final_message", ""),
            conversation_id=conversation_id,
            sql_query=final_state.get("sql_query"),
            query_results=final_state.get("query_results", [])[:500],
            visualizations=viz_data,
            insights=final_state.get("insights"),
            follow_up_suggestions=final_state.get("follow_up_suggestions")
        )

        if self._cache_svc:
            try:
                await self._cache_svc.cache_result(
                    user_message, response.model_dump(exclude={"conversation_id"}),
                )
            except Exception:
                pass

        # Trigger Evaluation Background Task for DTDL
        asyncio.create_task(self._evaluator.run_full_evaluation(final_state))
        
        return response
