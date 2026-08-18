"""
Two LLM providers:

- GeminiClient: cloud provider (Google AI Studio). Runs a two-phase flow so
  tool calling and forced-JSON structured output can both be satisfied:
    Phase 1 -- tools enabled, free-text answer (automatic function calling
               lets the SDK run the tool-call loop for us).
    Phase 2 -- tools disabled, response_schema enabled, asks the model to
               package the phase-1 answer into valid AssistantAnswer JSON.

- OllamaClient: local, open-source model served by Ollama (this project's
  stand-in for vLLM -- see README for why). No tool calling / structured
  output support is assumed here; it's a plain chat completion used as an
  offline/local provider option.
"""
import httpx
from google import genai
from google.genai import types

from . import config
from .net import ipv4_httpx_client
from .schemas import AssistantAnswer

SYSTEM_INSTRUCTION = (
    "You are the Fusemachines AI Fellowship Course Assistant. You help students "
    "find information in their own course materials (weekly guides and assignments). "
    "Always use the search_course_materials tool before answering questions about "
    "course content -- never rely on memory alone. If the answer isn't in the course "
    "materials, say so honestly and set escalate_to_human."
)


class GeminiClient:
    def __init__(self):
        self._client = genai.Client(
            api_key=config.GEMINI_API_KEY,
            http_options=types.HttpOptions(httpx_client=ipv4_httpx_client()),
        )

    def chat(self, message: str, tools: list, temperature: float, top_p: float) -> AssistantAnswer:
        phase1 = self._client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=temperature,
                top_p=top_p,
                tools=tools,
            ),
        )
        draft_answer = phase1.text or ""

        phase2 = self._client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=(
                f"User question: {message}\n\nDraft answer: {draft_answer}\n\n"
                "Package this into the required JSON schema."
            ),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=AssistantAnswer,
            ),
        )
        return phase2.parsed


class OllamaClient:
    def __init__(self, host: str = config.OLLAMA_HOST, model: str = config.OLLAMA_MODEL):
        self.host = host
        self.model = model

    def chat(self, message: str, temperature: float) -> str:
        resp = httpx.post(
            f"{self.host}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": message},
                ],
                "stream": False,
                "options": {"temperature": temperature},
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]
