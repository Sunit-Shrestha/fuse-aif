"""
Tools the assistant can call. Functions are plain, type-hinted, docstring-
documented Python callables -- the google-genai SDK's automatic function
calling introspects them directly to build the tool schema and to invoke
them, so no manual JSON schema authoring is needed.
"""
import re

from . import config
from .rag import RagIndex


def make_tools(rag_index: RagIndex, sources_used: list[str] | None = None):
    def search_course_materials(query: str) -> str:
        """Search the Fusemachines AI Fellowship course materials for relevant passages.

        Use this whenever the user asks anything about course content, assignments,
        or concepts covered in the fellowship -- do not answer from memory alone.

        Args:
            query: A short search query describing what to look for.
        """
        chunks = rag_index.search(query, top_k=config.TOP_K)
        if not chunks:
            return "No relevant course material found."
        if sources_used is not None:
            for c in chunks:
                if c.source not in sources_used:
                    sources_used.append(c.source)
        return "\n\n".join(f"[Source: {c.source}]\n{c.text}" for c in chunks)

    def list_available_weeks() -> str:
        """List which weeks of course material are available to search."""
        weeks = set()
        for chunk in rag_index.chunks:
            match = re.match(r"Week_(\d+)_", chunk.source)
            if match:
                weeks.add(int(match.group(1)))
        return "Available weeks: " + ", ".join(str(w) for w in sorted(weeks))

    return [search_course_materials, list_available_weeks]
