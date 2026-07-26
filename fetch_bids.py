"""
Pulls open contract opportunities from the SAM.gov Get Opportunities Public API.

Docs: https://open.gsa.gov/api/get-opportunities-public-api/
Free tier: 10 requests/day without registering an API key, 1,000/day with a free key.

Usage:
    from fetch_bids import fetch_opportunities
    bids = fetch_opportunities(api_key="...", keywords=["IT services"], naics_codes=["541512"])
"""

import os
import datetime
import requests

SAM_API_URL = "https://api.sam.gov/opportunities/v2/search"


def _date_str(d: datetime.date) -> str:
    # SAM.gov expects MM/dd/yyyy
    return d.strftime("%m/%d/%Y")


def fetch_opportunities(api_key: str, keywords=None, naics_codes=None, days_back: int = 3, limit: int = 25):
    """
    Fetch active solicitations posted in the last `days_back` days.

    Returns a list of dicts with a normalized shape:
        {id, title, agency, naics, posted_date, due_date, description_url, sam_url}
    """
    today = datetime.date.today()
    start = today - datetime.timedelta(days=days_back)

    params = {
        "api_key": api_key,
        "postedFrom": _date_str(start),
        "postedTo": _date_str(today),
        "limit": limit,
        "ptype": "o",  # o = solicitation/opportunity (not award notices)
    }

    # SAM.gov's ncode and title params only take one value each, so multiple NAICS
    # codes or keywords are queried one at a time and merged/de-duplicated locally.
    # NAICS code is a structured field and a much more reliable filter than a title
    # keyword match (opportunity titles rarely contain the literal keyword text), so
    # prefer naics_codes when both are given.
    if naics_codes:
        results = {}
        for code in naics_codes:
            resp = requests.get(SAM_API_URL, params={**params, "ncode": code}, timeout=30)
            resp.raise_for_status()
            for item in resp.json().get("opportunitiesData", []):
                results[item.get("noticeId")] = item
        raw_items = list(results.values())
    elif keywords:
        results = {}
        for kw in keywords:
            resp = requests.get(SAM_API_URL, params={**params, "title": kw}, timeout=30)
            resp.raise_for_status()
            for item in resp.json().get("opportunitiesData", []):
                results[item.get("noticeId")] = item
        raw_items = list(results.values())
    else:
        resp = requests.get(SAM_API_URL, params=params, timeout=30)
        resp.raise_for_status()
        raw_items = resp.json().get("opportunitiesData", [])

    normalized = []
    for item in raw_items:
        normalized.append({
            "id": item.get("noticeId"),
            "title": item.get("title", "Untitled opportunity"),
            "agency": item.get("fullParentPathName", "Unknown agency"),
            "naics": item.get("naicsCode", ""),
            "posted_date": item.get("postedDate", ""),
            "due_date": item.get("responseDeadLine", ""),
            "description_url": item.get("description", ""),
            "sam_url": item.get("uiLink", ""),
        })

    return normalized


if __name__ == "__main__":
    key = os.environ.get("SAM_GOV_API_KEY", "")
    kws = os.environ.get("BID_KEYWORDS", "IT services").split(",")
    codes = [c for c in os.environ.get("NAICS_CODES", "").split(",") if c]
    bids = fetch_opportunities(api_key=key, keywords=kws, naics_codes=codes)
    print(f"Fetched {len(bids)} opportunities")
    for b in bids[:5]:
        print("-", b["title"])
