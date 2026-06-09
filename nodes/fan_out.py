from langgraph.types import Send

from state import AgentState, SpecialistState


def fan_out_node(state: AgentState) -> list[Send]:
    stats_state = SpecialistState(
        specialist_type="stats",
        question=state["question"],
        df_csv=state["df_csv"],
        df_schema=state["df_schema"],
        overview_plan="",
        analysis_plan="",
        generated_code="",
        execution_output="",
        execution_error="",
        chart_path="",
        result="",
        codegen_retries=0,
        replan_count=0,
        critic_verdict="",
        specialist_results=[],
    )

    viz_state = SpecialistState(
        specialist_type="viz",
        question=state["question"],
        df_csv=state["df_csv"],
        df_schema=state["df_schema"],
        overview_plan="",
        analysis_plan="",
        generated_code="",
        execution_output="",
        execution_error="",
        chart_path="",
        result="",
        codegen_retries=0,
        replan_count=0,
        critic_verdict="",
        specialist_results=[],
    )

    numeric_markers = ("int64", "float64", "datetime")
    has_numeric = any(m in state["df_schema"] for m in numeric_markers)

    if has_numeric:
        return [
            Send("stats_subgraph", stats_state),
            Send("viz_subgraph", viz_state),
        ]
    return [Send("stats_subgraph", stats_state)]
