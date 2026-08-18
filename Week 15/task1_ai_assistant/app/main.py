"""
FastAPI app for the Fusemachines Course Assistant.

POST /chat            -- ask a question; RAG + tool calling + structured JSON output.
GET  /health          -- basic health check.

Run: uvicorn app.main:app --reload --port 8000
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from . import config
from .llm_client import GeminiClient, OllamaClient
from .rag import RagIndex
from .schemas import ChatRequest, ChatResponse
from .tools import make_tools

_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    rag_index = RagIndex()
    if (config.INDEX_DIR / "index.faiss").exists():
        rag_index.load(config.INDEX_DIR)
    else:
        rag_index.build(config.CORPUS_DIR, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        rag_index.save(config.INDEX_DIR)
    _state["rag_index"] = rag_index
    _state["gemini"] = GeminiClient()
    _state["ollama"] = OllamaClient()
    yield
    _state.clear()


app = FastAPI(title="Fusemachines Course Assistant", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "chunks_indexed": len(_state["rag_index"].chunks)}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    temperature = req.temperature if req.temperature is not None else config.DEFAULT_TEMPERATURE
    top_p = req.top_p if req.top_p is not None else config.DEFAULT_TOP_P

    if req.provider == "ollama":
        try:
            text = _state["ollama"].chat(req.message, temperature)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Local model unavailable: {exc}")
        return ChatResponse(answer=text, sources=[], escalate_to_human=False, provider_used="ollama")

    sources_used: list[str] = []
    tools = make_tools(_state["rag_index"], sources_used)
    try:
        result = _state["gemini"].chat(req.message, tools, temperature, top_p)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini request failed: {exc}")

    return ChatResponse(
        answer=result.answer,
        sources=sources_used or result.sources,
        escalate_to_human=result.escalate_to_human,
        provider_used="gemini",
    )
