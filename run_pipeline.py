"""
Orchestrator: fetch open opportunities from SAM.gov, summarize/score each one with an LLM,
and write the results to data/bids.json for the dashboard to read.

This is the script GitHub Actions runs on a schedule. It can also be run locally:
    python run_pipeline.py
"""

import os
import json
import datetime
from pathlib import Path

from fetch_bids import fetch_opportunities
from summarize import summarize_all

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = DATA_DIR / "bids.json"


def load_env_local():
    """Loads .env for local runs. In GitHub Actions, env vars are injected directly instead."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def main():
    load_env_local()

    sam_key = os.environ.get("SAM_GOV_API_KEY", "")
    groq_key = os.environ.get("GROQ_API_KEY", "")
    keywords = [k.strip() for k in os.environ.get("BID_KEYWORDS", "IT services").split(",") if k.strip()]
    naics = [c.strip() for c in os.environ.get("NAICS_CODES", "").split(",") if c.strip()]

    if not sam_key:
        raise SystemExit("Missing SAM_GOV_API_KEY. Set it in .env locally or as a GitHub Actions secret.")
    if not groq_key:
        raise SystemExit("Missing GROQ_API_KEY. Set it in .env locally or as a GitHub Actions secret.")

    print("Fetching opportunities from SAM.gov...")
    bids = fetch_opportunities(api_key=sam_key, keywords=keywords, naics_codes=naics)
    print(f"Found {len(bids)} opportunities. Summarizing with AI...")

    enriched = summarize_all(bids, api_key=groq_key)

    output = {
        "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
        "total_found": len(enriched),
        "high_relevance": sum(1 for b in enriched if b.get("relevance") == "High"),
        "categories": sorted(set(b.get("category", "Uncategorized") for b in enriched)),
        "bids": enriched,
    }

    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output, indent=2))
    print(f"Wrote {len(enriched)} bids to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
