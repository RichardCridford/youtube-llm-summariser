# Youtube LLM SUMMARISER

## About this project 
This is a YouTube Summariser API built in Python using FastAPI. You give it a YouTube URL, and it fetches the video’s metadata and transcript, runs a summarisation workflow, and returns a clean, structured summary.
The system supports both an LLM‑powered summariser (GPT‑4o‑mini) and a deterministic fallback mode for testing without an API key.


## Why I built it
I created this project as a hands‑on way to practice working with REST APIs, background job queues, and multi‑step workflows.
I also used it as a chance to experiment with Cursor — letting it generate scaffolding while I focused on the actual logic, architecture, and debugging.

This is not a “finished product.”
It’s a learning project that keeps evolving as I refine the code, improve the workflow, and make the API more user‑friendly.

## What it does
- Accepts a YouTube URL
- Fetches metadata + transcript
- Creates a background job
- Runs a summarisation workflow
- Returns the final summary when the job completes
- Uses an LLM if available, or a fallback summary if not
- The goal is to keep the system simple, transparent, and easy to extend as I continue improving it.