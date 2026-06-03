import re
from langchain_core.messages import HumanMessage, SystemMessage
import config
from state import AgentState

SYSTEM_PROMPT = """You are a Python code generator. Output raw Python code only — \
no markdown fences, no explanation, no comments.

Rules:
- A pandas DataFrame called `df` is already loaded in the environment. Do NOT import pandas \
or load any CSV file.
- You may import other libraries (matplotlib, numpy, etc.) as needed.
- If the plan requires a chart, you MUST save it with EXACTLY plt.savefig("outputs/chart.png") \
followed immediately by plt.close(). Never use plt.show(). Ignore any filename the plan suggests \
— always use "outputs/chart.png".
- Print all numeric results so they appear in stdout.
- When printing a Series or DataFrame, always use print(result.to_string()) so that index labels and column names are included in the output.
- Write clean, minimal code that directly follows the plan steps."""


def _strip_fences(text: str) -> str:
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text.strip())
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def codegen_node(state: AgentState) -> dict:
    llm = config.get_llm(temperature=0.0)

    user_content = (
        f"DataFrame schema (for column/dtype reference only — df is already loaded):\n"
        f"{state['df_schema']}\n\n"
        f"Plan to implement:\n{state['analysis_plan']}"
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]

    response = llm.invoke(messages)
    generated_code = _strip_fences(response.content)
    return {"generated_code": generated_code}
