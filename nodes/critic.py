from langchain_core.messages import HumanMessage, SystemMessage
import config
from state import AgentState

SYSTEM_PROMPT = (
    "You are a strict output validator. "
    "Reply with exactly one word: pass or retry. No other text."
)


def critic_node(state: AgentState) -> dict:
    if state["execution_error"]:
        return {"critic_verdict": "retry"}

    if not state["execution_output"] and not state["chart_path"]:
        return {"critic_verdict": "retry"}

    chart_note = (
        f"A chart was saved to {state['chart_path']}."
        if state["chart_path"]
        else "No chart was saved."
    )

    user_content = (
        f"Question: {state['question']}\n\n"
        f"Execution output:\n{state['execution_output']}\n\n"
        f"{chart_note}\n\n"
        "Note: if the question asks for a chart, plot, graph, or histogram and a chart file "
        "was saved, that counts as a complete and valid answer even if the text output is empty.\n\n"
        "Does the output (including any saved chart) adequately answer the question? "
        "Reply with exactly one word: pass or retry."
    )

    llm = config.get_llm(temperature=0.0)
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ])

    verdict = response.content.strip().lower()
    verdict = "pass" if verdict.startswith("pass") else "retry"
    return {"critic_verdict": verdict}
