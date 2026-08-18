from typing import List, Optional

from pydantic import BaseModel


class PredictRequest(BaseModel):
    text: str


class PredictBatchRequest(BaseModel):
    texts: List[str]


class PredictResponse(BaseModel):
    category: str
    confidence: Optional[float] = None
    probabilities: Optional[dict] = None
    provider_used: str
    cached: bool = False
    latency_ms: float
