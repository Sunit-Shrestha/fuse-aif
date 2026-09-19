import os
from pathlib import Path

from dotenv import load_dotenv

from .net import force_ipv4_dns

load_dotenv()
force_ipv4_dns()

BASE_DIR = Path(__file__).resolve().parent.parent
CORPUS_DIR = BASE_DIR / "data" / "corpus"
INDEX_DIR = BASE_DIR / "data" / "index"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "120"))
TOP_K = int(os.environ.get("TOP_K", "4"))

DEFAULT_TEMPERATURE = float(os.environ.get("GEMINI_TEMPERATURE", "0.4"))
DEFAULT_TOP_P = float(os.environ.get("GEMINI_TOP_P", "0.9"))
