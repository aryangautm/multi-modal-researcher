from core.config import Configuration
from core.database import pg_checkpointer
from langgraph.graph import END, START, StateGraph
from schemas.research import ResearchState, ResearchStateInput, ResearchStateOutput

from .nodes import (
    analyze_video_node,
    create_report_node,
    search_research_node,
    should_analyze_video,
)


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
    graph.add_node("search_research", search_research_node)
    graph.add_node("analyze_video", analyze_video_node)
    graph.add_node("create_report", create_report_node)

    # Add edges
    graph.add_edge(START, "search_research")
    graph.add_conditional_edges(
        "search_research",
        should_analyze_video,
        {"analyze_video": "analyze_video", "create_report": "create_report"},
    )
    graph.add_edge("analyze_video", "create_report")
    graph.add_edge("create_report", END)

    return graph


def create_compiled_graph():
    """Create and compile the research graph"""
    graph = create_research_graph()
    return graph.compile(checkpointer=pg_checkpointer)


research_graph = create_compiled_graph()
