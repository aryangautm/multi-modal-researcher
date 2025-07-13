from core.config import Configuration
from langgraph.graph import END, START, StateGraph

from .nodes import create_podcast_node, generate_podcast_script
from .state import PodcastState, PodcastStateInput, PodcastStateOutput


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
    graph.add_edge("generate_podcast_script", "create_podcast_node")
    graph.add_edge("create_podcast_node", END)

    return graph


def create_compiled_graph(checkpointer=None):
    """Create and compile the podcast graph"""
    graph = create_podcast_graph()
    return graph.compile(checkpointer=checkpointer)
