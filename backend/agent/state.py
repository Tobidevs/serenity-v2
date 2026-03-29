from typing import Annotated, Literal, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field

class AgentState(TypedDict):
    """State schema for the research agent.
    
    Args:
        researcher_messages: Sequence of messages from the researcher, including LLM responses and tool outputs
        denomination: Specification of the religious denomination for research context
        mode: Research mode, either "academic" for scholarly analysis or "devotional"
        sources: List of sources used in the research process
    """
    
    researcher_messages: Annotated[Sequence[BaseMessage], add_messages]
    denomination: Annotated[str, Field(description="Denomination Specification for Research")]
    mode: Annotated[str, Literal["academic", "devotional"]]
    sources: Annotated[Sequence[str], Field(description="List of sources used in research")]
    

class Summary(BaseModel):
    """Schema for webpage content summarization.
    
    """
    summary: str = Field(description="Concise summary of the webpage content")
    key_excerpts: str = Field(description="Important quotes and excerpts from the content")
    