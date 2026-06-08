from langgraph.graph import StateGraph, START, END

from state import AgentState
from nodes.ingestion import ingestion_node
from nodes.fan_out import fan_out_node
from nodes.narrative import narrative_node
from nodes.synthesizer import synthesizer_node
from nodes.summarizer import summarizer_node
from nodes.specialists.stats import stats_subgraph
from nodes.specialists.viz import viz_subgraph

builder = StateGraph(AgentState)

builder.add_node("ingestion", ingestion_node)
builder.add_node("stats_subgraph", stats_subgraph)
builder.add_node("viz_subgraph", viz_subgraph)
builder.add_node("narrative", narrative_node)
builder.add_node("synthesizer", synthesizer_node)
builder.add_node("summarizer", summarizer_node)

builder.add_edge(START, "ingestion")
builder.add_conditional_edges("ingestion", fan_out_node, ["stats_subgraph", "viz_subgraph"])
builder.add_edge("stats_subgraph", "narrative")
builder.add_edge("viz_subgraph", "narrative")
builder.add_edge("narrative", "synthesizer")
builder.add_edge("synthesizer", "summarizer")
builder.add_edge("summarizer", END)

graph = builder.compile()
