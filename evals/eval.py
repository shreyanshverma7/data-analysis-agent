# D9: two-pass eval — pass 1 runs the 70B agent (25s sleep to stay under 12K TPM),
# pass 2 runs the 17B Scout judge on cached answers (30K TPM, no sleep needed).
# Re-run judge only: python evals/eval.py --judge-pass

import argparse
import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import run_agent
from evals.judge import evaluate

_EVAL_SET = os.path.join(os.path.dirname(__file__), "titanic_eval_set.jsonl")
_CACHE_FILE = os.path.join(os.path.dirname(__file__), "answers_cache.json")


def _load_dataset() -> list:
    with open(_EVAL_SET) as f:
        return [json.loads(line) for line in f if line.strip()]


def run_agent_pass() -> None:
    entries = _load_dataset()
    cache = []

    for i, entry in enumerate(entries, 1):
        print(f"[{i:02d}/{len(entries)}] {entry['question'][:50]}...")
        try:
            result = run_agent(entry["question"], [])
            cache.append({
                "id": entry["id"],
                "category": entry["category"],
                "question": entry["question"],
                "answer": result["answer"],
                "chart_path": result["chart_path"],
                "error": None,
            })
        except Exception as e:
            cache.append({
                "id": entry["id"],
                "category": entry["category"],
                "question": entry["question"],
                "answer": None,
                "chart_path": None,
                "error": str(e),
            })

        if i < len(entries):
            print(f"  sleeping 25s...")
            time.sleep(25)

    with open(_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)
    print(f"\nAgent pass complete. Answers saved to: {_CACHE_FILE}")


def run_judge_pass() -> str:
    with open(_CACHE_FILE) as f:
        cache = json.load(f)

    entries = {e["id"]: e for e in _load_dataset()}
    results = []

    for item in cache:
        if item["error"] is not None:
            results.append({
                "id": item["id"],
                "category": item["category"],
                "question": item["question"],
                "answer": item["answer"],
                "numeric_score": None,
                "completeness": None,
                "clarity": None,
                "chart_correct": None,
                "reasoning": None,
                "error": item["error"],
            })
            continue

        entry = entries[item["id"]]
        scores = evaluate(item["question"], item["answer"], item["chart_path"], entry)
        results.append({
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "answer": item["answer"],
            "numeric_score": scores["numeric_score"],
            "completeness": scores["completeness"],
            "clarity": scores["clarity"],
            "chart_correct": scores["chart_correct"],
            "reasoning": scores["reasoning"],
            "error": None,
        })

    scored = [r for r in results if r["error"] is None]
    error_count = len(results) - len(scored)

    def _mean(key):
        vals = [r[key] for r in scored if r[key] is not None]
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    chart_correct_count = sum(1 for r in scored if r["chart_correct"])

    aggregate = {
        "numeric_score_mean": _mean("numeric_score"),
        "completeness_mean": _mean("completeness"),
        "clarity_mean": _mean("clarity"),
        "chart_correct_rate": round(chart_correct_count / len(scored), 4) if scored else 0.0,
        "total": len(results),
        "errors": error_count,
    }

    filename = f"evals/results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump({"results": results, "aggregate": aggregate}, f, indent=2)

    print(f"\n=== Eval Results ===")
    print(f"Numeric score:    {aggregate['numeric_score_mean']:.2f}")
    print(f"Completeness:     {aggregate['completeness_mean']:.2f}")
    print(f"Clarity:          {aggregate['clarity_mean']:.2f}")
    print(f"Chart correct:    {chart_correct_count}/{len(scored)}")
    print(f"Errors:           {error_count}")
    print(f"Results saved to: {filename}")

    return filename


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-pass", action="store_true")
    parser.add_argument("--judge-pass", action="store_true")
    args = parser.parse_args()

    if args.agent_pass:
        run_agent_pass()
    elif args.judge_pass:
        run_judge_pass()
    else:
        run_agent_pass()
        run_judge_pass()
