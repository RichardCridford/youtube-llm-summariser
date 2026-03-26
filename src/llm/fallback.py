# fallback.py
from typing import List
from ..models import VideoMetadata

def build_fallback_summary(
    metadata: VideoMetadata,
    transcript_text: str
) -> str:
    """
    Builds a deterministic Markdown summary used when no LLM is available.
    """

    notes: List[str] = []
    notes.append(f"Title: {metadata.title}")
    if metadata.channel_title:
        notes.append(f"Channel: {metadata.channel_title}")
    if metadata.description:
        notes.append(f"Description (truncated): {metadata.description[:300]}...")
    if transcript_text:
        notes.append(f"Transcript preview: {transcript_text[:500]}...")

    key_topics: List[str] = metadata.tags[:10] if metadata.tags else []

    return (
        "## 📌 Summary\n"
        f"Auto-generated summary for '{metadata.title}' (no LLM available).\n\n"
        "## 📝 Detailed Notes\n"
        + "\n".join(f"- {n}" for n in notes)
        + "\n\n## 🎯 Key Topics\n"
        + "\n".join(f"- {t}" for t in key_topics)
    )