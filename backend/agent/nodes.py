from langchain.chat_models import init_chat_model
from langgraph.prebuilt import ToolNode

from .prompts import (
    SCHOLAR_SYSTEM_PROMPT,
    STRATEGIST_SYSTEM_PROMPT,
    get_source_hierarchy,
)
from .tools import web_search, bible_rag, request_clarification
from .state import AgentState, ScholarOutput
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, trim_messages
from langgraph.types import interrupt

tools = [web_search, bible_rag, request_clarification]
model = init_chat_model(model="openai:gpt-4.1")
strategist_model = model.bind_tools(tools)
scholar_model = model.with_structured_output(ScholarOutput)


def strategist_node(state: AgentState) -> AgentState:
    """Analyze current state and decide on next action."""
    try:

        # Optionally trim history to last N tokens before injecting
        # trimmed_history = trim_messages(
        #     state["messages"], max_tokens=4000, token_counter=strategist_model
        # )

        response = strategist_model.invoke(state["messages"])

    except Exception as exc:
        error_response = f"Error during Strategist LLM call: {exc}"
        return {"messages": [HumanMessage(content=error_response)]}

    return {"messages": [response]}


def route_strategist(state: AgentState) -> str:
    last_message = state["messages"][-1]

    if not last_message.tool_calls:
        return "end"

    tool_names = {tc["name"] for tc in last_message.tool_calls}

    if "request_clarification" in tool_names:
        return "clarify"
    else:
        return "tools"


def clarify_node(state: AgentState) -> AgentState:
    last_message = state["messages"][-1]
    clarification_call = next(
        tc for tc in last_message.tool_calls if tc["name"] == "request_clarification"
    )
    question = clarification_call["args"]["question"]

    user_clarification = interrupt(question)
    return {"messages": [HumanMessage(content=user_clarification)]}


tool_node = ToolNode(tools)


def scholar_node(state: AgentState) -> AgentState:
    try:
        denomination = state.get("denomination", "Christian")
        mode = (state.get("mode") or "devotional").lower()

        system_prompt = SCHOLAR_SYSTEM_PROMPT.format(
            denomination=denomination,
            mode=mode.upper(),
            source_hierarchy=get_source_hierarchy(denomination),
        )

        response = scholar_model.invoke(
            [SystemMessage(content=system_prompt)] + state["messages"]
        )

        return {
            "answer": response.answer,
            "scripture_references": response.scripture_references,
            "sources": response.sources,
            "denomination_notes": response.denomination_notes,
            "mode": response.mode,
        }
    except Exception as exc:
        error_response = f"Error during Scholar LLM call: {exc}"
        return {"messages": [HumanMessage(content=error_response)]}
