from langchain.chat_models import init_chat_model
import asyncio

from .prompts import SYSTEM_PROMPT
from .tools import web_search, bible_rag, request_clarification
from .state import AgentState
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, trim_messages
from langgraph.types import interrupt

tools = [web_search, bible_rag, request_clarification]
tools_dict = {tool.name: tool for tool in tools}
model = init_chat_model(model="openai:gpt-5.1")
strategist_model = model.bind_tools(tools)


def strategist_node(state: AgentState) -> AgentState:
    """Analyze current state and decide on next action."""
    try:

        # Optionally trim history to last N tokens before injecting
        # trimmed_history = trim_messages(
        #     state["messages"], max_tokens=4000, token_counter=strategist_model
        # )

        response = strategist_model.invoke(state["messages"])

    except Exception as exc:
        response = f"Error during LLM call: {exc}"

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


def clarify_node(state: AgentState) -> None:
    last_message = state["messages"][-1]
    clarification_call = next(
        tc for tc in last_message.tool_calls 
        if tc["name"] == "request_clarification"
    )
    question = clarification_call["args"]["question"]
    
    user_clarification = interrupt(question)
    return {"messages": [HumanMessage(content=user_clarification)]}
    

async def tool_node(state: AgentState) -> AgentState:
    """Execute all tool calls from previous LLM response.
    Returns updated state with tool execution results.
    """
    try:
        messages = state.get("messages", [])
        if not messages:
            return {"messages": ["No messages from researcher to process."]}

        last_message = messages[-1]
        tool_calls = getattr(last_message, "tool_calls", None) or []
        if not tool_calls:
            return {"messages": []}

        tasks = []
        valid_tool_calls = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            if not tool_name or tool_name not in tools_dict:
                raise ValueError(f"Invalid tool call: {tool_call}")
            valid_tool_calls.append(tool_call)
            tasks.append(tools_dict[tool_name].ainvoke(tool_args))

        results = await asyncio.gather(*tasks)

        tool_outputs = []
        for tool_call, result in zip(valid_tool_calls, results):
            if isinstance(result, Exception):
                raise ValueError(
                    f"Tool call failed: {tool_call['name']} with error {result}"
                )
            tool_outputs.append(
                ToolMessage(
                    content=result,
                    tool_name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )

        if not tool_outputs:
            raise ValueError("No valid tool outputs were generated.")

        return {"messages": tool_outputs}
    except Exception as exc:
        raise ValueError(f"Error during tool execution: {exc}") from exc


def scholar_node(state: AgentState) -> AgentState:
    """Generate final output based on current state."""
    # Placeholder for output generation logic
    return state
