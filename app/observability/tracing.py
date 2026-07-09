"""OpenTelemetry tracing setup."""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource


def setup_tracing(service_name: str = "rag-chatbot") -> None:
    # OpenTelemetry setup
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    
    # LangSmith / LangGraph tracing is automatically enabled if these env vars are set:
    # LANGCHAIN_TRACING_V2=true
    # LANGCHAIN_API_KEY=<your_api_key>
    # LANGCHAIN_PROJECT=rag-chatbot


def get_tracer(name: str = "rag-chatbot") -> trace.Tracer:
    return trace.get_tracer(name)
