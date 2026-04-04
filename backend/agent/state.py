from typing import Annotated, Literal, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field


class AgentState(MessagesState):
    """State schema for the research agent.

    Args:
        denomination: Specification of the religious denomination for research context
        mode: Research mode, either "academic" for scholarly analysis or "devotional"
        sources: List of sources used in the research process
    """

    denomination: str
    answer: str
    scripture_references: list[str]
    sources: list[str]
    denomination_notes: str
    mode: str


class Summary(BaseModel):
    """Schema for webpage content summarization."""

    summary: str = Field(description="Concise summary of the webpage content")
    key_excerpts: str = Field(
        description="Important quotes and excerpts from the content"
    )


class StrategistOutput(BaseModel):

    action: Annotated[
        str,
        Literal["tool_call", "clarify"],
        Field(
            description="Action to take: 'tool_call' to execute a tool, 'clarify' to ask user for more information"
        ),
    ]
    question: Annotated[
        str,
        Field(description="Clarifying question for the user if action is 'clarify'"),
    ]
    search_query: Annotated[
        Sequence[str],
        Field(description="List of search queries for the tool if action is 'search'"),
    ]


class ScholarOutput(BaseModel):
    answer: Annotated[
        str,
        Field(
            description="Final answer to the user's query, framed according to the specified denomination and mode"
        ),
    ]
    scripture_references: Annotated[
        Sequence[str],
        Field(description="List of scripture references cited in the answer"),
    ]
    sources: Annotated[
        Sequence[str], Field(description="List of sources cited in the answer")
    ]
    denomination_notes: Annotated[
        str,
        Field(
            description="Any specific notes on how the answer is framed according to the denomination's perspective"
        ),
    ]
    mode: Annotated[str, Literal["academic", "devotional"]] = Field(
        description="The research mode, either 'academic' for scholarly analysis or 'devotional' for faith-building content"
    )


class WebSearchInput(BaseModel):
    queries: list[str] = Field(
        description="1-2 standalone, fully self-contained search queries with "
        "denominational anchoring and mode framing applied."
    )
    resolved_query: str = Field(
        description="The user's original query with all pronouns and references "
        "fully resolved. Passed to the Scholar for response framing."
    )
    denomination: Annotated[
        str, Literal["catholic", "orthodox", "reformed", "anglican", "lutheran"]
    ] = Field(
        description="The active denomination for this session, derived from the latest user message."
    )
    mode: Annotated[str, Literal["academic", "devotional"]] = Field(
        description="The research mode for this session, derived from the latest user message."
    )


class BibleRAGInput(BaseModel):
    queries: list[str] = Field(
        description="Search queries to find relevant Bible passages. Use theological "
        "terms, paraphrased concepts, or direct scripture references."
    )
    translation: str | None = Field(
        default=None,
        description="Bible translation to filter by (e.g. 'KJV'). Only KJV is currently "
        "available. Leave None to include all available translations.",
    )
    testament: str | None = Field(
        default=None,
        description="Scope results to 'Old' or 'New' testament. Leave None to search both.",
    )
    genre: str | None = Field(
        default=None,
        description="Filter by genre: 'Gospel', 'Epistle', 'Torah', 'Prophecy', or "
        "'History/Wisdom/Other'. Leave None to search all genres.",
    )
    top_k: int = Field(
        default=3, description="Number of passages to retrieve per query. Default is 3."
    )


class ClarifyInput(BaseModel):
    question: str = Field(
        description="A single, specific question that resolves the ambiguity "
        "blocking search. Must be one question only — not a list."
    )
