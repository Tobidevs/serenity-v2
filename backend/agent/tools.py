import os
from typing import Annotated, Literal
from dotenv import load_dotenv

from langchain_core.tools import tool, InjectedToolArg

from .utils import (
    tavily_search_multiple,
    deduplicate_search_results,
    process_search_results,
    format_search_output,
)

load_dotenv()


@tool(parse_docstring=True)
async def tavily_search(
    query: str,
    max_results: Annotated[int, InjectedToolArg] = 3,
    topics: Annotated[
        Literal["general", "news", "finance"], InjectedToolArg
    ] = "general",
) -> str:
    """
    Fetch results from Tavily Search API with content summarization

    Args:
        query: The search query string to execute against the Tavily API.
        max_results: Maximum number of search results to retrieve.
        topics: Topic filter for search results, can be "general", "news", or "finance".

    Returns:
        A list of dictionaries containing the search results from the Tavily API.
    """
    search_results = await tavily_search_multiple(
        [query],
        max_results=max_results,
        search_depth=os.getenv("TAVILY_SEARCH_DEPTH"),
        chunks_per_source=os.getenv("TAVILY_CHUNKS_PER_SOURCE"),
        topic=topics,
        include_raw_content=False,
    )

    unique_results = deduplicate_search_results(search_results)

    processed_results = await process_search_results(
        unique_results, use_summarizations=False
    )

    return format_search_output(processed_results)


@tool(parse_docstring=True)
def think_tool(reflection: str) -> dict:
    """Reflect on research progress and plan next steps.

    Args:
        reflection: Analysis of current findings, gaps, and whether to continue searching

    """
    return "Reflection recorded"
