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
    """
    Defines the supported output formats for video summaries.
    The selected style is passed into the summarisation workflow and is
    intended to influence prompt construction and output formatting.

    Note:
    The styles are currently defined and exposed through the API
    but are not yet implemented in the prompt generation logic.
    """

    meeting_notes = "meeting_notes"
    study_notes = "study_notes"
    tweet_thread = "tweet_thread"
    generic = "generic"


class SummaryResult(BaseModel):
   """
    Represents the final output produced by the summarisation workflow.

    A SummaryResult is generated after the workflow has processed the
    video's metadata and transcript. It contains the completed summary
    returned either by the LLM or by the deterministic fallback path.

    Fields:
    - video_id: Unique identifier of the summarised YouTube video.
    - summary: The final human-readable Markdown summary.
    """ 
   video_id: str
   summary: str 
    
class CreateSummaryRequest(BaseModel):
    """
    Represents a client's request to generate a video summary.

    This model defines the input accepted by the POST /v1/summaries
    endpoint. A client may provide either a YouTube URL or a video ID,
    along with optional settings that control how the summary is
    generated.

    Fields:
    - url: Full YouTube URL for the video to summarise.
    - video_id: YouTube video identifier. Can be used instead of a URL.
    - style: Determines the structure and tone of the generated summary.
    - language: Target language for the summary output.
    - max_tokens: Maximum number of tokens the LLM may use when generating
    the response.
    """
    url: Optional[HttpUrl] = None
    video_id: Optional[str] = None
    style: SummaryStyle = SummaryStyle.generic
    language: str = "en"
    max_tokens: int = 1200


class Job(BaseModel):
    """
    Represents a summarisation job tracked by the server.

    Jobs are created when a client submits a summary request and are
    updated as they move through the processing pipeline. Clients can
    poll a job to check its current status, retrieve a completed summary,
    or inspect any errors that occurred during processing.

    Fields:
    - id: Unique identifier for the job.
    - status: Current state of the job lifecycle.
    - video_id: Identifier of the YouTube video being processed.
    - error: Error message if the job fails.
    - result: Final summary result when processing completes successfully.
    """
    id: str
    status: JobStatus
    video_id: Optional [str] = None
    error: Optional[str] = None
    result: Optional[SummaryResult] = None

