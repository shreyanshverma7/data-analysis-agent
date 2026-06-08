from langchain_core.messages import AIMessage, HumanMessage

from state import AgentState


def summarizer_node(state: AgentState) -> dict:
    answer = state["synthesis"] or state["final_answer"]

    updated_messages = list(state["messages"]) + [
        HumanMessage(content=state["question"]),
        AIMessage(content=answer),
    ]

    return {"messages": updated_messages}
