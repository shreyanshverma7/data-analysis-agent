from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import config
from state import AgentState

SYSTEM_PROMPT = (
    "You are a data analyst writing a clear, concise answer for a non-technical user. "
    "Use only the execution output provided. "
    "Do not invent numbers or facts not present in the output."
)


def summarizer_node(state: AgentState) -> dict:
    user_content = (
        f"Question: {state['question']}\n\n"
        f"Execution output:\n{state['execution_output']}"
    )
    if state["chart_path"]:
        user_content += f"\n\nA chart has been saved to: {state['chart_path']}"

    llm = config.get_llm(temperature=0.0)
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ])

    final_answer = response.content.strip()

    updated_messages = list(state["messages"]) + [
        HumanMessage(content=state["question"]),
        AIMessage(content=final_answer),
    ]

    return {"final_answer": final_answer, "messages": updated_messages}
