"""
FastAPI backend for the productionized AG_NEWS topic router.

POST /predict        -- single headline, sync-wrapped-async + cached.
POST /predict_batch   -- list of headlines, one batched ONNX forward pass.
GET  /health

Reliability: response caching, rate limiting (slowapi), retrying + a Gemini
fallback classifier if the local ONNX model errors, and graceful degradation
(a clear UNKNOWN response instead of a 500) if both paths fail.

Run: uvicorn backend.main:app --port 8000
"""
import asyncio
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from . import config
from .cache import TTLCache
from .fallback import GeminiFallbackClassifier
from .model import RouterModel
from .schemas import PredictBatchRequest, PredictRequest, PredictResponse

_state: dict = {}
_executor = ThreadPoolExecutor(max_workers=4)
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _state["model"] = RouterModel()
    _state["fallback"] = GeminiFallbackClassifier()
    _state["cache"] = TTLCache(config.CACHE_MAX_SIZE, config.CACHE_TTL_SECONDS)
    yield
    _state.clear()


app = FastAPI(title="AG_NEWS Topic Router", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def _cache_key(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()


def _classify_with_fallback(text: str) -> tuple[dict, str]:
    """Runs on the thread pool. Tries the local ONNX model first; on any
    exception, falls back to Gemini; if that also fails, degrades gracefully
    instead of raising."""
    try:
        return _state["model"].predict_one(text), "onnx_local"
    except Exception:
        pass
    try:
        return _state["fallback"].predict_one(text), "gemini_fallback"
    except Exception:
        return {"category": "UNKNOWN", "confidence": 0.0, "probabilities": None}, "degraded"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
@limiter.limit(config.RATE_LIMIT)
async def predict(request: Request, body: PredictRequest):
    start = time.time()
    key = _cache_key(body.text)
    cached = _state["cache"].get(key)
    if cached is not None:
        return PredictResponse(**cached, cached=True, latency_ms=(time.time() - start) * 1000)

    loop = asyncio.get_running_loop()
    result, provider = await loop.run_in_executor(_executor, _classify_with_fallback, body.text)

    response_data = {**result, "provider_used": provider}
    _state["cache"].set(key, response_data)
    return PredictResponse(**response_data, cached=False, latency_ms=(time.time() - start) * 1000)


@app.post("/predict_batch", response_model=list[PredictResponse])
@limiter.limit(config.RATE_LIMIT)
async def predict_batch(request: Request, body: PredictBatchRequest):
    start = time.time()
    loop = asyncio.get_running_loop()
    try:
        results = await loop.run_in_executor(_executor, _state["model"].predict_batch, body.texts)
        provider = "onnx_local"
    except Exception:
        # Batch fallback: classify each item individually through the same
        # single-item fallback path (Gemini has no batch API here).
        results, providers = [], []
        for text in body.texts:
            r, p = _classify_with_fallback(text)
            results.append(r)
            providers.append(p)
        latency = (time.time() - start) * 1000
        return [
            PredictResponse(**r, provider_used=p, cached=False, latency_ms=latency)
            for r, p in zip(results, providers)
        ]

    latency = (time.time() - start) * 1000
    return [PredictResponse(**r, provider_used=provider, cached=False, latency_ms=latency) for r in results]
