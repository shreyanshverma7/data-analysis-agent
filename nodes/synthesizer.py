from langchain_core.messages import HumanMessage, SystemMessage

import config
from schemas import SynthesisOutput
from state import AgentState

_SYSTEM_PROMPT = (
    "You are a senior data analyst. Synthesize the outputs from specialist agents into one "
    "clear, concise answer. IMPORTANT: defer to the Stats agent output for all factual claims "
    "and numbers — it ran real code against the data. The Narrative agent provides "
    "interpretation only. If a specialist failed, acknowledge the gap briefly and continue "
    "with available results."
)

_BOTH_FAILED = (
    "Analysis failed — both computation agents exhausted all retries. "
    "Please rephrase your question or try again."
)


def synthesizer_node(state: AgentState) -> dict:
    stats_entry = None
    viz_entry = None
    narrative_entry = None

    for entry in state["specialist_results"]:
        t = entry.get("type")
        if t == "stats":
            stats_entry = entry
        elif t == "viz":
            viz_entry = entry
        elif t == "narrative":
            narrative_entry = entry

    stats_failed = stats_entry is None or not stats_entry.get("result")
    viz_skipped = viz_entry is None
    viz_failed = (not viz_skipped) and not viz_entry.get("chart_path")

    if stats_failed and (viz_skipped or viz_failed):
        return {
            "final_answer": _BOTH_FAILED,
            "synthesis": "",
            "chart_path": "",
        }

    parts = [f"Question: {state['question']}"]

    if not stats_failed:
        parts.append(f"Stats output:\n{stats_entry['result']}")
    else:
        parts.append("Stats: unavailable (failed)")

    if not viz_skipped and not viz_failed:
        parts.append(f"Visualization: chart saved at {viz_entry['chart_path']}")
    elif viz_failed:
        parts.append("Visualization: unavailable (failed)")
    # viz_skipped: omit visualization section entirely

    if narrative_entry and narrative_entry.get("result"):
        parts.append(f"Narrative interpretation:\n{narrative_entry['result']}")

    user_content = "\n\n".join(parts)

    llm = config.get_llm(temperature=0.0).with_structured_output(SynthesisOutput)
    response = llm.invoke([
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ])
    answer = response.answer

    chart_path = (
        viz_entry["chart_path"]
        if viz_entry and viz_entry.get("chart_path")
        else ""
    )

    return {
        "final_answer": answer,
        "synthesis": answer,
        "chart_path": chart_path,
    }
