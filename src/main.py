from __future__ import annotations

import os
import re
import uuid
from typing import Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .llm.workflow import run_summarisation_workflow
from .models import (
    CreateSummaryRequest,
    Job,
    JobStatus,
    SummaryResult,
    TranscriptSegment,
    VideoMetadata,
)
from .youtube_client.api import YouTubeClient

from dotenv import load_dotenv
load_dotenv()


try:
    from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    YouTubeTranscriptApi = None  # type: ignore

app = FastAPI(title="YouTube LLM Summariser", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_jobs: Dict[str, Job] = {}


def _extract_video_id(url_or_id: str) -> str:
    """
    Extracts a YouTube video id from a URL or returns the input if it already
    looks like an id.
    """
    # If it looks like a bare video id (11 chars, no spaces), just return it.
    if re.fullmatch(r"[a-zA-Z0-9_-]{11}", url_or_id):
        return url_or_id

    patterns = [
        r"v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    raise ValueError("Could not extract video id from input.")


def _normalise_metadata(raw: dict, video_id: str) -> VideoMetadata:
    items = raw.get("items", [])
    if not items:
        raise ValueError("No metadata found for video.")

    item = items[0]
    snippet = item.get("snippet", {})
    content_details = item.get("contentDetails", {})

    return VideoMetadata(
        video_id=video_id,
        title=snippet.get("title", ""),
        description=snippet.get("description", "") or "",
        channel_title=snippet.get("channelTitle"),
        tags=snippet.get("tags", []),
        published_at=snippet.get("publishedAt"),
        duration=content_details.get("duration"),
        language=snippet.get("defaultAudioLanguage") or snippet.get("defaultLanguage"),
    )


def _fetch_transcript_segments(video_id: str) -> List[TranscriptSegment]:
    if YouTubeTranscriptApi is None:
        return []
    try:
        raw_segments = YouTubeTranscriptApi.get_transcript(video_id)
    except Exception:
        return []

    segments: List[TranscriptSegment] = []
    for seg in raw_segments:
        start = float(seg.get("start", 0.0))
        duration = float(seg.get("duration", 0.0))
        text = seg.get("text", "")
        segments.append(
            TranscriptSegment(
                start_s=start,
                end_s=start + duration,
                text=text,
            )
        )
    return segments


async def _process_job(job_id: str, req: CreateSummaryRequest) -> None:
    job = _jobs[job_id]
    _jobs[job_id] = job.copy(update={"status": JobStatus.processing})

    try:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            raise RuntimeError("YOUTUBE_API_KEY is not set.")

        video_id_input: Optional[str] = None
        if req.video_id:
            video_id_input = req.video_id
        elif req.url:
            video_id_input = str(req.url)
        else:
            raise ValueError("Either url or video_id must be provided.")

        video_id = _extract_video_id(video_id_input)

        yt_client = YouTubeClient(api_key=api_key)
        raw_metadata = await yt_client.get_video_metadata(video_id)
        metadata = _normalise_metadata(raw_metadata, video_id)

        transcript_segments = _fetch_transcript_segments(video_id)

        summary: SummaryResult = await run_summarisation_workflow(
            metadata=metadata,
            transcript_segments=transcript_segments,
            style=req.style,
            language=req.language,
            max_tokens=req.max_tokens,
        )

        _jobs[job_id] = Job(
            id=job_id,
            status=JobStatus.completed,
            video_id=video_id,
            error=None,
            result=summary,
        )
    except Exception as exc:  # pragma: no cover - simple error path
        _jobs[job_id] = Job(
            id=job_id,
            status=JobStatus.failed,
            video_id=job.video_id,
            error=str(exc),
            result=None,
        )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/summaries", response_model=Job)
async def create_summary_job(
    req: CreateSummaryRequest, background_tasks: BackgroundTasks
) -> Job:
    if not req.url and not req.video_id:
        raise HTTPException(
            status_code=400, detail="Either 'url' or 'video_id' must be provided."
        )

    raw_input = req.video_id or str(req.url)
    try:
        video_id = _extract_video_id(raw_input)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    job_id = str(uuid.uuid4())
    job = Job(id=job_id, status=JobStatus.queued, video_id=video_id)
    _jobs[job_id] = job

    background_tasks.add_task(_process_job, job_id, req)

    return job


@app.get("/v1/summaries/{job_id}", response_model=Job)
async def get_summary_job(job_id: str) -> Job:
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job

