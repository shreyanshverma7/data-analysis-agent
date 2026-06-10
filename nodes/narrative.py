from langchain_core.messages import HumanMessage, SystemMessage

import config
from schemas import NarrativeOutput
from state import AgentState

_SYSTEM_PROMPT = (
    "You are a data analyst. Given the question and the computed statistics below, "
    "write a concise 2-3 sentence interpretation. Explain what the numbers mean, "
    "any notable pattern, and why it matters. Do not restate the numbers — interpret them."
)

_SYSTEM_PROMPT_FALLBACK = (
    "You are a data analyst. Stats computation was unavailable for this question. "
    "Based on the DataFrame schema alone, write a concise 2-3 sentence interpretation "
    "of what the data likely shows. "
    "Begin your response with exactly: 'Based on schema only — stats unavailable:'"
)


def narrative_node(state: AgentState) -> dict:
    stats_output = None
    for entry in state["specialist_results"]:
        if entry.get("type") == "stats" and entry.get("result"):
            stats_output = entry["result"]
            break

    if stats_output is not None:
        user_content = (
            f"Question: {state['question']}\n\n"
            f"Computed statistics:\n{stats_output}"
        )
        system_prompt = _SYSTEM_PROMPT
    else:
        user_content = (
            f"Question: {state['question']}\n\n"
            f"DataFrame schema:\n{state['df_schema']}"
        )
        system_prompt = _SYSTEM_PROMPT_FALLBACK

    try:
        llm = config.get_llm(temperature=0.0).with_structured_output(NarrativeOutput)
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content),
        ])
        result = response.interpretation
        error = None
    except Exception as e:
        result = None
        error = str(e)

    return {
        "specialist_results": [{
            "type": "narrative",
            "result": result,
            "error": error,
            "chart_path": None,
        }]
    }
