from langchain.chat_models import init_chat_model
import asyncio
from .tools import think_tool, tavily_search
from .state import AgentState
from langchain_core.messages import SystemMessage, ToolMessage

tools = [tavily_search, think_tool]
tools_dict = {tool.name: tool for tool in tools}
model = init_chat_model(model="openai:gpt-5.1")
researcher_model = model.bind_tools(tools)


def input_call(state: AgentState) -> AgentState:
    """Analyze current state and decide on next action."""
    try:
        response = researcher_model.invoke(
            [
                SystemMessage(content=RESEARCH_AGENT_SYSTEM_PROMPT),
            ]
            + state["messages"],
        )
    except Exception as exc:
        response = f"Error during LLM call: {exc}"

    return {"messages": [response]}


async def tool_node(state: AgentState) -> AgentState:
    """Execute all tool calls from previous LLM response.
    Returns updated state with tool execution results.
    """
    try:
        researcher_messages = state.get("researcher_messages", [])
        if not researcher_messages:
            return {"researcher_messages": ["No messages from researcher to process."]}

        last_message = researcher_messages[-1]
        tool_calls = getattr(last_message, "tool_calls", None) or []
        if not tool_calls:
            return {"researcher_messages": []}

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

        return {"researcher_messages": tool_outputs}
    except Exception as exc:
        raise ValueError(f"Error during tool execution: {exc}") from exc


def output_call(state: AgentState) -> AgentState:
    """Generate final output based on current state."""
    # Placeholder for output generation logic
    return state
