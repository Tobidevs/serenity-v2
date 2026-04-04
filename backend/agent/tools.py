import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
from langgraph.prebuilt import InjectedState
from typing import Annotated, Any

from .utils import (
    _build_filter,
    _format_bible_output,
    build_domains,
    tavily_search_multiple,
    deduplicate_search_results,
    process_search_results,
    format_search_output,
)
from .state import WebSearchInput, BibleRAGInput, ClarifyInput, AgentState

load_dotenv()

_embeddings: OpenAIEmbeddings | None = None
_index: Any | None = None


def _get_bible_clients() -> tuple[OpenAIEmbeddings, Any]:
    """Lazily initialize and cache Bible RAG dependencies."""
    global _embeddings, _index

    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    if _index is None:
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        if not pinecone_api_key:
            raise RuntimeError(
                "Missing required environment variable: PINECONE_API_KEY"
            )

        pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "bible-rag")
        _index = Pinecone(api_key=pinecone_api_key).Index(pinecone_index_name)

    return _embeddings, _index


@tool(args_schema=WebSearchInput)
async def web_search(
    queries: list[str], resolved_query: str, denomination: str, mode: str
) -> str:
    """Search curated theological sources for commentary, patristic texts,
    and doctrinal resources filtered by the active denomination."""

    domains = build_domains(denomination, mode)

    search_results = await tavily_search_multiple(
        queries,
        search_depth=os.getenv("TAVILY_SEARCH_DEPTH"),
        chunks_per_source=os.getenv("TAVILY_CHUNKS_PER_SOURCE"),
        include_domains=domains,
        include_raw_content=False,
    )

    unique_results = deduplicate_search_results(search_results)

    processed_results = await process_search_results(
        unique_results, use_summarizations=False
    )

    return format_search_output(processed_results)


@tool(args_schema=BibleRAGInput)
async def bible_rag(
    queries: list[str],
    state: Annotated[AgentState, InjectedState],
    translation: str | None = None,
    testament: str | None = None,
    genre: str | None = None,
    top_k: int = 3,
) -> str:
    """
    Retrieve relevant Bible passages from the Pinecone vector index.
    Use for questions about specific verses, passages, biblical themes, or theology.
    Combine with web_search in most cases for denomination-aware context.
    """
    
    pinecone_filter = _build_filter(
        translation=translation,
        testament=testament,
        genre=genre,
    )

    embeddings, index = _get_bible_clients()

    all_results = []

    for query in queries:
        vector = await embeddings.aembed_query(query)

        response = index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            filter=pinecone_filter if pinecone_filter else None,
        )

        for match in response.matches:
            meta = match.metadata
            all_results.append(
                {
                    "score": match.score,
                    "reference": meta.get("reference", ""),
                    "book": meta.get("book", ""),
                    "chapter": meta.get("chapter", ""),
                    "start_verse": meta.get("start_verse", ""),
                    "end_verse": meta.get("end_verse", ""),
                    "testament": meta.get("testament", ""),
                    "translation": meta.get("translation", ""),
                    "genre": meta.get("genre", ""),
                    "text": meta.get("text", ""),
                }
            )

    seen = set()
    unique_results = []
    for r in all_results:
        key = (
            r["book"],
            r["chapter"],
            r["start_verse"],
            r["end_verse"],
            r["translation"],
        )
        if key not in seen:
            seen.add(key)
            unique_results.append(r)

    unique_results.sort(key=lambda x: x["score"], reverse=True)

    return _format_bible_output(unique_results)


@tool(args_schema=ClarifyInput)
def request_clarification(question: str) -> str:
    """Ask the user a clarifying question when their query is too ambiguous
    to search. Mutually exclusive with web_search and bible_rag — never
    call this alongside a search tool."""
    ...
