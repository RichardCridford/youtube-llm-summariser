from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, HttpUrl, Field


class JobStatus(str, Enum):
    """
    Represents the lifecycle state of a summarisation job.

    The server assigns one of these states to every job created by the client.
    They describe where the job is in the processing pipeline:

    - queued: The job has been accepted but not yet started.
    - processing: The worker is currently fetching metadata, transcript, or running the LLM.
    - completed: The summarisation workflow finished successfully and a SummaryResult is available.
    - failed: An unrecoverable error occurred and the job cannot be completed.
    """
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class TranscriptSegment(BaseModel):
    """
     Represents a single fragment of a YouTube transcript.

    Each segment corresponds to a continuous spoken passage with a defined
    start and end time. The summarisation workflow receives a list of these
    segments from the YouTube client and later collapses them into a single
    text block for prompt construction.

    Fields:
    - start_s: Timestamp (in seconds) where the spoken segment begins.
    - end_s: Timestamp (in seconds) where the spoken segment ends.
    - text: The transcribed speech for this time interval. 
    """
    start_s: float = Field(..., description="Start time in seconds")
    end_s: float = Field(..., description="End time in seconds")
    text: str


class VideoMetadata(BaseModel):
    """
    Describes the core information about a YouTube video required for
    summarisation.

    This model is populated by the YouTube client before the workflow runs.
    The metadata is used to enrich the LLM prompt, provide context for the
    fallback summary, and help the system identify the video being processed.

    Fields:
    - video_id: Unique identifier of the YouTube video.
    - title: The video's title as provided by YouTube.
    - description: Full video description text (may be long or empty).
    - channel_title: Name of the channel that published the video.
    - tags: List of tags assigned to the video, used for topic extraction.
    - published_at: ISO timestamp of when the video was published.
    - duration: Video duration in ISO 8601 format (e.g., PT12M30S).
    - language: Language code if known (e.g., "en"), used for prompt selection.  
    """
    video_id: str
    title: str
    description: str = ""
    channel_title: Optional[str] = None
    tags: List[str] = []
    published_at: Optional[str] = None
    duration: Optional[str] = None
    language: Optional[str] = None


class SummaryStyle(str, Enum):
    meeting_notes = "meeting_notes"
    study_notes = "study_notes"
    tweet_thread = "tweet_thread"
    generic = "generic"


class SummaryResult(BaseModel):
    video_id: str
    summary: str # full Markdown Output
    
class CreateSummaryRequest(BaseModel):
    url: Optional[HttpUrl] = None
    video_id: Optional[str] = None
    style: SummaryStyle = SummaryStyle.generic
    language: str = "en"
    max_tokens: int = 1200


class Job(BaseModel):
    id: str
    status: JobStatus
    video_id: Optional [str] = None
    error: Optional[str] = None
    result: Optional[SummaryResult] = None

