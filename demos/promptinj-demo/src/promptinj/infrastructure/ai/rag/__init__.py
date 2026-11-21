"""Retrieval-augmented assistants: spec, builder, graph and adapter."""
from .builder import build_rag_assistant
from .deps import RagDeps
from .spec import Delimiters, RagSpec, RetrievalConfig

__all__ = ["Delimiters", "RagDeps", "RagSpec", "RetrievalConfig", "build_rag_assistant"]
