# Week 15 — Applied AI & Engineering AI Systems

Two independent deliverables, per `W15_Assignment.pdf`:

- **[`task1_ai_assistant/`](task1_ai_assistant/README.md)** — Task 1: an AI assistant with
  Gemini (LLM integration, prompt engineering, structured JSON output, tool calling), a
  RAG pipeline (chunking + sentence-transformers embeddings + FAISS), and a locally
  served open-source LLM (Ollama's `llama3.2:1b`, standing in for vLLM — see that
  README for why). Dockerized.

- **[`task2_productionize_router/`](task2_productionize_router/README.md)** — Task 2:
  productionizes the Week 13 LSTM AG_NEWS classifier — retrained on the full dataset
  (90.5% test accuracy), ONNX-optimized (52x latency reduction after quantization), and
  served behind a FastAPI backend + Streamlit UI with caching, rate limiting, retries,
  and a Gemini fallback. Docker Compose.

Both share one `.env` (Gemini API key) at this level.

## Prerequisites to run either app

```bash
# .env in this directory:
GEMINI_API_KEY=your_key_here

# Ollama (Task 1's local model), already installed on this machine:
ollama pull llama3.2:1b
```

See each task's own README for setup, architecture diagrams, and design-decision
rationale (including a networking workaround needed on this specific machine — see
`task1_ai_assistant/README.md`'s "A networking note" section, which applies to both
tasks' Gemini integration).
