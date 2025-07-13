import uuid

from app.agents.research.graph import create_compiled_graph


def test_research_graph_invocation():
    """
    Tests that the research graph can be created and invoked successfully.
    """
    research_graph = create_compiled_graph()
    test_thread_id = str(uuid.uuid4())
    test_input = {
        "topic": "AI in healthcare",
        "video_url": "https://www.youtube.com/watch?v=uvqDTbusdUU",
    }

    result = research_graph.invoke(
        test_input,
        config={"thread_id": test_thread_id},
    )

    print(result)
    assert result is not None
    assert "summary" in result
    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 50
