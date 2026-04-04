import asyncio
from typing import List, Literal, Annotated
from tavily import AsyncTavilyClient
from dotenv import load_dotenv
from datetime import datetime

from .config import REPOSITORIES, AVAILABLE_TRANSLATIONS, VALID_GENRES
from .prompts import SUMMARIZE_WEBPAGE_PROMPT
from .state import Summary


from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool, InjectedToolArg

load_dotenv()


tavily_async_client = AsyncTavilyClient()
model = init_chat_model(
    model="openai:gpt-4.1-nano",
    temperature=0.0,
)
# Set up structured output model for summarization
summarization_model = model.with_structured_output(Summary)


def get_todays_date():
    """Return today's date as a string."""
    return datetime.now().strftime("%a %b %-d, %Y")


async def tavily_search_multiple(
    search_queries: List[str],
    max_results: int = 3,
    search_depth: str = "advanced",
    include_domains: List[str] = None,
    chunks_per_source: int = 1,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
) -> List[dict]:
    """Perform async search using Tavily API for multiple queries.

    Args:
        search_queries: List of search queries to execute
        max_results: Maximum number of results per query
        search_depth: Depth of search to perform
        chunks_per_source: Number of chunks to retrieve per source
        topic: Topic filter for search results
        include_raw_content: Whether to include raw webpage content

    Returns:
        List of search result dictionaries
    """

    tasks = [
        tavily_async_client.search(
            query,
            max_results=max_results,
            search_depth=search_depth,
            chunks_per_source=chunks_per_source,
            include_raw_content=include_raw_content,
            topic=topic,
            include_domains=include_domains,
        )
        for query in search_queries
    ]

    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)

        search_docs = []
        for query, result in zip(search_queries, results):
            if isinstance(result, Exception):
                raise ValueError(f"Tavily search failed for query '{query}': {result}")
            else:
                search_docs.append(result)

        if not search_docs:
            raise ValueError("Tavily search returned no results for all queries.")

        return search_docs
    except Exception as exc:
        raise ValueError(f"Error during Tavily search: {exc}") from exc


def deduplicate_search_results(search_results: List[dict]) -> dict:
    """Deduplicate search results by URL to avoid processing duplicate content.

    Args:
        search_results: List of search result dictionaries

    Returns:
        Dictionary mapping URLs to unique results
    """
    unique_results = {}

    for response in search_results:
        for result in response["results"]:
            url = result["url"]
            if url not in unique_results:
                unique_results[url] = result

    return unique_results


def summarize_webpage_content(webpage_content: str) -> str:
    """Summarize webpage content using the configured summarization model.

    Args:
        webpage_content: Raw webpage content to summarize

    Returns:
        Formatted summary with key excerpts
    """
    try:
        # Generate summary
        summary = summarization_model.invoke(
            [
                HumanMessage(
                    content=SUMMARIZE_WEBPAGE_PROMPT.format(
                        webpage_content=webpage_content, date=get_todays_date()
                    )
                )
            ]
        )

        # Format summary with clear structure
        formatted_summary = (
            f"<summary>\n{summary.summary}\n</summary>\n\n"
            f"<key_excerpts>\n{summary.key_excerpts}\n</key_excerpts>"
        )

        return formatted_summary

    except Exception as e:
        print(f"Failed to summarize webpage: {str(e)}")
        return (
            webpage_content[:1000] + "..."
            if len(webpage_content) > 1000
            else webpage_content
        )


async def process_search_results(
    unique_results: dict, use_summarizations: bool = False
) -> dict:
    """Process search results by summarizing content where available.

    Args:
        unique_results: Dictionary of unique search results
        use_summarizations: Whether to use summarization (default: True)

    Returns:
        Dictionary of processed search results with summaries where applicable
    """
    # Old synchronous version for reference:
    # summarized_results = {}

    # for url, result in unique_results.items():
    #     # Use existing content if no raw content for summarization
    #     if not result.get("raw_content"):
    #         content = result["content"]
    #     else:
    #         # Summarize raw content for better processing
    #         content = summarize_webpage_content(result["raw_content"])

    #     summarized_results[url] = {"title": result["title"], "content": content}

    # return summarized_results

    processed_results = {}

    # If summarization is disabled, return original content without processing
    if not use_summarizations:
        for url, result in unique_results.items():
            processed_results[url] = {
                "title": result["title"],
                "content": result["content"],
            }
        return processed_results

    # Build a list of coroutines for summarizing each webpage content concurrently
    tasks = [
        asyncio.to_thread(summarize_webpage_content, result["raw_content"])
        for result in unique_results.values()
    ]

    summarized_contents = await asyncio.gather(*tasks, return_exceptions=True)

    for (url, result), summarized_content in zip(
        unique_results.items(), summarized_contents
    ):
        if isinstance(summarized_content, Exception):
            print(f"Summarization failed for '{url}': {summarized_content}")
            content = result["content"]  # Fallback to original content on failure
        else:
            content = summarized_content

        processed_results[url] = {"title": result["title"], "content": content}

    return processed_results


def format_search_output(processed_results: dict) -> str:
    if not processed_results:
        return "No search results found."

    results = []
    for url, result in processed_results.items():
        results.append(
            f"<source>\n"
            f"<title>{result['title']}</title>\n"
            f"<url>{url}</url>\n"
            f"<content>{result['content']}</content>\n"
            f"</source>"
        )

    return "\n\n".join(results)


def build_domains(denomination: str, mode: str) -> List[str]:
    """Build a list of domains to filter search results by based on the active denomination."""
    
    # Construct the include_domains list
    include_domains = REPOSITORIES["general"].copy()
    
    if denomination in REPOSITORIES["denominations"]:
        include_domains.extend(REPOSITORIES["denominations"][denomination])
    
    if mode in REPOSITORIES["modes"]:
        include_domains.extend(REPOSITORIES["modes"][mode])
    
    return include_domains

def _build_filter(
    translation: str | None,
    testament: str | None,
    genre: str | None,
) -> dict:
    """
    Construct a Pinecone metadata filter dict.
    Only adds clauses for values that are actually present in the index.
    """
    conditions = []

    # Translation — default to all available if none specified
    if translation and translation in AVAILABLE_TRANSLATIONS:
        conditions.append({"translation": {"$eq": translation}})
    elif AVAILABLE_TRANSLATIONS:
        # Constrain to what's actually ingested (avoids empty results)
        conditions.append({"translation": {"$in": AVAILABLE_TRANSLATIONS}})

    if testament in ("Old", "New"):
        conditions.append({"testament": {"$eq": testament}})

    if genre and genre in VALID_GENRES:
        conditions.append({"genre": {"$eq": genre}})

    if not conditions:
        return {}
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}

def _format_bible_output(results: list[dict]) -> str:
    """Serialize results into XML-like source blocks matching web_search output format."""
    if not results:
        return "<bible_results>\n<message>No relevant passages found.</message>\n</bible_results>"

    blocks = []
    for i, r in enumerate(results):
        block = (
            f'<source index="{i + 1}">\n'
            f'  <reference>{r["reference"]}</reference>\n'  # "John 3:16-18"
            f'  <book>{r["book"]}</book>\n'
            f'  <chapter>{r["chapter"]}</chapter>\n'
            f'  <verses>{r["start_verse"]}-{r["end_verse"]}</verses>\n'
            f'  <testament>{r["testament"]}</testament>\n'
            f'  <translation>{r["translation"]}</translation>\n'
            f'  <genre>{r["genre"]}</genre>\n'
            f'  <text>{r["text"]}</text>\n'
            f'  <score>{r["score"]:.3f}</score>\n'
            f"</source>"
        )
        blocks.append(block)

    return "<bible_results>\n" + "\n".join(blocks) + "\n</bible_results>"
