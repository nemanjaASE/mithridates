"""Composition root: chooses the concrete classes and wires them to the use cases."""
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from .application.ports import (
    AccountRepository,
    AuditLog,
    CredentialStore,
    DocumentRetriever,
    OutputFilter,
)
from .application.use_cases import AskAssistantUseCase, LoginUseCase
from .config import Settings

if TYPE_CHECKING:  # importing these eagerly would pull in langchain and psycopg
    from .infrastructure.ai.rag import RagSpec
    from .infrastructure.ai.registry import AssistantRegistry
    from .infrastructure.db.factory import Stores
    from .infrastructure.llm.factory import LLMFactory

from .infrastructure.audit.logging_audit_log import LoggingAuditLog
from .infrastructure.security.authentication.jwt_service import JwtService
from .infrastructure.security.authentication.password_hasher import BcryptPasswordHasher


@dataclass(frozen=True)
class Adapters:
    """Pre-built adapters that replace the ones the container would construct."""

    repository: AccountRepository | None = None
    credential_store: CredentialStore | None = None
    retriever: DocumentRetriever | None = None
    llm_factory: LLMFactory | None = None


@dataclass(frozen=True)
class Container:
    """The use cases and the description the HTTP layer needs."""

    settings: Settings
    backend: dict[str, object]
    jwt_service: JwtService
    login_use_case: LoginUseCase
    ask_use_case: AskAssistantUseCase
    assistants: Mapping[str, str]


def _label(override: object | None, real: str) -> str:
    """Returns the backend name, or `test-double` when it was replaced."""
    return real if override is None else "test-double"


def _build_stores(settings: Settings, adapters: Adapters) -> Stores | None:
    """Builds the account, credential and document stores.

    Returns:
        The stores, or None when every store is replaced.
    """
    if adapters.repository and adapters.credential_store and adapters.retriever:
        return None
    from .infrastructure.db.factory import PersistenceFactory

    factory = PersistenceFactory(settings.persistence)
    return factory.stores(settings.database, settings.app_db)


def _build_retriever(
    settings: Settings, stores: Stores | None, override: DocumentRetriever | None
) -> DocumentRetriever:
    """Builds the retriever: question to vector to nearest documents."""
    if override is not None:
        return override
    from .infrastructure.embeddings.factory import EmbedderFactory
    from .infrastructure.retrieval.vector_retriever import VectorRetriever

    return VectorRetriever(stores.documents, EmbedderFactory(settings.embeddings).build())


def _build_llm_factory(settings: Settings, override: LLMFactory | None) -> LLMFactory:
    """Builds the factory that resolves a model role to a chat model."""
    if override is not None:
        return override
    from .infrastructure.llm.factory import LLMFactory

    return LLMFactory(settings.models)


def _output_filters() -> dict[str, OutputFilter]:
    """Returns the output filters a RAG spec may name."""
    from .infrastructure.output_filters.card_number_filter import CardNumberFilter

    return {"card_number": CardNumberFilter()}


def _build_registry(
    settings: Settings,
    adapters: Adapters,
    repository: AccountRepository,
    retriever: DocumentRetriever,
    audit: AuditLog,
) -> AssistantRegistry:
    """Builds every assistant and registers it by name.

    Returns:
        The registry.
    """
    from functools import partial

    from .assistants import account_demo
    from .infrastructure.ai.agent import AgentDeps, build_tool_agent
    from .infrastructure.ai.common.prompts import PromptLoader
    from .infrastructure.ai.rag import RagDeps, build_rag_assistant
    from .infrastructure.ai.registry import AssistantRegistry

    prompts = PromptLoader(account_demo.PROMPTS_DIR)
    llm = _build_llm_factory(settings, adapters.llm_factory)
    registry = AssistantRegistry()

    rag_deps = RagDeps(
        llm=llm, prompts=prompts, retriever=retriever, output_filters=_output_filters()
    )
    for spec in account_demo.RAG_SPECS:
        # `rag_top_k` is deployment-level, so it is applied here rather than duplicated
        # in every spec; everything else about an assistant stays in its spec file.
        spec = _with_top_k(spec, settings.rag_top_k)
        registry.register(
            spec.name, spec.description, partial(build_rag_assistant, spec, rag_deps)
        )

    for spec in account_demo.AGENT_SPECS:
        deps = AgentDeps(
            llm=llm,
            prompts=prompts,
            tools=account_demo.account_tools(
                repository, account_demo.TOOL_POLICIES[spec.name], audit
            ),
        )
        registry.register(spec.name, spec.description, partial(build_tool_agent, spec, deps))

    return registry.build_all()


def _with_top_k(spec: RagSpec, top_k: int) -> RagSpec:
    """Returns the spec with its retrieval depth set to `top_k`."""
    return replace(spec, retrieval=replace(spec.retrieval, top_k=top_k))


def build_container(settings: Settings, adapters: Adapters | None = None) -> Container:
    """Creates the adapters, the assistants and the use cases.

    Args:
        settings: The application settings.
        adapters: Adapters to use instead of the real ones.

    Returns:
        The wired use cases.
    """
    adapters = adapters or Adapters()

    stores = _build_stores(settings, adapters)
    repository = adapters.repository or stores.accounts
    credential_store = adapters.credential_store or stores.credentials
    retriever = _build_retriever(settings, stores, adapters.retriever)
    audit = LoggingAuditLog()
    registry = _build_registry(settings, adapters, repository, retriever, audit)

    jwt_service = JwtService(settings.jwt)
    # Login reads credentials only; the agent's tool reads accounts only.
    login_use_case = LoginUseCase(credential_store, BcryptPasswordHasher(), jwt_service, audit)

    models = {
        role: _label(adapters.llm_factory, spec.describe())
        for role, spec in sorted(settings.models.items())
    }
    backend = {
        "models": models,
        "store": _label(adapters.repository, settings.persistence.backend),
        "retrieval": _label(
            adapters.retriever,
            f"{settings.persistence.backend}:{settings.embeddings.provider}:{settings.embeddings.model}",
        ),
    }
    return Container(
        settings=settings,
        backend=backend,
        jwt_service=jwt_service,
        login_use_case=login_use_case,
        ask_use_case=AskAssistantUseCase(registry),
        assistants=registry.describe(),
    )
