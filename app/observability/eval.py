"""Evaluation module integrating RAGAS and LLM-as-judge for pipeline assessment."""

from __future__ import annotations

import os
from typing import Dict, Any, List

from langsmith import traceable
from langchain_google_genai import ChatGoogleGenerativeAI
from datasets import Dataset

from ragas import evaluate
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy,
)

from app.core.logger import get_logger

logger = get_logger(__name__)


class PipelineEvaluator:
    """Evaluates the generation pipeline using RAGAS and custom LLM-as-judge metrics."""

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self._llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.0)

    @traceable(name="ragas_evaluation")
    async def evaluate_ragas(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: str = ""
    ) -> Dict[str, float]:
        """Calculates RAGAS metrics for a single query."""
        
        # Ragas expects a dataset
        data = {
            "question": [question],
            "answer": [answer],
            "contexts": [contexts],
        }
        if ground_truth:
            data["ground_truth"] = [ground_truth]
            
        dataset = Dataset.from_dict(data)
        
        # Select metrics based on availability of ground_truth
        metrics = [faithfulness, answer_relevancy, context_precision]
        if ground_truth:
            metrics.append(context_recall)

        try:
            # We use evaluate without passing llm explicitely if standard env vars are set,
            # or configure ragas to use the Gemini model.
            result = evaluate(
                dataset=dataset,
                metrics=metrics,
                llm=self._llm,
                raise_exceptions=False
            )
            return dict(result)
        except Exception as exc:
            logger.error("ragas_evaluation_failed", error=str(exc))
            return {}

    @traceable(name="llm_as_judge_sql")
    async def evaluate_sql_correctness(self, question: str, sql_query: str, schema_context: str) -> Dict[str, Any]:
        """Uses LLM-as-judge to determine if the generated SQL correctly answers the question."""
        
        prompt = f"""You are an expert SQL judge. Your task is to evaluate if the provided SQL query correctly and safely answers the user's question given the schema context.
        
        USER QUESTION: {question}
        
        SCHEMA CONTEXT:
        {schema_context}
        
        GENERATED SQL:
        {sql_query}
        
        Respond ONLY with a JSON object containing two fields:
        - "score": An integer from 0 to 10 (10 being perfect).
        - "reason": A brief explanation of why this score was given.
        """
        
        try:
            response = await self._llm.ainvoke(prompt)
            content = response.content.strip()
            
            # Clean up markdown JSON formatting if present
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
                
            import json
            result = json.loads(content)
            return {
                "sql_correctness_score": result.get("score", 0) / 10.0,
                "sql_correctness_reason": result.get("reason", "")
            }
        except Exception as exc:
            logger.error("llm_as_judge_failed", error=str(exc))
            return {"sql_correctness_score": 0.0, "sql_correctness_reason": f"Evaluation failed: {exc}"}

    @traceable(name="full_pipeline_evaluation")
    async def run_full_evaluation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Runs all evaluations on the final LangGraph state."""
        question = state.get("user_message", "")
        answer = state.get("final_message", "")
        contexts = [state.get("schema_context", "")] if state.get("schema_context") else []
        sql_query = state.get("sql_query", "")
        
        results = {}
        
        # 1. RAGAS
        if answer and contexts:
            ragas_scores = await self.evaluate_ragas(question, answer, contexts)
            results.update(ragas_scores)
            
        # 2. LLM as Judge (SQL)
        if sql_query and contexts:
            sql_scores = await self.evaluate_sql_correctness(question, sql_query, contexts[0])
            results.update(sql_scores)
            
        logger.info("pipeline_evaluation_completed", scores=results)
        return results
