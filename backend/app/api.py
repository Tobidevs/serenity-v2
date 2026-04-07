import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage

from agent.agent import serenity_agent
from agent.prompts import STRATEGIST_SYSTEM_PROMPT

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    denomination: str
    mode: str
    thread_id: str = None


class ChatResponse(BaseModel):
    thread_id: str
    answer: str
    sources: list[str]
    scripture_references: list[str]
    mode: str
    denomination_notes: str


def normalize_markdown_answer(answer: str) -> str:
    """Normalize common escaped sequences so frontend markdown renders as intended."""
    if not answer:
        return ""

    normalized = answer.strip()

    # If model emitted literal escape sequences, convert them to actual characters.
    if "\\n" in normalized:
        normalized = normalized.replace("\\r\\n", "\n").replace("\\n", "\n")
    if "\\t" in normalized:
        normalized = normalized.replace("\\t", "\t")

    return normalized


def build_human_message(user_input: str, denomination: str, mode: str) -> HumanMessage:
    return HumanMessage(
        content=f"""[Session: Denomination={denomination} | Mode={mode}]
        {user_input}"""
    )


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        if not request.thread_id:  # New conversation
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}

            serenity_agent_result = await serenity_agent.ainvoke(
                {
                    "messages": [
                        SystemMessage(content=STRATEGIST_SYSTEM_PROMPT),
                        build_human_message(
                            request.message, request.denomination, request.mode
                        ),
                    ],
                    "denomination": request.denomination,
                    "mode": request.mode,
                },
                config=config,
            )
            # todo refactor for interrupt handling

            return ChatResponse(
                thread_id=thread_id,
                answer=normalize_markdown_answer(
                    serenity_agent_result.get("answer", "")
                ),
                scripture_references=serenity_agent_result.get(
                    "scripture_references", []
                ),
                sources=serenity_agent_result.get("sources", []),
                mode=serenity_agent_result.get("mode", ""),
                denomination_notes=serenity_agent_result.get("denomination_notes", ""),
            )
        else:  # Existing conversation
            config = {"configurable": {"thread_id": request.thread_id}}
            current_state = await serenity_agent.aget_state(config)

            serenity_agent_result = await serenity_agent.ainvoke(
                {
                    "messages": build_human_message(
                        request.message, request.denomination, request.mode
                    ),
                    "denomination": request.denomination,
                    "mode": request.mode,
                },
                config=config,
            )

            return ChatResponse(
                thread_id=request.thread_id,
                answer=normalize_markdown_answer(
                    serenity_agent_result.get("answer", "")
                ),
                scripture_references=serenity_agent_result.get(
                    "scripture_references", []
                ),
                sources=serenity_agent_result.get("sources", []),
                mode=serenity_agent_result.get("mode", ""),
                denomination_notes=serenity_agent_result.get("denomination_notes", ""),
            )
    except Exception as exc:
        return ChatResponse(
            thread_id=request.thread_id,
            answer=f"Error: {exc}",
            scripture_references=[],
            sources=[],
            mode="",
            denomination_notes="",
        )
