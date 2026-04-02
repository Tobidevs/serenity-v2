from typing import Annotated, Literal, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages, MessageState
from pydantic import BaseModel, Field

class AgentState(MessageState):
    """State schema for the research agent.
    
    Args:
        denomination: Specification of the religious denomination for research context
        mode: Research mode, either "academic" for scholarly analysis or "devotional"
        sources: List of sources used in the research process
    """
    
    denomination: Annotated[str, Field(description="Denomination Specification for Research")]
    mode: Annotated[str, Literal["academic", "devotional"]]
    sources: Annotated[Sequence[str], Field(description="List of sources used in research")]
    

class Summary(BaseModel):
    """Schema for webpage content summarization.
    
    """
    summary: str = Field(description="Concise summary of the webpage content")
    key_excerpts: str = Field(description="Important quotes and excerpts from the content")
    
class StrategistOutput(BaseModel):
    
    action: Annotated[str, Literal["tool_call", "clarify"], Field(description="Action to take: 'tool_call' to execute a tool, 'clarify' to ask user for more information")]
    question = Annotated[str, Field(description="Clarifying question for the user if action is 'clarify'")]
    search_query = Annotated[Sequence[str], Field(description="List of search queries for the tool if action is 'search'")]
    
    

class WebSearchInput(BaseModel):
    queries: list[str] = Field(
        description="1-2 standalone, fully self-contained search queries with "
        "denominational anchoring and mode framing applied."
    )
    resolved_query: str = Field(
        description="The user's original query with all pronouns and references "
        "fully resolved. Passed to the Scholar for response framing."
    )
    denomination: Annotated[str, Literal["catholic", "orthodox", "reformed", "anglican", "lutheran"]] = Field(
        description="The active denomination for this session, derived from the latest user message."
    )
    mode: Annotated[str, Literal["academic", "devotional"]] = Field(
        description="The research mode for this session, derived from the latest user message."
    )


class BibleRAGInput(BaseModel):
    topic: str = Field(
        description="A concise description of the theological topic or question "
        "to guide verse retrieval. Derived from the resolved query."
    )


class ClarifyInput(BaseModel):
    question: str = Field(
        description="A single, specific question that resolves the ambiguity "
        "blocking search. Must be one question only — not a list."
    )