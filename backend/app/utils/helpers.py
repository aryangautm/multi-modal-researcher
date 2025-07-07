from rich.console import Console
from rich.markdown import Markdown


def display_gemini_response(response):
    """Extract text from Gemini response and display as markdown with references"""
    console = Console()

    # Extract main content
    text = response.candidates[0].content.parts[0].text
    md = Markdown(text)
    console.print(md)

    # Get candidate for grounding metadata
    candidate = response.candidates[0]

    # Build sources text block
    sources_text = ""

    # Display grounding metadata if available
    if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
        console.print("\n" + "=" * 50)
        console.print("[bold blue]References & Sources[/bold blue]")
        console.print("=" * 50)

        # Display and collect source URLs
        if candidate.grounding_metadata.grounding_chunks:
            console.print(
                f"\n[bold]Sources ({len(candidate.grounding_metadata.grounding_chunks)}):[/bold]"
            )
            sources_list = []
            for i, chunk in enumerate(candidate.grounding_metadata.grounding_chunks, 1):
                if hasattr(chunk, "web") and chunk.web:
                    title = getattr(chunk.web, "title", "No title") or "No title"
                    uri = getattr(chunk.web, "uri", "No URI") or "No URI"
                    console.print(f"{i}. {title}")
                    console.print(f"   [dim]{uri}[/dim]")
                    sources_list.append(f"{i}. {title}\n   {uri}")

            sources_text = "\n".join(sources_list)

        # Display grounding supports (which text is backed by which sources)
        if candidate.grounding_metadata.grounding_supports:
            console.print(f"\n[bold]Text segments with source backing:[/bold]")
            for support in candidate.grounding_metadata.grounding_supports[
                :5
            ]:  # Show first 5
                if hasattr(support, "segment") and support.segment:
                    snippet = (
                        support.segment.text[:100] + "..."
                        if len(support.segment.text) > 100
                        else support.segment.text
                    )
                    source_nums = [str(i + 1) for i in support.grounding_chunk_indices]
                    console.print(
                        f"• \"{snippet}\" [dim](sources: {', '.join(source_nums)})[/dim]"
                    )

    return text, sources_text
