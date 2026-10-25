# Restaurant Insights AI

A recruiter-friendly, portfolio demonstration of how restaurant operational metrics can be translated into clear manager briefings using **Python + Streamlit + optional Claude API**. All data is synthetic. Not affiliated with Farmer Boys.

## Features
- Store Manager view: weekly KPIs, plain-English briefing, next action, and evidence limitations.
- VP / Operations view: cost/sales trends and restaurant comparisons.
- Business Q&A with verified calculations (predefined questions; **not** free-form NL-to-SQL).
- Optional real Claude API generation for manager briefings; deterministic offline fallback if no key is configured.
- Clear separation of observed metrics, hypotheses, and recommendations.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Connect your Claude API key

Create `.streamlit/secrets.toml` in your project folder:

```toml
ANTHROPIC_API_KEY = "your_key_here"
```

Alternatively set `ANTHROPIC_API_KEY` as an environment variable. **Never commit your key to GitHub.** `.gitignore` excludes local secrets.

For **Streamlit Community Cloud**: push the project files to GitHub (without secrets), deploy `app.py`, then open **App settings → Secrets** and add the same `ANTHROPIC_API_KEY = "..."` line. Reboot the app if needed.

The default model is `claude-sonnet-4-5`; `claude-haiku-4-5` is an alternative. Your API account must have access to the selected model. If a model is unavailable, adjust the model identifier in `app.py` to one your account supports.

Click **Generate with Claude** in the Store Manager view. Claude usage may incur API charges. Without a key, the demo still runs using calculation-grounded text templates.

## Data & AI safety

- `sample_restaurant_data.csv` is entirely fabricated.
- Weekly ratios use `cost / sales`; differences in ratios are reported as **percentage points**, not percent changes.
- Calculations are performed in Python. Only derived synthetic facts are sent to Claude.
- Claude receives a restrictive instruction to avoid inventing numbers or claiming causality; its response is checked for expected JSON fields, but generated text is **not mathematically verified**. Human review is required.
- No upload of real operational, employee or customer data is provided.
- Recommendations are investigation ideas, not proven causal findings.

## Recruiter demo (60 seconds)

1. Select a restaurant and show sales, labor share, food share, and service time.
2. Click **Generate with Claude** to show a plain-English manager briefing.
3. Explain that the figures are computed first, and AI translates them into manager-friendly language.
4. Switch to **VP / Operations** to show underlying evidence and store comparisons.

**Project story:** “A recruiter asked how I would explain analytics to a store manager. I built a small example that connects operational metrics with plain-English, action-oriented communication.”
