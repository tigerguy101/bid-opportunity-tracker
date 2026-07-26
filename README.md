# Bid opportunity tracker

An agentic pipeline that checks SAM.gov for new federal contract opportunities every day,
uses an LLM to summarize and score each one for relevance, and displays the results on a
public dashboard. Runs entirely in the cloud via GitHub Actions, no computer needs to stay on.

**How it works**

1. GitHub Actions wakes up once a day (fully automated, see `.github/workflows/daily-bid-check.yml`).
2. `fetch_bids.py` pulls new opportunities from the SAM.gov Get Opportunities Public API.
3. `summarize.py` sends each one to a free-tier LLM (Groq) which writes a plain-English
   summary, a relevance score (High/Medium/Low), and a category.
4. `run_pipeline.py` ties those two together and writes the results to `data/bids.json`,
   which GitHub Actions commits back to the repo.
5. `dashboard.py` (a Streamlit app) reads that file and displays it. It never calls any
   API itself, it's a read-only viewer, so it stays fast and doesn't need any keys to run.

## 1. Get free API keys

- **SAM.gov**: sign in at [sam.gov](https://sam.gov), go to Account Details, and request an
  API key. Public access works too (10 requests/day) if you skip this, but a free key raises
  that to 1,000/day.
- **Groq**: create a free key at [console.groq.com/keys](https://console.groq.com/keys).
  No credit card required for the free tier.

## 2. Run it locally first

```bash
pip install -r requirements.txt
cp .env.example .env        # then fill in your two API keys
python run_pipeline.py      # generates data/bids.json
streamlit run dashboard.py  # opens the dashboard at localhost:8501
```

## 3. Put it on GitHub (public repo)

```bash
git init
git add .
git commit -m "Initial commit: bid opportunity tracker"
gh repo create bid-opportunity-tracker --public --source=. --push
# no gh CLI? create a repo on github.com and follow its "push an existing repo" instructions
```

Then, in the repo's Settings -> Secrets and variables -> Actions:

- Add repository secrets `SAM_GOV_API_KEY` and `GROQ_API_KEY`.
- Optionally add repository variables `BID_KEYWORDS` and `NAICS_CODES` to customize what
  it looks for (defaults live in `.env.example`).

The workflow runs automatically every day at 12:00 UTC. You can also trigger it manually
from the Actions tab (`workflow_dispatch`) to test it right away instead of waiting.

## 4. Deploy the public dashboard (free)

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click "New app", point it at your repo, and set the main file to `dashboard.py`.
3. Deploy. You'll get a public URL like `your-app-name.streamlit.app`.

Since GitHub Actions commits fresh data to the repo every day, and Streamlit Community
Cloud auto-redeploys on every push to the repo, the dashboard stays current with zero
manual steps after this initial setup.

## Customizing

- Change `BID_KEYWORDS` / `NAICS_CODES` in `.env` (local) or the repo's Actions variables
  (deployed) to match whatever categories of work you actually want to track.
- Swap the Groq call in `summarize.py` for OpenAI, Gemini, or Claude if you'd rather use a
  different model, the rest of the pipeline doesn't care which one you use.
- Change the cron schedule in `.github/workflows/daily-bid-check.yml` to run more or less
  often.

## Adapting this for a private data source

SAM.gov is used here because it has a clean public API that works for anyone. If you want
a private version pointed at a specific state's procurement notifications (many states,
including Louisiana's LaPAC system, don't have a public API and only notify registered
vendors by email), swap `fetch_bids.py` for a script that reads those emails instead, the
rest of the pipeline (summarize, save, display) stays the same.
