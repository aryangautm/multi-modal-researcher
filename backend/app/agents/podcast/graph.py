from core.config import Configuration
from langgraph.graph import END, START, StateGraph
from schemas.podcast.agent_state import (
    PodcastState,
    PodcastStateInput,
    PodcastStateOutput,
)

from .nodes import create_podcast_node, generate_podcast_script


def create_podcast_graph() -> StateGraph:
    """Create and return the podcast workflow graph"""

    # Create the graph with configuration schema
    graph = StateGraph(
        PodcastState,
        input=PodcastStateInput,
        output=PodcastStateOutput,
        config_schema=Configuration,
    )

    # Add nodes
    graph.add_node("generate_podcast_script", generate_podcast_script)
    graph.add_node("create_podcast_node", create_podcast_node)

    # Add edges
    graph.add_edge(START, "generate_podcast_script")
    graph.add_edge("generate_podcast_script", "create_podcast")
    graph.add_edge("create_podcast", END)

    return graph


def create_compiled_graph():
    """Create and compile the podcast graph"""
    graph = create_podcast_graph()
    return graph.compile()
