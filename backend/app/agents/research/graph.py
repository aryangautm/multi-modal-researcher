from app.core.config import Configuration
from langgraph.graph import END, START, StateGraph

from .nodes import (
    analyze_video_node,
    create_report_node,
    research_node,
    should_analyze_video,
)
from .state import ResearchState, ResearchStateInput, ResearchStateOutput


def create_research_graph() -> StateGraph:
    """Create and return the research workflow graph"""

    # Create the graph with configuration schema
    graph = StateGraph(
        ResearchState,
        input=ResearchStateInput,
        output=ResearchStateOutput,
        config_schema=Configuration,
    )

    # Add nodes
    graph.add_node("research", research_node)
    graph.add_node("analyze_video", analyze_video_node)
    graph.add_node("create_report", create_report_node)

    # Add edges
    graph.add_edge(START, "research")
    graph.add_conditional_edges(
        "research",
        should_analyze_video,
        {"analyze_video": "analyze_video", "create_report": "create_report"},
    )
    graph.add_edge("analyze_video", "create_report")
    graph.add_edge("create_report", END)

    return graph


def create_compiled_graph(checkpointer=None):
    """Create and compile the research graph"""
    graph = create_research_graph()
    return graph.compile(checkpointer=checkpointer)
