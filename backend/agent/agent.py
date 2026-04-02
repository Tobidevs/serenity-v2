from langgraph.graph import END, START, StateGraph
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from .nodes import clarify_node, route_strategist, strategist_node, tool_node, scholar_node
from .state import AgentState


serenity_agent_builder = StateGraph(AgentState)

serenity_agent_builder.add_node("strategist_node", strategist_node)
serenity_agent_builder.add_node("tool_node", tool_node)
serenity_agent_builder.add_node("clarify_node", clarify_node)
serenity_agent_builder.add_node("scholar_node", scholar_node)

serenity_agent_builder.add_edge(START, "strategist_node")
serenity_agent_builder.add_conditional_edges(
    "strategist_node",
    route_strategist,
    {
        "clarify": "clarify_node",
        "tools": "tool_node",
        "end": END
    }
)
serenity_agent_builder.add_edge("tool_node", "scholar_node")
serenity_agent_builder.add_edge("clarify_node", "strategist_node")
serenity_agent_builder.add_edge("scholar_node", END)

serenity_agent = serenity_agent_builder.compile(checkpointer=InMemorySaver())


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
