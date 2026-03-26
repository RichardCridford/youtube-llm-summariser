# prompts.py
import textwrap
from ..models import SummaryResult, SummaryStyle, TranscriptSegment, VideoMetadata

def build_prompt(
    metadata: VideoMetadata,
    transcript_text: str,
    style: SummaryStyle,
    language: str,
) -> str:

    return textwrap.dedent(f"""
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
""")