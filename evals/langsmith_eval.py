import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: F401 — loads .env and sets LANGCHAIN_* env vars before langsmith imports

from langsmith import Client
from langsmith.evaluation import evaluate as ls_evaluate

_EVAL_SET = os.path.join(os.path.dirname(__file__), "titanic_eval_set.jsonl")
_DATASET_NAME = "titanic-eval-v2"


def _load_dataset() -> list:
    with open(_EVAL_SET) as f:
        return [json.loads(line) for line in f if line.strip()]


def _ensure_dataset(client: Client) -> None:
    existing = list(client.list_datasets(dataset_name=_DATASET_NAME))
    if existing:
        print(f"Dataset '{_DATASET_NAME}' already exists — skipping creation.")
        return

    entries = _load_dataset()
    dataset = client.create_dataset(_DATASET_NAME)
    client.create_examples(
        inputs=[{"question": e["question"]} for e in entries],
        outputs=[
            {
                "expected_numbers": e["expected_numbers"],
                "expected_facts": e["expected_facts"],
                "expected_chart": e["expected_chart"],
            }
            for e in entries
        ],
        dataset_id=dataset.id,
    )
    print(f"Dataset '{_DATASET_NAME}' created with {len(entries)} examples.")


def run_pipeline(inputs: dict) -> dict:
    from agent import run_agent
    result = run_agent(inputs["question"], [])
    return {"answer": result["answer"], "chart_path": result["chart_path"]}


def eval_numeric_score(run, example):
    from evals.judge import evaluate
    scores = evaluate(
        example.inputs["question"],
        run.outputs["answer"],
        run.outputs.get("chart_path"),
        example.outputs,
    )
    return {"key": "numeric_score", "score": scores["numeric_score"]}


def eval_completeness(run, example):
    from evals.judge import evaluate
    scores = evaluate(
        example.inputs["question"],
        run.outputs["answer"],
        run.outputs.get("chart_path"),
        example.outputs,
    )
    return {"key": "completeness", "score": scores["completeness"]}


def eval_clarity(run, example):
    from evals.judge import evaluate
    scores = evaluate(
        example.inputs["question"],
        run.outputs["answer"],
        run.outputs.get("chart_path"),
        example.outputs,
    )
    return {"key": "clarity", "score": scores["clarity"]}


def eval_chart_correct(run, example):
    from evals.judge import evaluate
    scores = evaluate(
        example.inputs["question"],
        run.outputs["answer"],
        run.outputs.get("chart_path"),
        example.outputs,
    )
    return {"key": "chart_correct", "score": 1.0 if scores["chart_correct"] else 0.0}


def run_langsmith_eval() -> None:
    client = Client()
    _ensure_dataset(client)

    results = ls_evaluate(
        run_pipeline,
        data=_DATASET_NAME,
        evaluators=[eval_numeric_score, eval_completeness, eval_clarity, eval_chart_correct],
        experiment_prefix="v2-parallel-agents",
    )

    experiment_name = getattr(results, "experiment_name", None)
    print(f"\nExperiment: {experiment_name or 'v2-parallel-agents-*'}")
    print("View results in LangSmith → Datasets → titanic-eval-v2 → Experiments")


if __name__ == "__main__":
    run_langsmith_eval()
