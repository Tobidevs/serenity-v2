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
    