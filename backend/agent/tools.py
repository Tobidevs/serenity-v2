import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from .utils import (
    build_domains,
    tavily_search_multiple,
    deduplicate_search_results,
    process_search_results,
    format_search_output,
)
from .state import WebSearchInput, BibleRAGInput, ClarifyInput

load_dotenv()



@tool(args_schema=WebSearchInput)
async def web_search(queries: list[str], resolved_query: str, denomination: str, mode: str) -> str:
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
def bible_rag(topic: str) -> str:
    """Retrieve semantically relevant Bible verses for the current topic
    from the vector store."""
    ...


@tool(args_schema=ClarifyInput)
def request_clarification(question: str) -> str:
    """Ask the user a clarifying question when their query is too ambiguous
    to search. Mutually exclusive with web_search and bible_rag — never
    call this alongside a search tool."""
    ...

