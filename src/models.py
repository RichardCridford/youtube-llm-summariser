from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, HttpUrl, Field


class JobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class TranscriptSegment(BaseModel):
    start_s: float = Field(..., description="Start time in seconds")
    end_s: float = Field(..., description="End time in seconds")
    text: str


class VideoMetadata(BaseModel):
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

