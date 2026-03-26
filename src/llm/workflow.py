# wokeflow.py

from __future__ import annotations

import os
from typing import Iterable, List, Optional

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore

from ..models import SummaryResult, SummaryStyle, TranscriptSegment, VideoMetadata

#-----------------------------------------------------------------------------------
# 1. 	Takes metadata + transcript
# 2. 	Builds a prompt
# 3. 	Asks the LLM to summarise it
# 4. 	Returns a Summary result
#-----------------------------------------------------------------------------------


def _join_transcript(segments: Iterable[TranscriptSegment]) -> str:
    return " ".join(seg.text.strip() for seg in segments if seg.text.strip())


async def run_summarisation_workflow(
    metadata: VideoMetadata,
    transcript_segments: Optional[List[TranscriptSegment]],
    style: SummaryStyle,
    language: str = "en",
    max_tokens: int = 1200,
) -> SummaryResult:

    transcript_text = _join_transcript(transcript_segments or [])

    # --- LLM path ---
    if OpenAI is not None and os.getenv("OPENAI_API_KEY"):
        client = OpenAI()
        prompt = _build_prompt(metadata, transcript_text, style, language)
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
    notes: List[str] = []
    notes.append(f"Title: {metadata.title}")
    if metadata.channel_title:
        notes.append(f"Channel: {metadata.channel_title}")
    if metadata.description:
        notes.append(f"Description (truncated): {metadata.description[:300]}...")
    if transcript_text:
        notes.append(f"Transcript preview: {transcript_text[:500]}...")

    key_topics: List[str] = metadata.tags[:10] if metadata.tags else []

    fallback_markdown = (
        "## 📌 Summary\n"
        f"Auto-generated summary for '{metadata.title}' (no LLM available).\n\n"
        "## 📝 Detailed Notes\n"
        + "\n".join(f"- {n}" for n in notes)
        + "\n\n## 🎯 Key Topics\n"
        + "\n".join(f"- {t}" for t in key_topics)
    )

    return SummaryResult(
        video_id=metadata.video_id,
        summary=fallback_markdown,
   
    )


def _build_prompt(
    metadata: VideoMetadata,
    transcript_text: str,
    style: SummaryStyle,
    language: str,
) -> str:

    style_description = {
        SummaryStyle.meeting_notes: "meeting-style notes with clear bullet points and action items",
        SummaryStyle.study_notes: "study notes emphasising key concepts and definitions",
        SummaryStyle.tweet_thread: "a concise tweet-thread style outline",
        SummaryStyle.generic: "a clear, general-purpose summary and bullet-point notes",
    }[style]

    return f"""
Summarise the following YouTube video in {language}.

Title: {metadata.title}
Description: {metadata.description}
Channel: {metadata.channel_title}
Tags: {', '.join(metadata.tags or [])}

Transcript:
{transcript_text}

Return the final answer as clean, human-readable Markdown using the following structure:

## 📌 Summary
A short paragraph summarising the video.

## 📝 Detailed Notes
Bullet-pointed notes capturing the most important details.

## 🎯 Key Topics
A list of the main themes or concepts.

## ✔️ Action Items
Only include this section if relevant.

## 🏷️ Content Type
A simple label describing the type of video.

Do not return JSON. 
Do not wrap the output in code fences. 
Do not include backticks. 
The output must be pure Markdown.
"""

     

