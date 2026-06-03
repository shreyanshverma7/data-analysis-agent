from langgraph.graph import StateGraph, START, END

from state import AgentState
from nodes.ingestion import ingestion_node
from nodes.analyst import analyst_node
from nodes.codegen import codegen_node
from nodes.executor import executor_node
from nodes.critic import critic_node
from nodes.summarizer import summarizer_node


def retry_router_node(state: AgentState) -> dict:
    if state["codegen_retry_count"] < 3:
        return {"codegen_retry_count": state["codegen_retry_count"] + 1}
    elif state["replan_count"] < 1:
        return {"replan_count": 1, "codegen_retry_count": 0}
    else:
        return {"final_answer": "Unable to answer your question after multiple attempts."}


def _route_critic(state: AgentState) -> str:
    return "summarizer" if state["critic_verdict"] == "pass" else "retry_router"


def _route_retry_router(state: AgentState) -> str:
    if state["final_answer"]:
        return END
    if state["codegen_retry_count"] > 0:
        return "codegen"
    return "analyst"


builder = StateGraph(AgentState)

builder.add_node("ingestion", ingestion_node)
builder.add_node("analyst", analyst_node)
builder.add_node("codegen", codegen_node)
builder.add_node("executor", executor_node)
builder.add_node("critic", critic_node)
builder.add_node("retry_router", retry_router_node)
builder.add_node("summarizer", summarizer_node)

builder.add_edge(START, "ingestion")
builder.add_edge("ingestion", "analyst")
builder.add_edge("analyst", "codegen")
builder.add_edge("codegen", "executor")
builder.add_edge("executor", "critic")

builder.add_conditional_edges("critic", _route_critic, {
    "summarizer": "summarizer",
    "retry_router": "retry_router",
})

builder.add_conditional_edges("retry_router", _route_retry_router, {
    END: END,
    "codegen": "codegen",
    "analyst": "analyst",
})

builder.add_edge("summarizer", END)

graph = builder.compile()
