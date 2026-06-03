from graph import graph
from state import default_state
from langchain_core.messages import HumanMessage, AIMessage


def run_agent(question: str, messages: list) -> dict:
    state = default_state(question)
    state["messages"] = messages
    try:
        result = graph.invoke(state)
    except Exception as e:
        print(f"\nAgent: Sorry, something went wrong — {e}\n")
        return {"answer": "", "chart_path": "", "messages": messages}
    return {
        "answer": result["final_answer"],
        "chart_path": result["chart_path"],
        "messages": result["messages"],
    }


if __name__ == "__main__":
    messages = []
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            continue
        if question.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        result = run_agent(question, messages)
        messages = result["messages"]

        print(f"\nAgent: {result['answer']}")
        if result["chart_path"]:
            print(f"Chart saved: {result['chart_path']}")
        print()
