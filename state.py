import operator
from typing import Annotated, TypedDict


class AgentState(TypedDict):
    question: str
    df_csv: str
    df_schema: str
    messages: list
    chart_path: str
    final_answer: str
    specialist_results: Annotated[list, operator.add]
    synthesis: str


class SpecialistState(TypedDict):
    specialist_type: str
    question: str
    df_csv: str
    df_schema: str
    overview_plan: str
    analysis_plan: str
    generated_code: str
    execution_output: str
    execution_error: str
    chart_path: str
    result: str
    codegen_retries: int
    replan_count: int
    critic_verdict: str
    specialist_results: Annotated[list, operator.add]


class SpecialistOutput(TypedDict):
    specialist_results: Annotated[list, operator.add]


def default_state(question: str) -> AgentState:
    return AgentState(
        question=question,
        df_csv="",
        df_schema="",
        messages=[],
        chart_path="",
        final_answer="",
        specialist_results=[],
        synthesis="",
    )
