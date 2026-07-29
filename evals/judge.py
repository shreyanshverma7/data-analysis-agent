import json
import os
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

import config


def _get_judge_llm() -> ChatGroq:
    return ChatGroq(
        model=config.JUDGE_MODEL,
        api_key=os.environ.get("GROQ_API_KEY"),
        temperature=0,
    )

_SYSTEM_PROMPT = (
    "You are an impartial evaluator for a data analysis AI assistant. "
    "Score the answer on two dimensions. "
    "Return ONLY valid JSON with keys: completeness, clarity, reasoning. "
    "Do not include any other text."
)


def _numeric_score(agent_answer: str, expected_numbers: list) -> float:
    if not expected_numbers:
        return 1.0
    parsed_floats = [float(x) for x in re.findall(r"\d+\.?\d*", agent_answer)]
    matched = sum(
        1
        for item in expected_numbers
        if any(abs(f - item["value"]) <= item["tolerance"] for f in parsed_floats)
    )
    return matched / len(expected_numbers)


def evaluate(question: str, agent_answer: str, chart_path, entry: dict) -> dict:
    numeric_score = _numeric_score(agent_answer, entry.get("expected_numbers", []))

    facts = entry.get("expected_facts", [])
    facts_block = "\n".join(f"- {f}" for f in facts)
    user_content = (
        f"Question: {question}\n\n"
        f"Agent answer: {agent_answer}\n\n"
        f"Expected facts (all of these should be addressed):\n{facts_block}\n\n"
        "Score:\n"
        "- completeness (0.0–1.0): fraction of expected facts present in the answer\n"
        "- clarity (0.0–1.0): how readable, well-structured, and jargon-free the answer is\n"
        "- reasoning: one sentence explaining the scores"
    )

    llm = _get_judge_llm()
    response = llm.invoke([
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ])

    raw = response.content.strip()
    raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    try:
        parsed = json.loads(raw)
        completeness = float(parsed["completeness"])
        clarity = float(parsed["clarity"])
        reasoning = parsed["reasoning"]
    except Exception:
        completeness = 0.0
        clarity = 0.0
        reasoning = "judge parse error"

    chart_correct = entry.get("expected_chart", False) == bool(chart_path)

    return {
        "numeric_score": numeric_score,
        "completeness": completeness,
        "clarity": clarity,
        "reasoning": reasoning,
        "chart_correct": chart_correct,
    }
