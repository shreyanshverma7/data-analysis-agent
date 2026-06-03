from typing import TypedDict


class AgentState(TypedDict):
    question: str           # original user question
    df_csv: str             # full CSV string — REPL loads df from this
    df_schema: str          # shape + dtypes + null counts + head(5)
    analysis_plan: str      # analyst node → step-by-step plan
    generated_code: str     # codegen node → raw Python string
    execution_output: str   # stdout captured from PythonREPLTool
    execution_error: str    # exception text, empty string if clean run
    critic_verdict: str     # "pass" or "retry"
    codegen_retry_count: int  # incremented on each code-gen retry; max 3
    replan_count: int         # incremented on analyst re-plan; max 1
    chart_path: str         # abs path to saved .png, or empty string
    final_answer: str       # summarizer → clean natural-language response
    messages: list          # full HumanMessage / AIMessage history


def default_state(question: str) -> AgentState:
    return AgentState(
        question=question,
        df_csv="",
        df_schema="",
        analysis_plan="",
        generated_code="",
        execution_output="",
        execution_error="",
        critic_verdict="",
        codegen_retry_count=0,
        replan_count=0,
        chart_path="",
        final_answer="",
        messages=[],
    )
