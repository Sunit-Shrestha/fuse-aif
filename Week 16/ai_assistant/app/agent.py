"""
Agentic "verified research" loop (W16).

Unlike the W15 /chat flow (one retrieval-tool pass, then a fixed JSON repackaging
call), here the model drives a manual loop: after every tool result it decides
whether to search again (different query / different week), ask the user a
clarifying question, or submit a final answer. The application never decides the
next step -- it only executes the tool the model picked and enforces guardrails.

Stopping conditions (the loop can never run forever):
  - model calls submit_answer (accepted)          -> status "answered"
  - model calls ask_user                          -> status "needs_clarification"
  - MAX_ITERATIONS reached                        -> status "max_iterations"
  - an LLM/tool exception that can't be recovered -> status "error"

Context engineering (see README): retrieval results are (1) capped in size and
(2) *cleared* once stale -- only the most recent KEEP_FULL_RESULTS tool results are
kept verbatim; older ones are replaced with a stub. The model is told to save what
it learned via record_note; those short note calls stay in the history (only search/list
results are cleared), so cleared evidence isn't lost.
"""
import time
from dataclasses import dataclass, field

from google import genai
from google.genai import types

from . import config
from .net import ipv4_httpx_client
from .rag import RagIndex

MAX_ITERATIONS = 8
KEEP_FULL_RESULTS = 2  # older tool results are cleared to a stub
MAX_CHARS_PER_CHUNK = 500  # cap per retrieved passage
BUDGET_WARNING_AT = 2  # warn the model when this many iterations remain
RETRIES = 3  # transient LLM errors (429 rate limit / 503) are retried with backoff
RETRY_SLEEP_S = 20
CLEARED_STUB = "[tool result cleared to save context -- see your recorded notes]"

AGENT_SYSTEM_INSTRUCTION = (
    "You are a careful research agent for the Fusemachines AI Fellowship course materials. "
    "Work in steps, using ONE tool call per step, and look at each result before choosing the next step.\n"
    "Rules:\n"
    "- Use search_course_materials to find evidence. Never answer from memory.\n"
    "- If the question mentions several weeks/topics or compares them, search each one separately "
    "(put 'Week N' in the query to target a week).\n"
    "- If a search result is empty, off-topic, or an error, try a differently-worded query or another "
    "tool. If a tool returns an error or garbage twice in a row, stop retrying and do NOT guess: submit_answer with confident=false and "
    "explain that you could not verify.\n"
    "- Call record_note for each key fact you find (retrieved text will be cleared later).\n"
    "- Be efficient: at most 2 searches per topic, then submit_answer as soon as the evidence suffices. "
    "If the materials do not cover something, say so in the answer rather than searching endlessly.\n"
    "- State only facts that appear in tool results (e.g. call list_available_weeks rather than guessing which weeks exist).\n"
    "- Always finish by calling submit_answer, never with a plain-text reply.\n"
    "- If the question is too vague to search, call ask_user instead of guessing.\n"
    "- When you have enough evidence, call submit_answer with the sources you actually used."
)


@dataclass
class AgentState:
    notes: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    searches: int = 0
    final: dict | None = None
    question: str | None = None
    trace: list[dict] = field(default_factory=list)  # one entry per tool call
    total_tokens: int = 0


class ResearchAgent:
    def __init__(self, rag_index: RagIndex, inject_failure: str | None = None):
        # inject_failure="search_unavailable" | "malformed_search": failure-injection hook
        self.rag = rag_index
        self.inject_failure = inject_failure
        self._client = genai.Client(
            api_key=config.GEMINI_API_KEY,
            http_options=types.HttpOptions(httpx_client=ipv4_httpx_client()),
        )

    def _generate(self, contents, cfg):
        for attempt in range(RETRIES + 1):
            try:
                return self._client.models.generate_content(model=config.GEMINI_MODEL, contents=contents, config=cfg)
            except Exception as exc:
                transient = any(code in str(exc) for code in ("429", "503", "UNAVAILABLE"))
                # A *daily* quota 429 won't clear by waiting, so don't burn time retrying it.
                if not transient or "PerDay" in str(exc) or attempt == RETRIES:
                    raise
                time.sleep(RETRY_SLEEP_S * (attempt + 1))

    def _make_tools(self, state: AgentState):
        def search_course_materials(query: str) -> str:
            """Search the course materials. Include 'Week N' in the query to restrict to one week.

            Args:
                query: Short search query.
            """
            state.searches += 1
            if self.inject_failure == "search_unavailable":
                raise ConnectionError("search backend unavailable (503)")
            if self.inject_failure == "malformed_search":
                return "\x00\x00<<corrupt>> ???"
            chunks = self.rag.search(query, top_k=config.TOP_K)
            if not chunks:
                return "No relevant course material found."
            for c in chunks:
                if c.source not in state.sources:
                    state.sources.append(c.source)
            return "\n\n".join(f"[Source: {c.source}]\n{c.text[:MAX_CHARS_PER_CHUNK]}" for c in chunks)

        def list_available_weeks() -> str:
            """List which weeks of course material exist."""
            import re

            weeks = {int(m.group(1)) for c in self.rag.chunks if (m := re.match(r"Week_(\d+)_", c.source))}
            return "Available weeks: " + ", ".join(str(w) for w in sorted(weeks))

        def record_note(note: str) -> str:
            """Save one short fact learned so far (with its source file) to your notes.

            Args:
                note: One concise fact, e.g. 'Week 12: uses X (Week_12_W12_Guide.txt)'.
            """
            state.notes.append(note)
            return f"Saved. You now have {len(state.notes)} notes."

        def ask_user(question: str) -> str:
            """Ask the user a clarifying question when the request is too vague. Ends the run.

            Args:
                question: The question to ask the user.
            """
            state.question = question
            return "Question sent to user."

        def submit_answer(answer: str, confident: bool, sources: list[str]) -> str:
            """Submit the final answer. Ends the run.

            Args:
                answer: Final answer for the user.
                confident: False if evidence was missing/unverifiable.
                sources: Source filenames actually used.
            """
            if state.searches == 0:
                return "REJECTED: you have not searched yet. Search the course materials first."
            state.final = {"answer": answer, "confident": confident, "sources": sources}
            return "Answer accepted."

        return {f.__name__: f for f in (search_course_materials, list_available_weeks, record_note, ask_user, submit_answer)}

    @staticmethod
    def _clear_stale_results(contents: list[types.Content]) -> None:
        """Context engineering: keep only the newest KEEP_FULL_RESULTS search/list results verbatim."""
        idx = [
            (i, j)
            for i, c in enumerate(contents)
            for j, p in enumerate(c.parts)
            if p.function_response and p.function_response.name in ("search_course_materials", "list_available_weeks")
        ]
        for i, j in idx[:-KEEP_FULL_RESULTS]:
            fr = contents[i].parts[j].function_response
            contents[i].parts[j] = types.Part.from_function_response(name=fr.name, response={"result": CLEARED_STUB})

    def run(self, message: str, temperature: float = 0.2) -> dict:
        state = AgentState()
        tools = self._make_tools(state)
        cfg = types.GenerateContentConfig(
            system_instruction=AGENT_SYSTEM_INSTRUCTION,
            temperature=temperature,
            tools=list(tools.values()),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        contents: list[types.Content] = [types.Content(role="user", parts=[types.Part(text=message)])]
        status = "max_iterations"
        error = None
        iterations = 0
        nudged = False

        for iterations in range(1, MAX_ITERATIONS + 1):
            try:
                resp = self._generate(contents, cfg)
            except Exception as exc:  # LLM call itself failed: stop, don't loop
                status, error = "error", f"LLM call failed: {exc}"
                break
            state.total_tokens += (resp.usage_metadata.total_token_count or 0) if resp.usage_metadata else 0

            calls = resp.function_calls or []
            if not calls:
                state.trace.append({"tool": "(no tool call)", "args": {}, "ok": False, "result": resp.text or ""})
                if nudged or not resp.candidates:
                    # Second text-only reply: accept it, but flag it as an unverified answer.
                    state.final = {"answer": resp.text or "", "confident": False, "sources": []}
                    status = "answered"
                    break
                # First text-only reply: the model skipped the protocol. Redirect it to submit_answer
                # (still counts against MAX_ITERATIONS, so this cannot loop).
                nudged = True
                contents.append(resp.candidates[0].content)
                contents.append(types.Content(role="user", parts=[types.Part(text=(
                    "Respond only by calling a tool. If you have finished, call submit_answer "
                    "(confident=false if evidence is missing); otherwise call the next tool."))]))
                continue

            contents.append(resp.candidates[0].content)
            response_parts = []
            for call in calls:  # every function_call must get a matching response
                args = dict(call.args or {})
                fn = tools.get(call.name)
                if fn is None:
                    result, ok = f"ERROR: unknown tool {call.name}", False
                else:
                    try:
                        result, ok = fn(**args), True
                    except Exception as exc:
                        result, ok = f"ERROR: {type(exc).__name__}: {exc}", False
                state.trace.append({"tool": call.name, "args": args, "ok": ok, "result": str(result)[:300]})
                response_parts.append(types.Part.from_function_response(name=call.name, response={"result": result}))
            left = MAX_ITERATIONS - iterations
            if left <= BUDGET_WARNING_AT and state.final is None and state.question is None:
                # Budget awareness: tell the model the loop is about to be cut off so it wraps up
                # with what it has instead of hitting the cap with no answer.
                response_parts.append(types.Part(text=f"[Budget notice: {left} step(s) left. Call submit_answer now "
                                                       "with what you have; set confident=false if evidence is incomplete.]"))
            contents.append(types.Content(role="user", parts=response_parts))
            self._clear_stale_results(contents)

            if state.final is not None:
                status = "answered"
                break
            if state.question is not None:
                status = "needs_clarification"
                break

        out = {
            "status": status,
            "iterations": iterations,
            "tokens": state.total_tokens,
            "trace": state.trace,
            "error": error,
        }
        if state.final:
            out.update(state.final)
        elif state.question:
            out["answer"] = state.question
        else:
            out["answer"] = "I could not finish within the step limit; partial notes: " + "; ".join(state.notes)
            out["confident"] = False
            out["sources"] = state.sources
        return out
