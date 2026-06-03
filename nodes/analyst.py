from langchain_core.messages import HumanMessage, SystemMessage
import config
from state import AgentState

SYSTEM_PROMPT = """You are a senior data analyst. Your only job is to produce a clear, \
step-by-step analysis plan that a Python programmer can follow to answer the user's question \
using a pandas DataFrame called `df`.

Rules:
- Output ONLY the numbered plan steps — no code, no prose, no markdown headers.
- Each step must be a single, concrete action (e.g. "Filter df to rows where Survived == 1").
- Reference actual column names from the schema.
- If a matplotlib chart is needed, include a step that saves it with plt.savefig().
- Keep the plan to 5 steps or fewer.
- Do not explain yourself — just the steps.
- If the question contains pronouns like 'that', 'it', or 'those', resolve them explicitly from the conversation history before writing the plan. State the resolved subject in your first step (e.g. 'Step 1: Compute average Fare grouped by Survived and Sex — continuing from the prior question about fare by survival status')."""


def analyst_node(state: AgentState) -> dict:
    llm = config.get_llm(temperature=0.0)

    window = config.SLIDING_WINDOW
    recent_messages = state["messages"][-(window * 2):] if state["messages"] else []

    FOLLOW_UP_WORDS = {"that", "it", "those", "this", "them", "they"}
    is_follow_up = any(w in FOLLOW_UP_WORDS for w in state["question"].lower().split())

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
        if is_follow_up and len(recent_messages) >= 2:
            user_content = (
                f"Prior question: {recent_messages[-2].content}\n"
                f"Prior answer: {recent_messages[-1].content}\n\n"
                f"Follow-up question: {state['question']}\n\n"
                f"DataFrame schema:\n{state['df_schema']}"
            )
        else:
            user_content = (
                f"Question: {state['question']}\n\n"
                f"DataFrame schema:\n{state['df_schema']}"
            )

    messages = [SystemMessage(content=SYSTEM_PROMPT)] + recent_messages + [HumanMessage(content=user_content)]

    response = llm.invoke(messages)
    return {"analysis_plan": response.content.strip()}
