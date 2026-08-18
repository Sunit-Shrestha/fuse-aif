from typing import List

from pydantic import BaseModel, Field


class AssistantAnswer(BaseModel):
    """Structured final response the assistant must return as valid JSON."""

    answer: str = Field(description="The final answer to the user's question, in plain language.")
    sources: List[str] = Field(default_factory=list, description="Filenames of course materials used, if any.")
    escalate_to_human: bool = Field(
        default=False, description="True if the question can't be answered from course materials."
    )


class ChatRequest(BaseModel):
    message: str
    temperature: float | None = None
    top_p: float | None = None
    provider: str = "gemini"  # "gemini" or "ollama"


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    escalate_to_human: bool = False
    provider_used: str
