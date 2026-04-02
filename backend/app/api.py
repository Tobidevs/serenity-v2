import uuid
from fastapi import APIRouter
from langchain_core.messages import HumanMessage, SystemMessage

from ..agent.agent import serenity_agent
from ..agent.prompts import SYSTEM_PROMPT

router = APIRouter()


class ChatRequest:
    message: str
    denomination: str
    mode: str
    thread_id: str = None


class ChatResponse:
    thread_id: str
    response: str
    sources: list[str]


def build_human_message(user_input: str, denomination: str, mode: str) -> HumanMessage:
    return HumanMessage(
        content=f"""[Session: Denomination={denomination} | Mode={mode}]
        {user_input}"""
    )


@router.get("chat")
async def chat(request: ChatRequest):
    try:
        if not request.thread_id:  # New conversation
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}

            serenity_agent_result = await serenity_agent.ainvoke(
                {
                    "messages": [
                        SystemMessage(content=SYSTEM_PROMPT),
                        build_human_message(request.message, request.denomination, request.mode),
                    ],
                    "denomination": request.denomination,
                    "mode": request.mode,
                },
                config=config,
            )
            # todo refactor for interrupt handiing

            return ChatResponse(
                thread_id=thread_id,
                response=serenity_agent_result["messages"][-1].content,
                sources=serenity_agent_result.get("sources", []),
            )
        else:  # Existing conversation
            config = {"configurable": {"thread_id": request.thread_id}}
            current_state = await serenity_agent.aget_state(config)

            serenity_agent_result = await serenity_agent.ainvoke({
                "messages": build_human_message(request.message, request.denomination, request.mode),
                "denomination": request.denomination,
                "mode": request.mode,
            })

            return ChatResponse(
                thread_id=request.thread_id,
                response=serenity_agent_result["messages"][-1].content,
                sources=serenity_agent_result.get("sources", []),
            )
    except Exception as exc:
        return ChatResponse(
            thread_id=request.thread_id, response=f"Error: {exc}", sources=[]
        )
