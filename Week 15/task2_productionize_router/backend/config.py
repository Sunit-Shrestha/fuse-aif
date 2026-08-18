import os
from pathlib import Path

from dotenv import load_dotenv

from .net import force_ipv4_dns

load_dotenv()
force_ipv4_dns()

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"

ONNX_MODEL_PATH = ARTIFACTS_DIR / "model.quant.onnx"
VOCAB_PATH = ARTIFACTS_DIR / "vocab.json"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "300"))
CACHE_MAX_SIZE = int(os.environ.get("CACHE_MAX_SIZE", "1000"))

RATE_LIMIT = os.environ.get("RATE_LIMIT", "30/minute")
