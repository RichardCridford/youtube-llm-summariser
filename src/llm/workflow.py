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
from .fallback import build_fallback_summary
from ..processing.transcript import join_transcript


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
    transcript_text = join_transcript(transcript_segments or [])



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
    fallback_markdown = build_fallback_summary(metadata, transcript_text)

    return SummaryResult(
        video_id=metadata.video_id,
        summary=fallback_markdown,
    )





     

