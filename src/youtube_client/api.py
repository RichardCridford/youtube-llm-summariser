import httpx
from typing import Any, Dict, Optional


class YouTubeClient:
    """
    Lightweight wrapper around the YouTube Data API (v3).
    Handles:
    - Video metadata
    - Comments (optional)
    - Transcripts (optional, via youtube-transcript-api)
    """

    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def _get(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Internal helper for GET requests."""
        params["key"] = self.api_key

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()

    async def get_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """
        Fetches snippet, contentDetails, and statistics for a video.
        """
        params = {
            "id": video_id,
            "part": "snippet,contentDetails,statistics",
        }
        return await self._get("videos", params)

    async def get_comments(self, video_id: str, max_results: int = 50) -> Dict[str, Any]:
        """
        Fetches top-level comments for a video.
        """
        params = {
            "videoId": video_id,
            "part": "snippet",
            "maxResults": max_results,
            "textFormat": "plainText",
        }
        return await self._get("commentThreads", params)

