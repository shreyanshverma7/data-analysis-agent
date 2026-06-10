import io
import time

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

NODE_STATUS = {
    "ingestion":     "Loading data...",
    "fan_out":       "Dispatching specialist agents...",
    "stats_subgraph": "Computing statistics...",
    "viz_subgraph":  "Generating visualization...",
    "narrative":     "Writing interpretation...",
    "synthesizer":   "Synthesizing answer...",
    "summarizer":    "Finalising...",
}


def _render_specialist_expanders(specialist_results: list) -> None:
    stats_entry = next((e for e in specialist_results if e.get("type") == "stats"), None)
    viz_entry = next((e for e in specialist_results if e.get("type") == "viz"), None)
    narrative_entry = next((e for e in specialist_results if e.get("type") == "narrative"), None)

    with st.expander("Stats output"):
        if stats_entry and stats_entry.get("result"):
            st.code(stats_entry["result"], language="text")
        elif stats_entry and stats_entry.get("error"):
            st.error(f"Stats failed: {stats_entry['error']}")
        else:
            st.write("No stats output.")

    if viz_entry is not None:
        with st.expander("Chart"):
            if viz_entry.get("chart_path"):
                st.image(viz_entry["chart_path"])
            else:
                st.error(f"Visualization failed: {viz_entry.get('error', 'unknown error')}")

    with st.expander("Narrative"):
        if narrative_entry and narrative_entry.get("result"):
            st.write(narrative_entry["result"])
        else:
            st.write("No narrative available.")


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
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv", "xlsx", "xls", "json"])

    if uploaded_file is not None:
        if uploaded_file.name != st.session_state["_loaded_filename"]:
            _ext = uploaded_file.name.split(".")[-1].lower()
            if _ext in ("xlsx", "xls"):
                df = pd.read_excel(uploaded_file)
            elif _ext == "json":
                df = pd.read_json(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            st.session_state.df_csv = df.to_csv(index=False)
            st.session_state.df_schema = _build_schema(df)
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.session_state["_loaded_filename"] = uploaded_file.name

        _meta_df = pd.read_csv(io.StringIO(st.session_state.df_csv))
        _ext = st.session_state["_loaded_filename"].split(".")[-1].upper()
        _numeric_cols = _meta_df.select_dtypes(include="number").shape[1]
        st.success("Loaded successfully")
        col1, col2 = st.columns(2)
        col1.metric("Rows", _meta_df.shape[0])
        col2.metric("Columns", _meta_df.shape[1])
        col1.metric("Numeric cols", _numeric_cols)
        col2.metric("Format", _ext)

        with st.expander("Dataset preview", expanded=False):
            st.dataframe(_meta_df.head(10))
            st.dataframe(_meta_df.describe())

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
        _render_specialist_expanders(entry.get("specialist_results", []))

if not st.session_state.df_csv:
    st.markdown("""
<div style="padding: 2rem; border-radius: 0.5rem; background: #f8f9fa; margin-top: 2rem;">
<h3>Data Analysis Agent</h3>
<ul>
<li>Upload any <strong>CSV, Excel, or JSON</strong> file in the sidebar</li>
<li>Parallel <strong>stats + visualization agents</strong> run simultaneously</li>
<li>Eval-tested: <strong>1.00 numeric accuracy</strong> on Titanic · <strong>0.90</strong> on Wine Quality</li>
</ul>
</div>
""", unsafe_allow_html=True)
    st.stop()

if not st.session_state.chat_history:
    _sq_df = pd.read_csv(io.StringIO(st.session_state.df_csv))
    _numeric_cols = _sq_df.select_dtypes(include="number").columns.tolist()
    _cat_cols = _sq_df.select_dtypes(include=["object", "bool"]).columns.tolist()

    _suggestions = []
    if _numeric_cols:
        _suggestions.append(f"What is the distribution of {_numeric_cols[0]}?")
    if _cat_cols:
        _suggestions.append(f"What is the breakdown by {_cat_cols[0]}?")
    if len(_numeric_cols) >= 2:
        _suggestions.append(f"What is the correlation between {_numeric_cols[0]} and {_numeric_cols[1]}?")

    if _suggestions:
        st.markdown("**Suggested questions:**")
        for _sq in _suggestions:
            if st.button(_sq, key=f"sq_{_sq}"):
                st.session_state["_pending_question"] = _sq
                st.rerun()

question = st.chat_input("Ask a question about your data...")

if "question" not in locals() or question is None:
    question = st.session_state.pop("_pending_question", None)

if question:
    with st.chat_message("user"):
        st.write(question)

    state = default_state(question)
    state["messages"] = st.session_state.messages
    state["df_csv"] = st.session_state.df_csv
    state["df_schema"] = st.session_state.df_schema

    current_state = dict(state)
    current_state.setdefault("specialist_results", [])

    numeric_markers = ("int64", "float64", "datetime")
    viz_will_run = any(m in st.session_state.df_schema for m in numeric_markers)

    if viz_will_run:
        col_stats, col_viz = st.columns(2)
        stats_ph = col_stats.empty()
        viz_ph = col_viz.empty()
        viz_ph.info("Viz agent — waiting")
    else:
        stats_ph = st.empty()
        viz_ph = None
    stats_ph.info("Stats agent — waiting")
    narrative_ph = st.empty()
    status_ph = st.empty()

    _start_time = time.time()
    for event in graph.stream(state, stream_mode="updates"):
        node_name = next(iter(event))
        partial_update = event[node_name]
        if partial_update:
            if "specialist_results" in partial_update:
                current_state["specialist_results"] = (
                    current_state["specialist_results"] + partial_update["specialist_results"]
                )
                rest = {k: v for k, v in partial_update.items() if k != "specialist_results"}
                current_state.update(rest)
            else:
                current_state.update(partial_update)

        if "stats_subgraph" in node_name:
            stats_ph.info("Stats agent — running...")
        elif "viz_subgraph" in node_name and viz_ph is not None:
            viz_ph.info("Viz agent — running...")
        elif node_name == "narrative":
            narrative_ph.info("Narrative — writing interpretation...")
        elif node_name in ("synthesizer", "summarizer"):
            narrative_ph.info("Synthesizer — building answer...")

        status_ph.info(NODE_STATUS.get(node_name, node_name))

    specialist_results = current_state.get("specialist_results", [])
    stats_entry = next((e for e in specialist_results if e.get("type") == "stats"), None)
    viz_entry = next((e for e in specialist_results if e.get("type") == "viz"), None)

    if stats_entry and stats_entry.get("result"):
        stats_ph.success("Stats agent — done ✓")
    else:
        stats_ph.error("Stats agent — failed ✗")

    if viz_ph is not None:
        if viz_entry and viz_entry.get("chart_path"):
            viz_ph.success("Viz agent — done ✓")
        elif viz_entry:
            viz_ph.error("Viz agent — failed ✗")
        # viz_ph is None means viz was intentionally skipped — no indicator needed

    narrative_ph.success("Narrative — done ✓")
    status_ph.success("Complete")
    _elapsed = time.time() - _start_time

    answer = current_state.get("final_answer", "")
    chart_path = current_state.get("chart_path", "")
    messages = current_state.get("messages", [])

    with st.chat_message("assistant"):
        st.write(answer)
        if chart_path:
            st.image(chart_path)
        _render_specialist_expanders(specialist_results)
        _mcol1, _mcol2 = st.columns(2)
        _mcol1.metric("Elapsed", f"{_elapsed:.1f}s")
        _mcol2.metric("~Tokens", len(answer) // 4)

    st.session_state.messages = messages
    st.session_state.chat_history.append({
        "question": question,
        "answer": answer,
        "chart_path": chart_path,
        "specialist_results": specialist_results,
    })

if st.session_state.chat_history:
    report_parts = []
    for entry in st.session_state.chat_history:
        report_parts.append(f"## Question\n{entry['question']}\n\n")
        report_parts.append(f"## Answer\n{entry['answer']}\n\n")

        sr = entry.get("specialist_results")
        if sr:
            stats_e = next((e for e in sr if e.get("type") == "stats"), None)
            viz_e = next((e for e in sr if e.get("type") == "viz"), None)
            narrative_e = next((e for e in sr if e.get("type") == "narrative"), None)

            stats_text = (stats_e["result"] if stats_e and stats_e.get("result") else "Unavailable")
            viz_text = (
                f"Chart saved at: {viz_e['chart_path']}"
                if viz_e and viz_e.get("chart_path")
                else "Unavailable"
            )
            narrative_text = (
                narrative_e["result"] if narrative_e and narrative_e.get("result") else "Unavailable"
            )

            report_parts.append(f"### Stats Output\n{stats_text}\n\n")
            report_parts.append(f"### Visualization\n{viz_text}\n\n")
            report_parts.append(f"### Narrative\n{narrative_text}\n\n")

        report_parts.append("---\n\n")
    report_md = "".join(report_parts)
    st.download_button(
        label="Download session report",
        data=report_md,
        file_name="analysis_report.md",
        mime="text/markdown",
    )
