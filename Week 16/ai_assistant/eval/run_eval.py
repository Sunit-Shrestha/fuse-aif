"""
From-scratch evaluation harness for the /research agentic loop (no eval framework).

Run from ai_assistant/:  python -m eval.run_eval
Writes eval/results.md (report) and eval/results.json (raw).

Per query it records: task completion, tool-call correctness, trajectory length
(iterations), total tokens, and -- for unsuccessful cases -- a failure class:
  hard failure            -> run crashed / hit the step cap / never produced a result
  soft failure            -> run finished but the answer is wrong or over-confident
  cascading soft failure  -> a bad tool step (error / empty / malformed result) earlier in
                             the trajectory was followed by a wrong or over-confident answer
"""
import json
import sys
import time
from pathlib import Path

from app import config
from app.agent import MAX_ITERATIONS, ResearchAgent
from app.rag import RagIndex

# Required args per tool + their types (what a *valid* call looks like).
TOOL_SPECS = {
    "search_course_materials": {"query": str},
    "list_available_weeks": {},
    "record_note": {"note": str},
    "ask_user": {"question": str},
    "submit_answer": {"answer": str, "confident": bool, "sources": list},
}

# expect: "answer" (needs keywords, confident), "unconfident" (honest "can't verify/not covered"),
#         "clarify" (must ask the user)
CASES = [
    dict(id="compare_12_14", q="Compare what Week 12 and Week 14 cover. Which is more about deployment?",
         expect="answer", keywords=["ner", "fine-tun"], must_use="search_course_materials", min_searches=2, max_iter=7),
    dict(id="dataset_w14", q="Which dataset does the Week 14 assignment use?",
         expect="answer", keywords=["bitext"], must_use="search_course_materials", min_searches=1, max_iter=5),
    dict(id="dataset_w12", q="What dataset is used in Week 12 and what task is it for?",
         expect="answer", keywords=["wnut"], must_use="search_course_materials", min_searches=1, max_iter=5),
    dict(id="not_in_corpus", q="What do the course materials say about Kubernetes operators?",
         expect="unconfident", must_use="search_course_materials", min_searches=1, max_iter=6),
    dict(id="missing_week", q="Summarize the Week 99 assignment.",
         expect="unconfident", must_use="search_course_materials", min_searches=1, max_iter=6),
    dict(id="vague", q="Tell me about it.",
         expect="clarify", must_use="ask_user", min_searches=0, max_iter=3),
    # --- failure injection (assignment: "Failure Injection Test") ---
    dict(id="inject_search_down", q="Which dataset does the Week 14 assignment use?", inject="search_unavailable",
         expect="unconfident", must_use="search_course_materials", min_searches=1, max_iter=7),
    dict(id="inject_malformed", q="Which dataset does the Week 14 assignment use?", inject="malformed_search",
         expect="unconfident", must_use="search_course_materials", min_searches=1, max_iter=7),
]


ADMISSIONS = ("no mention", "not contain", "no discussion", "not include", "not mentioned", "not covered", "no information", "no week", "not find", "unable",
              "could not", "couldn't", "cannot", "can't", "unavailable", "not available", "no relevant")


def tool_calls_valid(trace, case):
    """(all calls have a known tool + correct arg names/types, expected tool was used)."""
    problems = []
    for t in trace:
        if t["tool"] == "(no tool call)":
            problems.append("model gave text instead of a tool call")
            continue
        spec = TOOL_SPECS.get(t["tool"])
        if spec is None:
            problems.append(f"unknown tool {t['tool']}")
            continue
        for arg, typ in spec.items():
            val = t["args"].get(arg)
            if not isinstance(val, typ) or (typ is str and not val.strip()):
                problems.append(f"{t['tool']}: bad/missing arg '{arg}'")
    if case["must_use"] not in [t["tool"] for t in trace]:
        problems.append(f"expected tool {case['must_use']} never used")
    n_search = sum(t["tool"] == "search_course_materials" for t in trace)
    if n_search < case["min_searches"]:
        problems.append(f"only {n_search} searches, expected >= {case['min_searches']}")
    return problems


def judge(case, out):
    """Return list of reasons the task did NOT complete (empty = success)."""
    if out["status"] == "error":
        return [f"run error: {out['error']}"]
    if out["status"] == "max_iterations":
        return ["hit max iterations without answering"]
    exp = case["expect"]
    if exp == "clarify":
        return [] if out["status"] == "needs_clarification" else ["should have asked for clarification but answered"]
    if out["status"] != "answered":
        return [f"unexpected status {out['status']}"]
    if exp == "unconfident":
        # Pass = the answer admits the gap (or is flagged confident=false). A confident, specific answer
        # with nothing to ground it is the failure this case is designed to catch.
        admits = any(p in out["answer"].lower() for p in ADMISSIONS)
        return [] if (not out.get("confident", True) or admits) else ["over-confident answer where evidence was missing/invalid"]
    missing = [k for k in case["keywords"] if k not in out["answer"].lower()]
    reasons = [f"answer missing expected content: {missing}"] if missing else []
    if not out.get("confident", True):
        reasons.append("answer flagged unconfident despite evidence being available")
    return reasons


def classify(out, reasons):
    if out["status"] in ("error", "max_iterations"):
        return "hard failure"
    bad_step = any((not t["ok"]) or "No relevant course material" in t["result"] or "\x00" in t["result"] for t in out["trace"])
    return "cascading soft failure" if bad_step else "soft failure"


def main(only=None):
    """Runs the cases (all, or ids in `only`). Results accumulate in results.json so a run cut short by
    an API quota can be resumed: quota/rate-limit errors are infrastructure problems, not agent failures,
    so those cases are left un-recorded and simply re-run next time."""
    here = Path(__file__).parent
    prev = {}
    if (here / "results.json").exists():
        prev = {r["id"]: r for r in json.loads((here / "results.json").read_text())["rows"]}
    rag = RagIndex()
    rag.load(config.INDEX_DIR)
    for case in CASES:
        if only and case["id"] not in only:
            continue
        agent = ResearchAgent(rag, inject_failure=case.get("inject"))
        try:
            out = agent.run(case["q"])
        except Exception as exc:  # harness-level crash counts as a hard failure
            out = dict(status="error", iterations=0, tokens=0, trace=[], error=str(exc), answer="", confident=False)
        if out["status"] == "error" and "429" in (out["error"] or ""):
            print(f"{case['id']:<20} SKIPPED (API quota) -- rerun later")
            continue
        reasons = judge(case, out)
        problems = tool_calls_valid(out["trace"], case)
        row = dict(id=case["id"], model=config.GEMINI_MODEL, injected=case.get("inject"), completed=not reasons,
                   tools_ok=not problems, iterations=out["iterations"], reasonable_len=out["iterations"] <= case["max_iter"],
                   tokens=out["tokens"], status=out["status"], path=[t["tool"] for t in out["trace"]],
                   answer=out.get("answer", "")[:200], tool_problems=problems,
                   failure=dict(klass=classify(out, reasons), reasons=reasons) if reasons else None)
        prev[case["id"]] = row
        print(f"{case['id']:<20} completed={row['completed']} tools_ok={row['tools_ok']} iters={row['iterations']} tokens={row['tokens']}")
        time.sleep(2)  # be gentle with the free-tier rate limit

    rows = [prev[c["id"]] for c in CASES if c["id"] in prev]
    failures = [dict(id=r["id"], **r["failure"]) for r in rows if r["failure"]]
    if not rows:
        print("no results recorded")
        return
    n = len(rows)
    lines = ["# Evaluation results (`/research` agentic loop)", "",
             f"Models: {', '.join(sorted({f'`{r['model']}`' for r in rows}))}; MAX_ITERATIONS={MAX_ITERATIONS}; {n}/{len(CASES)} queries recorded (2 are failure injections).", "",
             f"- **Task completion rate:** {sum(r['completed'] for r in rows)}/{n}",
             f"- **Tool-call correctness:** {sum(r['tools_ok'] for r in rows)}/{n} queries with all valid calls + expected tool used",
             f"- **Mean trajectory length:** {sum(r['iterations'] for r in rows) / n:.1f} iterations",
             f"- **Total tokens:** {sum(r['tokens'] for r in rows)} (mean {sum(r['tokens'] for r in rows) // n} per query)", "",
             "| id | model | injected failure | completed | tools ok | iterations | tokens | tool path |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['model']} | {r['injected'] or '-'} | {'yes' if r['completed'] else 'NO'} | {'yes' if r['tools_ok'] else 'NO'} | "
                     f"{r['iterations']} | {r['tokens']} | {' > '.join(r['path'])} |")
    lines += ["", "## Failure log", ""]
    if failures:
        lines += ["| id | class | reason |", "|---|---|---|"] + [f"| {f['id']} | {f['klass']} | {'; '.join(f['reasons'])} |" for f in failures]
    else:
        lines.append("No failed cases.")
    probs = [(r["id"], r["tool_problems"]) for r in rows if r["tool_problems"]]
    if probs:
        lines += ["", "## Tool-call problems", ""] + [f"- {i}: {'; '.join(p)}" for i, p in probs]
    lines += ["", "## Final answers (truncated)", ""] + [f"- **{r['id']}** ({r['status']}): {r['answer']}" for r in rows]
    (here / "results.md").write_text("\n".join(lines) + "\n")
    (here / "results.json").write_text(json.dumps(dict(rows=rows, failures=failures), indent=2))
    print("\n".join(lines[:8]))


if __name__ == "__main__":
    main(only=sys.argv[1:] or None)
