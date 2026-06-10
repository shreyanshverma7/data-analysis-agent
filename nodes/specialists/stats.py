import os
import re

from e2b_code_interpreter import Sandbox
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

import config
from schemas import AnalysisPlan, CriticVerdict
from state import SpecialistState, SpecialistOutput

_ANALYST_PROMPT = """You are a data analyst. Produce a concise analysis plan to answer the question using statistics only. No visualization. Focus on aggregations, counts, means, distributions, correlations.

Each step must be a single, concrete action referencing actual column names from the schema. Keep the plan to 5 steps or fewer. Set expected_output_type to 'numeric'."""

_CODEGEN_PROMPT = """Write Python code using pandas only. No matplotlib or any chart. Print all results to stdout. The dataframe is already loaded as df. Output raw Python only, no markdown fences.

Rules:
- Do NOT import pandas or load any CSV file.
- Print all numeric results so they appear in stdout.
- When printing a Series or DataFrame, always use print(result.to_string()).
- Write clean, minimal code that directly follows the plan steps."""

_CRITIC_PROMPT = "You are a strict output validator. Decide whether the execution output adequately answers the question. Return pass only if numbers or a chart are present and relevant. Give a one-sentence reason."


def _strip_fences(text: str) -> str:
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text.strip())
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def stats_analyst_node(state: SpecialistState) -> dict:
    if state["replan_count"] > 0:
        user_content = (
            f"The previous plan failed during execution.\n\n"
            f"Previous plan:\n{state['analysis_plan']}\n\n"
            f"Generated code:\n{state['generated_code']}\n\n"
            f"Execution error:\n{state['execution_error']}\n\n"
            f"Revise the plan to fix this error. Question: {state['question']}\n\n"
            f"DataFrame schema:\n{state['df_schema']}"
        )
    else:
        user_content = (
            f"Question: {state['question']}\n\n"
            f"DataFrame schema:\n{state['df_schema']}"
        )

    llm = config.get_llm(temperature=0.0).with_structured_output(AnalysisPlan)
    response = llm.invoke([
        SystemMessage(content=_ANALYST_PROMPT),
        HumanMessage(content=user_content),
    ])
    return {"analysis_plan": "\n".join(f"{i}. {s}" for i, s in enumerate(response.steps, 1))}


def stats_codegen_node(state: SpecialistState) -> dict:
    user_content = (
        f"DataFrame schema (for column/dtype reference only — df is already loaded):\n"
        f"{state['df_schema']}\n\n"
        f"Plan to implement:\n{state['analysis_plan']}"
    )

    llm = config.get_llm(temperature=0.0)
    response = llm.invoke([
        SystemMessage(content=_CODEGEN_PROMPT),
        HumanMessage(content=user_content),
    ])
    return {"generated_code": _strip_fences(response.content)}


def stats_executor_node(state: SpecialistState) -> dict:
    prefix = (
        "import pandas as pd\n"
        "df = pd.read_csv('titanic.csv')\n"
    )
    full_code = prefix + state["generated_code"]

    with Sandbox.create(api_key=os.environ.get("E2B_API_KEY")) as sandbox:
        sandbox.files.write("titanic.csv", state["df_csv"].encode())
        execution = sandbox.run_code(full_code)

        stdout = "\n".join(execution.logs.stdout)

        if execution.error:
            error_text = f"{execution.error.name}: {execution.error.value}"
            return {"execution_output": "", "execution_error": error_text}

    return {"execution_output": stdout, "execution_error": ""}


def stats_critic_node(state: SpecialistState) -> dict:
    if state["execution_error"]:
        return {"critic_verdict": "retry"}

    if not state["execution_output"]:
        return {"critic_verdict": "retry"}

    llm = config.get_llm(temperature=0.0).with_structured_output(CriticVerdict)
    user_content = (
        f"Question: {state['question']}\n\n"
        f"Execution output:\n{state['execution_output']}"
    )
    response = llm.invoke([
        SystemMessage(content=_CRITIC_PROMPT),
        HumanMessage(content=user_content),
    ])
    return {"critic_verdict": response.verdict}


def stats_retry_router_node(state: SpecialistState) -> dict:
    if state["codegen_retries"] < 3:
        return {"codegen_retries": state["codegen_retries"] + 1}
    elif state["replan_count"] < 1:
        return {"codegen_retries": 0, "replan_count": state["replan_count"] + 1}
    else:
        return {"execution_error": "max retries exceeded"}


def stats_result_node(state: SpecialistState) -> dict:
    failed = state["execution_error"] == "max retries exceeded"
    return {
        "specialist_results": [{
            "type": "stats",
            "result": None if failed else state["execution_output"],
            "error": state["execution_error"] or None,
            "chart_path": None,
        }]
    }


def _route_after_critic(state: SpecialistState) -> str:
    return state["critic_verdict"]


def _route_after_retry(state: SpecialistState) -> str:
    if state["execution_error"] == "max retries exceeded":
        return "stats_result"
    if state["replan_count"] == 1 and state["codegen_retries"] == 0:
        return "stats_analyst"
    return "stats_codegen"


stats_graph = StateGraph(SpecialistState, output=SpecialistOutput)

stats_graph.add_node("stats_analyst", stats_analyst_node)
stats_graph.add_node("stats_codegen", stats_codegen_node)
stats_graph.add_node("stats_executor", stats_executor_node)
stats_graph.add_node("stats_critic", stats_critic_node)
stats_graph.add_node("stats_retry_router", stats_retry_router_node)
stats_graph.add_node("stats_result", stats_result_node)

stats_graph.set_entry_point("stats_analyst")
stats_graph.add_edge("stats_analyst", "stats_codegen")
stats_graph.add_edge("stats_codegen", "stats_executor")
stats_graph.add_edge("stats_executor", "stats_critic")
stats_graph.add_conditional_edges(
    "stats_critic",
    _route_after_critic,
    {"pass": "stats_result", "retry": "stats_retry_router"},
)
stats_graph.add_conditional_edges(
    "stats_retry_router",
    _route_after_retry,
    {
        "stats_codegen": "stats_codegen",
        "stats_analyst": "stats_analyst",
        "stats_result": "stats_result",
    },
)
stats_graph.add_edge("stats_result", END)

stats_subgraph = stats_graph.compile()
