import pandas as pd
import streamlit as st

from graph import graph
from state import default_state

st.set_page_config(layout="wide")

for key, default in [
    ("messages", []),
    ("df_csv", ""),
    ("df_schema", ""),
    ("chat_history", []),
    ("_loaded_filename", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default

NODE_LABELS = {
    "ingestion":  "Loading data",
    "analyst":    "Planning analysis",
    "codegen":    "Generating code",
    "executor":   "Executing in E2B sandbox",
    "critic":     "Reviewing output",
    "retry_router": "Retrying...",
    "summarizer": "Summarizing answer",
}


def _build_schema(df: pd.DataFrame) -> str:
    parts = [
        f"Shape: {df.shape[0]} rows × {df.shape[1]} columns",
        "",
        "Column dtypes:",
        df.dtypes.to_string(),
        "",
        "Null counts:",
        df.isnull().sum().to_string(),
        "",
        "First 5 rows:",
        df.head(5).to_string(index=False),
    ]
    return "\n".join(parts)


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    if uploaded_file is not None:
        if uploaded_file.name != st.session_state["_loaded_filename"]:
            df = pd.read_csv(uploaded_file)
            st.session_state.df_csv = df.to_csv(index=False)
            st.session_state.df_schema = _build_schema(df)
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.session_state["_loaded_filename"] = uploaded_file.name
            df_shape = (df.shape[0], df.shape[1])
        else:
            df_shape = None

        if df_shape:
            st.success(f"Loaded {df_shape[0]} rows × {df_shape[1]} columns")
        else:
            import io
            _df = pd.read_csv(io.StringIO(st.session_state.df_csv))
            st.success(f"Loaded {_df.shape[0]} rows × {_df.shape[1]} columns")

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.session_state.chat_history = []


# ── Main area ─────────────────────────────────────────────────────────────────
st.title("Data Analysis Agent")

for entry in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(entry["question"])
    with st.chat_message("assistant"):
        st.write(entry["answer"])
        if entry["chart_path"]:
            st.image(entry["chart_path"])

if not st.session_state.df_csv:
    st.info("Upload a CSV file in the sidebar to begin.")
    st.stop()

question = st.chat_input("Ask a question about your data...")

if question:
    with st.chat_message("user"):
        st.write(question)

    state = default_state(question)
    state["messages"] = st.session_state.messages
    state["df_csv"] = st.session_state.df_csv
    state["df_schema"] = st.session_state.df_schema

    current_state = dict(state)

    with st.status("Working...", expanded=True) as status:
        for event in graph.stream(state, stream_mode="updates"):
            node_name = next(iter(event))
            partial_update = event[node_name]
            if partial_update:
                current_state.update(partial_update)
            status.update(label=NODE_LABELS.get(node_name, node_name))
        status.update(label="Done", state="complete")

    answer = current_state.get("final_answer", "")
    chart_path = current_state.get("chart_path", "")
    messages = current_state.get("messages", [])

    with st.chat_message("assistant"):
        st.write(answer)
        if chart_path:
            st.image(chart_path)

    st.session_state.messages = messages
    st.session_state.chat_history.append({
        "question": question,
        "answer": answer,
        "chart_path": chart_path,
    })

if st.session_state.chat_history:
    report_parts = []
    for entry in st.session_state.chat_history:
        report_parts.append(f"## Q: {entry['question']}\n\n{entry['answer']}\n\n")
        if entry["chart_path"]:
            report_parts.append(f"*Chart saved to: {entry['chart_path']}*\n\n")
    report_md = "".join(report_parts)
    st.download_button(
        label="Download session report",
        data=report_md,
        file_name="analysis_report.md",
        mime="text/markdown",
    )
