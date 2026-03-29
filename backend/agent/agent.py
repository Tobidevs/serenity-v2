from langgraph.graph import END, START, StateGraph
from langchain_core.messages import HumanMessage
from .nodes import input_call, tool_node, output_call
from .state import AgentState


serenity_agent_builder = StateGraph(AgentState)

serenity_agent_builder.add_node("input_call", input_call)
serenity_agent_builder.add_node("tool_node", tool_node)
serenity_agent_builder.add_node("output_call", output_call)

serenity_agent_builder.add_edge(START, "input_call")
serenity_agent_builder.add_edge("input_call", "tool_node")
serenity_agent_builder.add_edge("tool_node", "output_call")
serenity_agent_builder.add_edge("output_call", END)

serenity_agent = serenity_agent_builder.compile()


async def run_agent():
    denomination = "Catholic"
    mode = "academic"
    result = await serenity_agent.ainvoke(
        {
            "messages": [HumanMessage(content="explain god")],
            "denomination": denomination,
            "mode": mode,
            "sources": [],
        }
    )
    print(f"AI Output: {result['messages'][-1].content}")
    print(f"Sources: {result['sources']}")
