"""RAGPipeline: query -> vector search -> retrieve -> add context -> generate."""
from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from app.core.config import get_settings
from app.core.rag.context_builder import ContextBuilder
from app.core.rag.retriever import ProjectServiceRetriever
from app.core.rag.retriever import RetrievedChunk

DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant. Answer the user's question based on the provided context.
If the context does not contain relevant information, say so clearly.
Do not make up information that is not in the context."""

DEFAULT_RAG_TEMPLATE = """Use the following context to answer the question. If the context is empty, explain that no relevant documents were found.

Context:
{context}

Question: {query}

Answer:"""


@dataclass
class RAGResponse:
    """Result of RAG pipeline execution."""
    content: str
    retrieved_count: int
    context_used: bool


class RAGPipeline:
    """RAG: User query -> vector search -> retrieve -> add context -> generate."""

    def __init__(
        self,
        retriever: ProjectServiceRetriever | None = None,
        context_builder: ContextBuilder | None = None,
    ) -> None:
        self.retriever = retriever or ProjectServiceRetriever()
        self.context_builder = context_builder or ContextBuilder()
        self.settings = get_settings()
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI | None:
        if not self.settings.openai_api_key:
            return None
        if self._client is None:
            self._client = OpenAI(
                api_key=self.settings.openai_api_key,
                base_url=self.settings.openai_base_url,
            )
        return self._client

    def run(
        self,
        query: str,
        knowledge_base_id: str,
        project_id: str,
        *,
        system_prompt: str | None = None,
        retrieve_limit: int = 10,
        model: str = "gpt-4.1-mini",
    ) -> RAGResponse:
        """Execute RAG: retrieve -> build context -> generate."""
        query = (query or "").strip()
        if not query:
            return RAGResponse(
                content="Please provide a question.",
                retrieved_count=0,
                context_used=False,
            )

        chunks = self.retriever.retrieve(
            query=query,
            knowledge_base_id=knowledge_base_id,
            project_id=project_id,
            limit=retrieve_limit,
        )

        context_str = self.context_builder.build(chunks)
        context_used = bool(context_str)

        client = self._get_client()
        if not client:
            return RAGResponse(
                content="LLM API not configured. Enable OpenAI API key for RAG generation.",
                retrieved_count=len(chunks),
                context_used=context_used,
            )

        user_message = DEFAULT_RAG_TEMPLATE.format(
            context=context_str or "(No relevant documents found.)",
            query=query,
        )
        system = (system_prompt or DEFAULT_SYSTEM_PROMPT).strip()

        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
            )
            content = (resp.choices[0].message.content or "").strip()
            return RAGResponse(
                content=content or "No response generated.",
                retrieved_count=len(chunks),
                context_used=context_used,
            )
        except Exception as e:
            return RAGResponse(
                content=f"Generation failed: {e!s}",
                retrieved_count=len(chunks),
                context_used=context_used,
            )
