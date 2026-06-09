import base64
import os
import re

from e2b_code_interpreter import Sandbox
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

import config
from state import SpecialistState, SpecialistOutput

_ANALYST_PROMPT = """You are a data visualization expert. Produce a concise plan to generate one chart that best answers the question. Describe what to plot, which columns to use, and what chart type. No statistics or print statements — the only output is a saved chart.

Rules:
- Output ONLY numbered plan steps — no code, no prose, no markdown headers.
- Each step must be a single, concrete action.
- Reference actual column names from the schema.
- Keep the plan to 5 steps or fewer."""

_CODEGEN_PROMPT = """Write Python code using pandas and matplotlib only. Generate exactly one chart. You MUST save it to outputs/chart.png using plt.savefig('outputs/chart.png', bbox_inches='tight'). Call plt.close() after saving. Do not call plt.show(). The dataframe is already loaded as df. Output raw Python only, no markdown fences.

Rules:
- Do NOT import pandas or load any CSV file.
- Always call os.makedirs('outputs', exist_ok=True) before saving.
- Write clean, minimal code that directly follows the plan steps."""

_CRITIC_PROMPT = "You are a strict output validator. Reply with exactly one word: pass or retry. No other text."

_CHART_PATH = "outputs/chart.png"


def _strip_fences(text: str) -> str:
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text.strip())
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def viz_analyst_node(state: SpecialistState) -> dict:
    llm = config.get_llm(temperature=0.0)

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

    response = llm.invoke([
        SystemMessage(content=_ANALYST_PROMPT),
        HumanMessage(content=user_content),
    ])
    return {"analysis_plan": response.content.strip()}


def viz_codegen_node(state: SpecialistState) -> dict:
    llm = config.get_llm(temperature=0.0)

    user_content = (
        f"DataFrame schema (for column/dtype reference only — df is already loaded):\n"
        f"{state['df_schema']}\n\n"
        f"Plan to implement:\n{state['analysis_plan']}"
    )

    response = llm.invoke([
        SystemMessage(content=_CODEGEN_PROMPT),
        HumanMessage(content=user_content),
    ])
    return {"generated_code": _strip_fences(response.content)}


def viz_executor_node(state: SpecialistState) -> dict:
    prefix = (
        "import matplotlib\n"
        "matplotlib.use('Agg')\n"
        "import os\n"
        "os.makedirs('outputs', exist_ok=True)\n"
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
            return {"execution_output": "", "execution_error": error_text, "chart_path": ""}

        try:
            b64_exec = sandbox.run_code(
                "import base64, os\n"
                "if os.path.exists('outputs/chart.png'):\n"
                "    with open('outputs/chart.png', 'rb') as _f:\n"
                "        print(base64.b64encode(_f.read()).decode('ascii'))\n"
            )
            b64_str = "".join(b64_exec.logs.stdout).strip()
            if b64_str:
                os.makedirs("outputs", exist_ok=True)
                with open(_CHART_PATH, "wb") as f:
                    f.write(base64.b64decode(b64_str))
                chart_path = os.path.abspath(_CHART_PATH)
            else:
                chart_path = ""
        except Exception:
            chart_path = ""

    return {"execution_output": stdout, "execution_error": "", "chart_path": chart_path}


def viz_critic_node(state: SpecialistState) -> dict:
    if state["execution_error"]:
        return {"critic_verdict": "retry"}

    if not state["chart_path"]:
        return {"critic_verdict": "retry"}

    return {"critic_verdict": "pass"}


def viz_retry_router_node(state: SpecialistState) -> dict:
    if state["codegen_retries"] < 3:
        return {"codegen_retries": state["codegen_retries"] + 1}
    elif state["replan_count"] < 1:
        return {"codegen_retries": 0, "replan_count": state["replan_count"] + 1}
    else:
        return {"execution_error": "max retries exceeded"}


def viz_result_node(state: SpecialistState) -> dict:
    failed = state["execution_error"] == "max retries exceeded"
    return {
        "specialist_results": [{
            "type": "viz",
            "result": None if failed else ("chart saved" if state["chart_path"] else None),
            "error": state["execution_error"] or None,
            "chart_path": None if failed else (state["chart_path"] or None),
        }]
    }


def _route_after_critic(state: SpecialistState) -> str:
    return state["critic_verdict"]


def _route_after_retry(state: SpecialistState) -> str:
    if state["execution_error"] == "max retries exceeded":
        return "viz_result"
    if state["replan_count"] == 1 and state["codegen_retries"] == 0:
        return "viz_analyst"
    return "viz_codegen"


viz_graph = StateGraph(SpecialistState, output=SpecialistOutput)

viz_graph.add_node("viz_analyst", viz_analyst_node)
viz_graph.add_node("viz_codegen", viz_codegen_node)
viz_graph.add_node("viz_executor", viz_executor_node)
viz_graph.add_node("viz_critic", viz_critic_node)
viz_graph.add_node("viz_retry_router", viz_retry_router_node)
viz_graph.add_node("viz_result", viz_result_node)

viz_graph.set_entry_point("viz_analyst")
viz_graph.add_edge("viz_analyst", "viz_codegen")
viz_graph.add_edge("viz_codegen", "viz_executor")
viz_graph.add_edge("viz_executor", "viz_critic")
viz_graph.add_conditional_edges(
    "viz_critic",
    _route_after_critic,
    {"pass": "viz_result", "retry": "viz_retry_router"},
)
viz_graph.add_conditional_edges(
    "viz_retry_router",
    _route_after_retry,
    {
        "viz_codegen": "viz_codegen",
        "viz_analyst": "viz_analyst",
        "viz_result": "viz_result",
    },
)
viz_graph.add_edge("viz_result", END)

viz_subgraph = viz_graph.compile()
