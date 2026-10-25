"""Restaurant Insights AI — synthetic-data portfolio demo."""
from pathlib import Path
import json
import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Restaurant Insights AI", page_icon="🍽️", layout="wide")
st.markdown("""<style>.block-container{padding-top:1.6rem;max-width:1200px}.hero{background:linear-gradient(115deg,#133d38,#246b58);color:white;padding:26px 30px;border-radius:17px;margin-bottom:16px}.hero h1{color:white;margin:0}.hero p{color:#d9eee7;margin:7px 0 0}.box{background:#edf7f2;padding:20px;border-radius:12px;border-left:5px solid #24795c}.foot{color:#64746e;font-size:.88rem}</style>""",unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>Restaurant Insights AI</h1><p>From operational metrics to manager-ready decisions</p></div>',unsafe_allow_html=True)
st.caption("INDEPENDENT PORTFOLIO DEMO • 100% SYNTHETIC RESTAURANT DATA • Not affiliated with Farmer Boys")

@st.cache_data
def load_data():
    df = pd.read_csv(Path(__file__).with_name("sample_restaurant_data.csv"))
    required = {"store", "week", "sales", "labor_cost", "food_cost", "service_minutes", "transactions"}
    if not required.issubset(df.columns):
        raise ValueError("Dataset is missing required columns")
    for col in required - {"store", "week"}:
        df[col] = pd.to_numeric(df[col], errors="raise")
    if df[list(required - {"store", "week"})].isna().any().any() or (df[["sales", "transactions"]] <= 0).any().any():
        raise ValueError("Invalid numeric values in data")
    return df

def delta(current, prior):
    return (current / prior - 1) * 100 if prior else None

def signed(x, unit="%"):
    return f"{x:+.1f}{unit}" if x is not None else "N/A"

def facts_for(prior, current):
    sales_change = delta(current.sales, prior.sales)
    transactions_change = delta(current.transactions, prior.transactions)
    labor_ratio_prior = prior.labor_cost / prior.sales * 100
    labor_ratio_current = current.labor_cost / current.sales * 100
    food_ratio_prior = prior.food_cost / prior.sales * 100
    food_ratio_current = current.food_cost / current.sales * 100
    return {
        "sales_prior_usd": round(float(prior.sales),2), "sales_current_usd": round(float(current.sales),2),
        "sales_change_pct": round(sales_change,2),
        "transactions_prior": int(prior.transactions), "transactions_current": int(current.transactions),
        "transactions_change_pct": round(transactions_change,2),
        "average_ticket_prior_usd": round(float(prior.sales/prior.transactions),2),
        "average_ticket_current_usd": round(float(current.sales/current.transactions),2),
        "labor_spend_prior_usd": round(float(prior.labor_cost),2),
        "labor_spend_current_usd": round(float(current.labor_cost),2),
        "labor_spend_change_pct": round(delta(current.labor_cost,prior.labor_cost),2) if prior.labor_cost else None,
        "labor_ratio_prior_pct": round(labor_ratio_prior,2),
        "labor_ratio_current_pct": round(labor_ratio_current,2),
        "labor_ratio_change_pp": round(labor_ratio_current-labor_ratio_prior,2),
        "food_ratio_prior_pct": round(food_ratio_prior,2),
        "food_ratio_current_pct": round(food_ratio_current,2),
        "food_ratio_change_pp": round(food_ratio_current-food_ratio_prior,2),
        "service_time_prior_min": round(float(prior.service_minutes),2),
        "service_time_current_min": round(float(current.service_minutes),2),
        "service_time_change_min": round(float(current.service_minutes-prior.service_minutes),2),
    }

def local_brief(f):
    sales_direction = "declined" if f["sales_change_pct"] < 0 else "increased"
    labor_direction = "rose" if f["labor_ratio_change_pp"] > 0 else "fell"
    service_direction = "increased" if f["service_time_change_min"] > 0 else "decreased"
    return {
        "headline": "Weekly restaurant performance at a glance",
        "what_happened": f"Sales {sales_direction} {abs(f['sales_change_pct']):.1f}% from last week. Labor expense as a share of sales {labor_direction} {abs(f['labor_ratio_change_pp']):.1f} percentage points. Average service time {service_direction} {abs(f['service_time_change_min']):.1f} minutes.",
        "why_it_matters": "Changes in sales, labor share, and service time may affect operating efficiency and guest experience. The data alone does not establish the cause.",
        "recommended_action": "Compare hourly order volume with staffing schedules and review order-flow bottlenecks before testing a small operational change.",
        "evidence_limit": "Weekly totals cannot identify specific shifts, staffing mismatches, or causes. Shift-level records and manager input are needed.",
    }

SYSTEM = """You are an operations analytics communication assistant. Explain VERIFIED numeric facts to a nontechnical restaurant store manager. You are given a JSON object of precomputed, synthetic, weekly restaurant metrics. Never invent numbers, drivers, shifts, weather, promotions, guest complaints, or causal conclusions. Clearly separate observed changes from hypotheses. Do not assert that labor cost ratio changes necessarily mean labor dollars rose. Give one modest, practical next investigation and say what further data would be needed. Do not provide financial projections. Respond with ONLY a valid JSON object containing exactly these five string keys: headline, what_happened, why_it_matters, recommended_action, evidence_limit. Keep each field short, conversational and accessible; no markdown."""

def get_key():
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        key = ""
    return key or os.environ.get("ANTHROPIC_API_KEY", "")

def claude_brief(f, model, key):
    from anthropic import Anthropic
    client = Anthropic(api_key=key, timeout=25.0, max_retries=1)
    response = client.messages.create(model=model, max_tokens=650, temperature=0, system=SYSTEM,
        messages=[{"role":"user", "content":"Verified restaurant facts (JSON): " + json.dumps(f)}])
    raw = "".join(block.text for block in response.content if getattr(block, "type", "") == "text").strip()
    if raw.startswith("```"):
        raw = raw.strip("`").removeprefix("json").strip()
    result = json.loads(raw)
    keys = ("headline", "what_happened", "why_it_matters", "recommended_action", "evidence_limit")
    if not isinstance(result, dict) or not all(isinstance(result.get(k),str) and result[k].strip() for k in keys):
        raise ValueError("Claude returned an unexpected format")
    return {k:result[k] for k in keys}

try:
    df = load_data()
except Exception as exc:
    st.error(f"Unable to load sample data: {exc}")
    st.stop()

with st.sidebar:
    st.header("Explore the demo")
    store = st.selectbox("Restaurant", sorted(df.store.unique()))
    audience = st.radio("Audience", ["Store manager", "VP / Operations"])
    st.divider()
    st.subheader("Claude AI")
    key = get_key()
    model = st.selectbox("Claude model", ["claude-sonnet-4-5", "claude-haiku-4-5"])
    st.caption("API key is read from Streamlit Secrets or environment variables; never enter it in the app or commit it to GitHub.")
    st.success("API key configured") if key else st.info("No API key detected. Reliable offline summaries remain available.")

rows = df[df.store == store].set_index("week")
if not {"Prior", "Current"}.issubset(rows.index):
    st.error("Sample data requires one Prior and one Current row per store.")
    st.stop()
prior, current = rows.loc["Prior"], rows.loc["Current"]
f = facts_for(prior, current)

st.subheader(f"{store} · Weekly performance")
c1,c2,c3,c4 = st.columns(4)
c1.metric("Weekly sales", f"${current.sales:,.0f}", signed(f["sales_change_pct"]))
c2.metric("Labor / sales", f"{f['labor_ratio_current_pct']:.1f}%", signed(f["labor_ratio_change_pp"]," pp"), delta_color="inverse")
c3.metric("Food / sales", f"{f['food_ratio_current_pct']:.1f}%", signed(f["food_ratio_change_pp"]," pp"), delta_color="inverse")
c4.metric("Avg service time", f"{current.service_minutes:.1f} min", signed(f["service_time_change_min"]," min"), delta_color="inverse")

if audience == "Store manager":
    st.markdown("### Your manager briefing")
    if "brief_cache" not in st.session_state:
        st.session_state.brief_cache = {}
    cache_key = (store,model)
    col1,col2 = st.columns([1,3])
    with col1:
        generate = st.button("✨ Generate with Claude", type="primary", disabled=not bool(key), use_container_width=True)
    with col2:
        st.caption("Claude rewrites pre-calculated facts into plain English. Click to generate; API usage may incur charges.")
    if generate:
        try:
            with st.spinner("Preparing your briefing..."):
                st.session_state.brief_cache[cache_key] = claude_brief(f,model,key)
        except Exception as exc:
            st.warning("Claude was unavailable or returned an invalid response. Showing the verified offline briefing instead. Check your key, model access and API credits.")
    brief = st.session_state.brief_cache.get(cache_key) if key else None
    if brief is None:
        brief = local_brief(f)
        st.caption("Showing a deterministic, calculation-grounded briefing (not AI-generated).")
    else:
        st.caption("Claude-generated explanation based on validated weekly metrics. Review before operational use.")
    st.markdown(f"<div class='box'><h3>{brief['headline']}</h3><b>What happened</b><p>{brief['what_happened']}</p><b>Why it matters</b><p>{brief['why_it_matters']}</p><b>Suggested next step</b><p>{brief['recommended_action']}</p></div>",unsafe_allow_html=True)
    st.info("**What we don't know yet:** " + brief["evidence_limit"])
    st.markdown("#### What the numbers show")
    st.write(f"Transactions: **{prior.transactions:,.0f} → {current.transactions:,.0f}** ({signed(f['transactions_change_pct'])}). Average ticket: **${f['average_ticket_prior_usd']:.2f} → ${f['average_ticket_current_usd']:.2f}**.")
else:
    st.markdown("### Operations diagnostic")
    chart = pd.DataFrame({"Week":["Prior", "Current"], "Sales":[prior.sales,current.sales], "Labor expense":[prior.labor_cost,current.labor_cost], "Food expense":[prior.food_cost,current.food_cost]})
    st.plotly_chart(px.bar(chart,x="Week",y=["Sales","Labor expense","Food expense"],barmode="group",title="Sales and direct expense trends"),use_container_width=True)
    st.write(f"**Sales:** {signed(f['sales_change_pct'])} · **Transactions:** {signed(f['transactions_change_pct'])} · **Labor dollars:** {signed(f['labor_spend_change_pct'])} · **Labor share:** {signed(f['labor_ratio_change_pp'],' pp')}")
    current_all = df[df.week == "Current"].copy()
    current_all["Labor %"] = (current_all.labor_cost/current_all.sales*100).round(1)
    current_all["Food %"] = (current_all.food_cost/current_all.sales*100).round(1)
    st.dataframe(current_all[["store","sales","Labor %","Food %","service_minutes","transactions"]].rename(columns={"store":"Restaurant","sales":"Sales ($)","service_minutes":"Service (min)","transactions":"Transactions"}),hide_index=True,use_container_width=True)
    st.markdown("**Investigation:** Check whether a higher labor ratio is driven by higher labor dollars, lower sales, or both. Weekly aggregates cannot pinpoint causes.")
    st.markdown("**Measure improvement:** Compare labor share, transactions per labor hour (if available), service time and guest feedback against a similar restaurant after an operational change.")

st.divider()
st.markdown("### Ask a business question")
question = st.selectbox("Example question",["Why did labor cost percentage change?","What happened to sales?","Is service getting slower?"])
if question.startswith("Why"):
    st.write(f"Labor / sales moved from **{f['labor_ratio_prior_pct']:.1f}%** to **{f['labor_ratio_current_pct']:.1f}%** ({signed(f['labor_ratio_change_pp'],' pp')}). Labor spending changed **{signed(f['labor_spend_change_pct'])}**, while sales changed **{signed(f['sales_change_pct'])}**. Shift-level labor and demand data would help explain the pattern.")
elif question.startswith("What"):
    st.write(f"Sales moved from **${prior.sales:,.0f}** to **${current.sales:,.0f}** ({signed(f['sales_change_pct'])}). Transactions changed **{signed(f['transactions_change_pct'])}** and average ticket moved from **${f['average_ticket_prior_usd']:.2f}** to **${f['average_ticket_current_usd']:.2f}**. We would next investigate dayparts, promotions and menu mix.")
else:
    st.write(f"Average service time moved from **{prior.service_minutes:.1f}** to **{current.service_minutes:.1f} minutes** ({signed(f['service_time_change_min'],' min')}). This doesn't establish why it changed; order-level timestamps would be needed.")
with st.expander("Data, methodology and responsible AI"):
    st.write("The CSV contains synthetic weekly observations. Python calculates all metrics before an optional Claude call. Claude is instructed to explain those facts without inventing causes; its text should still be reviewed. No real customer, employee or company data is used. This demo is not a predictive model, a causal study, or an automated decision system.")
    st.json(f)
    st.dataframe(rows.reset_index(),hide_index=True)
