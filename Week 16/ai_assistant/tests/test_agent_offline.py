"""
Offline tests for the agentic loop: a scripted fake LLM replaces Gemini, so the
loop logic, guardrails, context clearing and the eval judge are checked with no API key.

Run from ai_assistant/:  python -m pytest tests -q   (or: python -m tests.test_agent_offline)
"""
from types import SimpleNamespace

from google.genai import types

from app import agent as agent_mod
from app.agent import CLEARED_STUB, MAX_ITERATIONS, ResearchAgent
from app.rag import Chunk
from eval.run_eval import CASES, classify, judge, tool_calls_valid


class FakeRag:
    chunks = [Chunk("ner stuff", "Week_12_W12_Guide.txt"), Chunk("llm stuff", "Week_14_W14_guide.txt")]

    def search(self, query, top_k=4):
        return [c for c in self.chunks if ("12" in query) == c.source.startswith("Week_12")] or []


def call(name, **args):
    content = types.Content(role="model", parts=[types.Part(function_call=types.FunctionCall(name=name, args=args))])
    return SimpleNamespace(function_calls=[content.parts[0].function_call], candidates=[SimpleNamespace(content=content)],
                           usage_metadata=SimpleNamespace(total_token_count=100), text=None)


def text(t):
    content = types.Content(role="model", parts=[types.Part(text=t)])
    return SimpleNamespace(function_calls=None, candidates=[SimpleNamespace(content=content)], usage_metadata=SimpleNamespace(total_token_count=50), text=t)


class FakeLLM:
    """Replays scripted responses; records the `contents` it was sent each turn."""

    def __init__(self, script):
        self.script, self.seen = list(script), []
        self.models = SimpleNamespace(generate_content=self._gen)

    def _gen(self, model, contents, config):
        self.seen.append([p for c in contents for p in c.parts])
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def make(script, inject=None):
    a = ResearchAgent(FakeRag(), inject_failure=inject)
    a._client = FakeLLM(script)
    return a


def test_multi_step_answer_and_token_sum():
    a = make([call("search_course_materials", query="Week 12"), call("record_note", note="12: NER"),
              call("search_course_materials", query="Week 14"),
              call("submit_answer", answer="ner vs llm", confident=True, sources=["Week_12_W12_Guide.txt"])])
    out = a.run("compare")
    assert out["status"] == "answered" and out["iterations"] == 4 and out["tokens"] == 400
    assert out["confident"] and [t["tool"] for t in out["trace"]][-1] == "submit_answer"


def test_submit_before_search_rejected_then_recovers():
    a = make([call("submit_answer", answer="guess", confident=True, sources=[]),
              call("search_course_materials", query="Week 12"),
              call("submit_answer", answer="ok", confident=True, sources=[])])
    out = a.run("q")
    assert out["iterations"] == 3 and "REJECTED" in out["trace"][0]["result"] and out["answer"] == "ok"


def test_ask_user_stops_loop():
    out = make([call("ask_user", question="which week?")]).run("it")
    assert out["status"] == "needs_clarification" and out["answer"] == "which week?" and out["iterations"] == 1


def test_max_iterations_cap():
    out = make([call("list_available_weeks")] * (MAX_ITERATIONS + 5)).run("loop forever")
    assert out["status"] == "max_iterations" and out["iterations"] == MAX_ITERATIONS and out["confident"] is False


def test_budget_notice_near_cap():
    a = make([call("list_available_weeks")] * MAX_ITERATIONS)
    a.run("q")
    texts = lambda turn: [p.text for p in turn if p.text and "Budget notice" in p.text]
    assert not texts(a._client.seen[MAX_ITERATIONS - 4]) and texts(a._client.seen[-1])


def test_llm_error_stops(monkeypatch=None):
    agent_mod.RETRY_SLEEP_S = 0
    out = make([RuntimeError("boom")]).run("q")
    assert out["status"] == "error" and "boom" in out["error"]


def test_transient_429_is_retried_but_daily_quota_is_not():
    agent_mod.RETRY_SLEEP_S = 0
    a = make([RuntimeError("429 RESOURCE_EXHAUSTED per minute"), call("ask_user", question="?")])
    assert a.run("q")["status"] == "needs_clarification"
    b = make([RuntimeError("429 ... GenerateRequestsPerDayPerProjectPerModel"), call("ask_user", question="?")])
    assert b.run("q")["status"] == "error"


def test_unknown_tool_and_bad_args_do_not_crash():
    out = make([call("nope"), call("search_course_materials"), call("ask_user", question="?")]).run("q")
    assert out["status"] == "needs_clarification"
    assert out["trace"][0]["ok"] is False and out["trace"][1]["ok"] is False  # TypeError from missing arg


def test_plain_text_reply_is_nudged_then_recovers():
    a = make([call("search_course_materials", query="Week 12"), text("done"),
              call("submit_answer", answer="ok", confident=True, sources=[])])
    out = a.run("q")
    assert out["status"] == "answered" and out["confident"] is True and out["iterations"] == 3
    assert "Respond only by calling a tool" in a._client.seen[2][-1].text


def test_two_plain_text_replies_end_unconfident():
    out = make([text("a"), text("b")]).run("q")
    assert out["status"] == "answered" and out["confident"] is False and out["answer"] == "b"


def test_stale_results_cleared_but_latest_two_kept():
    a = make([call("search_course_materials", query="Week 12"), call("search_course_materials", query="Week 14"),
              call("search_course_materials", query="Week 12 again"), call("search_course_materials", query="x"),
              call("ask_user", question="?")])
    a.run("q")
    last_turn = a._client.seen[-1]
    results = [p.function_response.response["result"] for p in last_turn
               if p.function_response and p.function_response.name == "search_course_materials"]
    assert len(results) == 4 and results[:2] == [CLEARED_STUB] * 2 and CLEARED_STUB not in results[2:]


def test_passages_capped():
    a = ResearchAgent(FakeRag())
    a.rag.chunks = [Chunk("x" * 5000, "Week_12_W12_Guide.txt")]
    st = agent_mod.AgentState()
    res = a._make_tools(st)["search_course_materials"]("Week 12")
    assert len(res) < 600 and st.sources == ["Week_12_W12_Guide.txt"]


def test_failure_injection_paths():
    a = make([call("search_course_materials", query="Week 12"),
              call("submit_answer", answer="cannot verify", confident=False, sources=[])], inject="search_unavailable")
    out = a.run("q")
    assert out["trace"][0]["ok"] is False and "unavailable" in out["trace"][0]["result"] and out["confident"] is False
    b = make([call("search_course_materials", query="Week 12"), call("ask_user", question="?")], inject="malformed_search")
    assert "\x00" in b.run("q")["trace"][0]["result"]


def test_eval_judge_validity_and_classification():
    case = {c["id"]: c for c in CASES}
    ok = make([call("search_course_materials", query="Week 12"), call("search_course_materials", query="Week 14"),
               call("submit_answer", answer="NER and fine-tuning", confident=True, sources=[])]).run("q")
    assert judge(case["compare_12_14"], ok) == [] and tool_calls_valid(ok["trace"], case["compare_12_14"]) == []
    # over-confident answer after a failed search -> cascading soft failure
    bad = make([call("search_course_materials", query="Week 12"),
                call("submit_answer", answer="Bitext", confident=True, sources=[])], inject="search_unavailable").run("q")
    reasons = judge(case["inject_search_down"], bad)
    assert reasons and classify(bad, reasons) == "cascading soft failure"
    # honest confident "not covered" passes; a confident invented answer to an unanswerable query fails
    nf = {"answer": "There is no mention of Kubernetes in the materials.", "status": "answered", "confident": True}
    assert judge(case["not_in_corpus"], nf) == []
    assert judge(case["not_in_corpus"], {**nf, "answer": "Operators automate cluster apps."})
    # cap hit -> hard failure; wrong answer with clean trace -> soft failure
    cap = make([call("list_available_weeks")] * 10).run("q")
    assert classify(cap, judge(case["dataset_w14"], cap)) == "hard failure"
    soft = make([call("search_course_materials", query="Week 12"),
                 call("submit_answer", answer="nothing", confident=True, sources=[])]).run("q")
    assert classify(soft, judge(case["dataset_w12"], soft)) == "soft failure"
    assert tool_calls_valid([{"tool": "search_course_materials", "args": {"query": ""}, "ok": True, "result": ""}],
                            case["dataset_w12"])


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
