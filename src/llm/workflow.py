# wokeflow.py
from __future__ import annotations

import os
from typing import Iterable, List, Optional

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore

from ..models import SummaryResult, SummaryStyle, TranscriptSegment, VideoMetadata
from .prompts import build_prompt



# Collapse transcript segments into one continuous text block.
def _join_transcript(segments: Iterable[TranscriptSegment]) -> str:
    return " ".join(seg.text.strip() for seg in segments if seg.text.strip())

def _build_fallback_summary(
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


async def run_summarisation_workflow(
    metadata: VideoMetadata,
    transcript_segments: Optional[List[TranscriptSegment]],
    style: SummaryStyle,
    language: str = "en",
    max_tokens: int = 1200,
) -> SummaryResult:
    """
    Orchestrates the full summarisation pipeline.

    1. Joins transcript segments into a single text block.
    2. Builds a prompt using metadata, transcript, style, and language.
    3. Uses OpenAI (if available) to generate a Markdown summary.
    4. Falls back to a deterministic Markdown summary if no LLM is available.

    Returns:
        SummaryResult: Contains the final Markdown summary.
    """
    transcript_text = _join_transcript(transcript_segments or [])



    # --- LLM path ---
    # If OpenAI is installed *and* an API key is present, use the real LLM.
    if OpenAI is not None and os.getenv("OPENAI_API_KEY"):
        client = OpenAI()
        prompt = build_prompt(metadata, transcript_text, style, language)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an assistant that produces clean, human-readable "
                        "Markdown summaries of YouTube videos. Do not return JSON. "
                        "Do not use code fences."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        content = response.choices[0].message.content or ""

        return SummaryResult(
            video_id=metadata.video_id,
            summary=content,     # full Markdown
         )
    
    # --- Fallback path ---
    fallback_markdown = _build_fallback_summary(metadata, transcript_text)

    return SummaryResult(
        video_id=metadata.video_id,
        summary=fallback_markdown,
    )





     

