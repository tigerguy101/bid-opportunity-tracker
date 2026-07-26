"""
Summarizes and scores bid opportunities using Groq's free-tier LLM API.

Get a free key at https://console.groq.com/keys (no credit card required for the free tier).
Swap GROQ_MODEL / the API call below for Gemini, OpenAI, or Anthropic if you'd rather use
a different provider, the rest of the pipeline doesn't care which one you use.
"""

import os
import json
import time
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an assistant that screens government contract opportunities for a small \
IT and AI consulting business. For each opportunity you are given, respond with a compact JSON \
object with exactly these fields:
  "summary": one or two plain-English sentences describing what the contract is for
  "relevance": one of "High", "Medium", or "Low", based on fit for an IT support, \
Microsoft 365, cloud, or AI/automation consulting business
  "category": a short 1-3 word category label (e.g. "IT services", "Facilities", "Administrative")
Return ONLY the JSON object, no other text."""


def summarize_bid(bid: dict, api_key: str) -> dict:
    """Takes one normalized bid dict and returns it enriched with summary/relevance/category."""
    user_content = (
        f"Title: {bid.get('title')}\n"
        f"Agency: {bid.get('agency')}\n"
        f"NAICS code: {bid.get('naics')}\n"
        f"Due date: {bid.get('due_date')}\n"
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    # Groq's free tier has a fairly low requests-per-minute cap. Retry on 429 with
    # backoff (honoring Retry-After when present) instead of failing the whole run.
    max_attempts = 5
    for attempt in range(max_attempts):
        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code == 429 and attempt < max_attempts - 1:
            wait = float(resp.headers.get("Retry-After", 5 * (attempt + 1)))
            time.sleep(wait)
            continue
        resp.raise_for_status()
        break
    content = resp.json()["choices"][0]["message"]["content"]

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = {"summary": "Could not generate summary.", "relevance": "Low", "category": "Uncategorized"}

    return {
        **bid,
        "summary": parsed.get("summary", ""),
        "relevance": parsed.get("relevance", "Low"),
        "category": parsed.get("category", "Uncategorized"),
    }


def summarize_all(bids: list, api_key: str, max_bids: int = 30) -> list:
    enriched = []
    for i, b in enumerate(bids[:max_bids]):
        enriched.append(summarize_bid(b, api_key))
        if i < len(bids) - 1:
            time.sleep(1.2)  # stay under Groq's free-tier requests-per-minute limit
    return enriched


if __name__ == "__main__":
    sample = {
        "id": "TEST123",
        "title": "Desktop and network support services",
        "agency": "Department of Example",
        "naics": "541512",
        "due_date": "2026-08-30",
    }
    key = os.environ.get("GROQ_API_KEY", "")
    print(json.dumps(summarize_bid(sample, key), indent=2))
