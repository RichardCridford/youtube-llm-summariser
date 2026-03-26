#transcript.py
from typing import Iterable
from ..models import TranscriptSegment

# Collapse transcript segments into one continuous text block.
def join_transcript(segments: Iterable[TranscriptSegment]) -> str:
    """
    Collapses transcript segments into one continuous text block.
    Removes empty or whitespace-only segments.
    """
    return " ".join(
        seg.text.strip()
        for seg in segments
        if seg.text and seg.text.strip()
    )