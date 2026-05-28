import logging
import os
import time
from pathlib import Path

from google import genai

from executor import run_query
from prompts import (
    DECOMPOSITION_PROMPT,
    FIX_PROMPT,
    GENERATE_PROMPT,
    SCHEMA,
    SUMMARIZE_PROMPT,
)
from validator import clean_sql, validate_sql


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(LOG_DIR / "project.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

_client = None


def _load_environment():
    try:
        from dotenv import load_dotenv as _load_dotenv
    except ImportError:  # pragma: no cover - optional runtime dependency
        return

    for candidate in (BASE_DIR / ".env", BASE_DIR.parent / ".env", Path.cwd() / ".env"):
        if candidate.exists():
            _load_dotenv(candidate)
            break


_load_environment()

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = (
    os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
    or os.getenv("GEMINI_API")
)


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else genai.Client()
    return _client


def _strip_markdown_fences(text: str) -> str:
    return clean_sql(text)


def query_gemini(prompt: str) -> str:
    response = _get_client().models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    return _strip_markdown_fences(response.text or "")


def create_gemini_chat():
    return _get_client().chats.create(model=MODEL_NAME)


def query_gemini_chat(chat, prompt: str) -> str:
    response = chat.send_message(prompt)
    return _strip_markdown_fences(response.text or "")


def _build_decomposition(question: str) -> str:
    prompt = DECOMPOSITION_PROMPT.format(schema=SCHEMA, question=question)
    logging.info("Asking Gemini for decomposition: %s", question)
    decomposition = query_gemini(prompt).strip()
    logging.info("Decomposition: %s", decomposition)
    return decomposition


def _build_sql(question: str, decomposition: str) -> str:
    prompt = GENERATE_PROMPT.format(
        schema=SCHEMA,
        decomposition=decomposition,
        question=question,
    )
    sql = query_gemini(prompt)
    logging.info("Generated SQL: %s", sql)
    return sql


def _summarize(question: str, sql: str, result):
    prompt = SUMMARIZE_PROMPT.format(question=question, sql=sql, result=result)
    return query_gemini(prompt).replace("***", "*").strip()


def run_text_to_sql(question: str, retry_limit: int = 3):
    start_time = time.time()
    logging.info("Received question: %s", question)

    try:
        decomposition = _build_decomposition(question)
        sql = _build_sql(question, decomposition)
        retries = 0
        result_data = None
        retry_chat = None

        while True:
            try:
                validated_sql = validate_sql(sql)
                result_data = run_query(validated_sql)
                status = "success"
                break
            except ValueError as exc:
                logging.warning("Unsafe query blocked: %s", exc)
                return {
                    "question": question,
                    "decomposition": decomposition,
                    "sql": clean_sql(sql),
                    "result": None,
                    "summary": "Unsafe query detected. Only SELECT is allowed.",
                    "status": "error",
                    "retries": retries,
                    "execution_time": round(time.time() - start_time, 2),
                }
            except Exception as exc:
                error_message = str(exc)
                logging.warning("Execution failed on attempt %s: %s", retries + 1, error_message)
                if retries >= retry_limit:
                    status = "failed"
                    break

                retries += 1
                if retry_chat is None:
                    retry_chat = create_gemini_chat()

                fix_prompt = FIX_PROMPT.format(
                    schema=SCHEMA,
                    question=question,
                    sql=sql,
                    error=error_message,
                )
                sql = query_gemini_chat(retry_chat, fix_prompt)
                logging.info("Retry SQL: %s", sql)

        if status == "success":
            summary = _summarize(question, sql, result_data)
        else:
            summary = "I encountered an unrecoverable error while fetching the data."

        execution_time = round(time.time() - start_time, 2)
        logging.info("Pipeline finished in %.2fs", execution_time)
        return {
            "question": question,
            "decomposition": decomposition,
            "sql": clean_sql(sql),
            "result": result_data,
            "summary": summary,
            "status": status,
            "retries": retries,
            "execution_time": execution_time,
        }
    except Exception as exc:
        execution_time = round(time.time() - start_time, 2)
        logging.exception("Pipeline failed unexpectedly")
        return {
            "question": question,
            "decomposition": None,
            "sql": None,
            "result": None,
            "summary": f"Unexpected error: {exc}",
            "status": "error",
            "retries": 0,
            "execution_time": execution_time,
        }
