import logging
import os
from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from groq import APIError, APIStatusError, Groq
from pydantic import BaseModel, Field

from backend.app.models.models import User
from backend.app.utils.auth_helper import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["AI Assistant"])

SYSTEM_PROMPT = (
    "You are EVolt's EV charging and battery assistant. Give concise, helpful "
    "information about electric vehicles, charging, battery health, and this "
    "application. You cannot access the user's account, vehicle, live stations, "
    "or charging data unless they provide it in the conversation. Do not claim "
    "to perform actions or access live data."
)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(min_length=1, max_length=12)


class ChatResponse(BaseModel):
    reply: str


@router.post("/message", response_model=ChatResponse)
def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI chat is not configured. Set GROQ_API_KEY in the project .env file and restart Docker.",
        )

    client = Groq(api_key=api_key)
    try:
        completion = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *[message.model_dump() for message in request.messages],
            ],
            max_tokens=700,
            temperature=0.7,
        )
    except APIError as exc:
        logger.exception("Groq chat request failed for user %s", current_user.id)
        if isinstance(exc, APIStatusError) and exc.status_code == 404:
            detail = "The configured Groq model is unavailable. Set GROQ_MODEL to a model available to your Groq account."
        elif isinstance(exc, APIStatusError) and exc.status_code in (401, 403):
            detail = "Groq rejected the API key. Check GROQ_API_KEY in C:\\EVolt AI\\.env."
        elif isinstance(exc, APIStatusError) and exc.status_code == 429:
            detail = "Groq rate limit or usage limit reached. Please wait and try again."
        else:
            detail = "The AI assistant could not respond. Please try again later."
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        ) from exc

    if not completion.choices or not completion.choices[0].message.content:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI assistant returned an empty response. Please try again.",
        )

    return ChatResponse(reply=completion.choices[0].message.content)
