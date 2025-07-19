from rich.console import Console
from rich.markdown import Markdown


def extract_text_and_sources(response):
    text = response.candidates[0].content.parts[0].text
    candidate = response.candidates[0]

    sources_text = ""

    # Display grounding metadata if available
    if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
        if candidate.grounding_metadata.grounding_chunks:
            sources_list = []
            for i, chunk in enumerate(candidate.grounding_metadata.grounding_chunks, 1):
                if hasattr(chunk, "web") and chunk.web:
                    title = getattr(chunk.web, "title", "No title") or "No title"
                    uri = getattr(chunk.web, "uri", "No URI") or "No URI"
                    sources_list.append(f"{i}. {title}\n   {uri}")

            sources_text = "\n".join(sources_list)

    return text, sources_text


def cited_markdown(response) -> tuple[str, str]:
    """
    Integrates grounding citations into generated text and appends a reference list.

    Args:
        response: The response object from the model containing generated text and grounding metadata.

    Returns:
        A single markdown string with inline citations and a formatted
        reference list at the end.
    """
    candidate = response.candidates[0]
    generated_text = candidate.content.parts[0].text
    grounding_chunks = candidate.grounding_metadata.grounding_chunks
    grounding_supports = candidate.grounding_metadata.grounding_supports

    if not grounding_supports:
        return generated_text

    # Step 1 & 2: Create a list of insertions and sort them in reverse order of index.
    # This is crucial to avoid shifting indices as we modify the text.
    insertions = []
    for support in grounding_supports:
        # Create the citation marker string, e.g., "[1][2][3]"
        # We add 1 to the chunk index to make it 1-based for the reader.
        citation_marker = "".join(
            [f"[[{idx + 1}]]" for idx in sorted(support.grounding_chunk_indices)]
        )

        # The segment end_index is where we'll insert the citation.
        insert_at_index = support.segment.end_index
        insertions.append((insert_at_index, citation_marker))

    # Sort by index in descending order.
    insertions.sort(key=lambda x: x[0], reverse=True)

    # Step 3: Inject the citations into the text from the end to the beginning.
    modified_text = generated_text
    for index, marker in insertions:
        # Make sure the index is within the bounds of the current text length
        if index is not None and 0 <= index <= len(modified_text):
            modified_text = modified_text[:index] + marker + modified_text[index:]

    # Step 4: Build the reference list in Markdown format.
    reference_list = []
    sources_list = []
    for i, chunk in enumerate(grounding_chunks):
        try:
            # Assumes the structure you provided with a 'web' key
            title = chunk.web.title
            uri = chunk.web.uri
            # Format: [1]: [Title of the page](https://example.com)
            sources_list.append(f"[[{i + 1}]] - [{title}]({uri})")
            reference_list.append(f"[{i + 1}]: {uri}")
        except (KeyError, TypeError):
            # Handle cases where the chunk format might be different
            reference_list.append(f"[{i + 1}]: Source not available")

    reference_string = "\n".join(reference_list)
    sources_text = "\n".join(sources_list)

    # Step 5: Combine the modified text and the reference list.
    final_output = f"{modified_text}\n\n{reference_string}"

    return final_output, sources_text


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
