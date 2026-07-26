"""
Public dashboard for the bid monitoring agent. Reads data/bids.json (written by run_pipeline.py,
refreshed daily by GitHub Actions) and displays it. No API keys needed to view this, it's a
read-only viewer.

Run locally:    streamlit run dashboard.py
Deploy free:    push to a public GitHub repo, then deploy at share.streamlit.io
"""

import json
from pathlib import Path

import streamlit as st

DATA_FILE = Path(__file__).parent / "data" / "bids.json"

st.set_page_config(page_title="SAM.gov Bid Opportunity Tracker", layout="centered")
st.title("SAM.gov Bid Opportunity Tracker")
st.caption("Public contract opportunities, checked and summarized automatically every day.")
st.caption("Built by Robert Selders II")
if not DATA_FILE.exists():
    st.info("No data yet. Run `python run_pipeline.py` once to generate data/bids.json.")
    st.stop()

data = json.loads(DATA_FILE.read_text())
bids = data.get("bids", [])

st.caption(f"Last updated: {data.get('last_updated', 'unknown')}")

col1, col2, col3 = st.columns(3)
col1.metric("Opportunities found", data.get("total_found", len(bids)))
col2.metric("High relevance", data.get("high_relevance", 0))
col3.metric("Categories tracked", len(data.get("categories", [])))

st.divider()

relevance_order = {"High": 0, "Medium": 1, "Low": 2}
bids_sorted = sorted(bids, key=lambda b: relevance_order.get(b.get("relevance", "Low"), 3))

relevance_filter = st.multiselect(
    "Filter by relevance",
    options=["High", "Medium", "Low"],
    default=["High", "Medium", "Low"],
)

for bid in bids_sorted:
    if bid.get("relevance") not in relevance_filter:
        continue

    badge_color = {"High": "green", "Medium": "orange", "Low": "gray"}.get(bid.get("relevance"), "gray")

    with st.container(border=True):
        left, right = st.columns([4, 1])
        with left:
            st.markdown(f"**{bid.get('title', 'Untitled')}**")
            st.caption(f"{bid.get('agency', 'Unknown agency')} · {bid.get('category', 'Uncategorized')}")
            st.write(bid.get("summary", ""))
        with right:
            st.markdown(f":{badge_color}[{bid.get('relevance', 'Low')}]")
            st.caption(f"Due {bid.get('due_date', 'n/a')}")
            if bid.get("sam_url"):
                st.link_button("View on SAM.gov", bid["sam_url"])

if not bids_sorted:
    st.write("No opportunities match the current filter.")
