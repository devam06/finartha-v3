# ui/forecast.py
import os, json
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# ---------- Gemini setup ----------
def _get_gemini():
    try:
        import google.generativeai as genai
    except Exception:
        return None, "Missing google-generativeai. Add to requirements.txt and redeploy."
    key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        return None, "Missing GOOGLE_API_KEY. Add it in Streamlit Cloud → App → Settings → Secrets."
    genai.configure(api_key=key)
    # swap to "gemini-1.5-pro" for deeper reasoning (slower)
    model = genai.GenerativeModel("gemini-1.5-flash")
    return model, None

# ---------- Data prep ----------
def _to_date(x):
    try:
        return pd.to_datetime(x).date()
    except Exception:
        return None

def _prep_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "category", "amount", "note"])
    out = df.copy()
    out["date"] = out["date"].apply(_to_date)
    out = out.dropna(subset=["date"])
    out["category"] = out["category"].astype(str)
    out["amount"] = pd.to_numeric(out["amount"], errors="coerce").fillna(0.0)
    out["is_income"] = out["category"].str.strip().str.lower().eq("income")
    return out

def _window(df, start, end):
    return df[(df["date"] >= start) & (df["date"] <= end)]

def _last_n_days_metrics(df: pd.DataFrame, days=30):
    today = datetime.today().date()
    start = today - timedelta(days=days - 1)
    prev_start = start - timedelta(days=days)
    prev_end = start - timedelta(days=1)

    cur = _window(df, start, today)
    prev = _window(df, prev_start, prev_end)

    cur_income = cur.loc[cur["is_income"], "amount"].sum()
    cur_exp = cur.loc[~cur["is_income"], "amount"].sum()
    cur_net = cur_income - cur_exp
    cur_savings_rate = (cur_net / cur_income * 100.0) if cur_income > 0 else 0.0

    prev_income = prev.loc[prev["is_income"], "amount"].sum()
    prev_exp = prev.loc[~prev["is_income"], "amount"].sum()
    prev_net = prev_income - prev_exp

    by_cat = (
        cur.loc[~cur["is_income"]]
        .groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .to_dict()
    )

    prev_by_cat = prev.loc[~prev["is_income"]].groupby("category")["amount"].sum().to_dict()
    spikes = []
    for cat, v in by_cat.items():
        pv = prev_by_cat.get(cat, 0.0)
        change = (v - pv)
        pct = (change / pv * 100.0) if pv > 0 else (100.0 if v > 0 else 0.0)
        spikes.append({"category": cat, "cur": float(v), "prev": float(pv), "delta": float(change), "pct_change": float(pct)})
    spikes = sorted(spikes, key=lambda x: (-x["pct_change"], -x["delta"]))[:3]

    return {
        "period_days": days,
        "today": str(today),
        "current": {
            "income": float(cur_income),
            "expense": float(cur_exp),
            "net": float(cur_net),
            "savings_rate_pct": float(cur_savings_rate),
            "top_categories": by_cat,
        },
        "previous": {
            "income": float(prev_income),
            "expense": float(prev_exp),
            "net": float(prev_net),
        },
        "category_spikes": spikes,
    }

# ---------- Local fallback ----------
def _local_status(metrics):
    inc = metrics["current"]["income"]
    exp = metrics["current"]["expense"]
    net = metrics["current"]["net"]
    sr = metrics["current"]["savings_rate_pct"]
    spikes = metrics["category_spikes"]
    big_spike = max((s["pct_change"] for s in spikes), default=0)
    if inc <= 0 and exp > 0:
        return "THUNDERSTORMS", "⛈️"
    if net >= 0 and sr >= 20 and big_spike < 15:
        return "CLEAR_SKIES", "☀️"
    if net >= 0 and (sr >= 5 or big_spike < 25):
        return "PARTLY_CLOUDY", "🌤️"
    if net < 0 and abs(net) <= 0.2 * max(inc, 1):
        return "LIGHT_SHOWERS", "🌧️"
    return "THUNDERSTORMS", "⛈️"

PROMPT = """You are a concise finance coach. The app computed summary metrics for the last {period_days} days.
Using the WEATHER metaphor, output a short forecast and one to three next steps.
Pick EXACTLY ONE status from this set:
- CLEAR_SKIES (☀️): everything on track.
- PARTLY_CLOUDY (🌤️): mostly fine, a few minor issues.
- LIGHT_SHOWERS (🌧️): caution; noticeable overspend or savings risk.
- THUNDERSTORMS (⛈️): critical issues; urgent action.

Return strictly valid JSON (no markdown, no backticks):
{{
  "status": "CLEAR_SKIES|PARTLY_CLOUDY|LIGHT_SHOWERS|THUNDERSTORMS",
  "emoji": "☀️|🌤️|🌧️|⛈️",
  "headline": "one-sentence summary",
  "explanation": "2-3 short sentences using the numbers in plain English",
  "actions": ["action 1", "action 2", "action 3"],
  "score": 0-100
}}

Numbers (INR):
current_income: {cur_income}
current_expense: {cur_expense}
current_net: {cur_net}
savings_rate_pct: {savings_rate_pct}
previous_income: {prev_income}
previous_expense: {prev_expense}
previous_net: {prev_net}
top_categories: {top_categories}
category_spikes: {category_spikes}

Rules:
- Negative net or >25% category spikes → lean 🌧️/⛈️ with specific actions.
- Positive net AND savings rate ≥20% and no big spikes → lean ☀️.
- Keep under ~80 words total.
"""

def _call_gemini(model, metrics):
    text = PROMPT.format(
        period_days=metrics["period_days"],
        cur_income=metrics["current"]["income"],
        cur_expense=metrics["current"]["expense"],
        cur_net=metrics["current"]["net"],
        savings_rate_pct=metrics["current"]["savings_rate_pct"],
        prev_income=metrics["previous"]["income"],
        prev_expense=metrics["previous"]["expense"],
        prev_net=metrics["previous"]["net"],
        top_categories=json.dumps(metrics["current"]["top_categories"]),
        category_spikes=json.dumps(metrics["category_spikes"]),
    )
    resp = model.generate_content(text)
    return resp.text if hasattr(resp, "text") else str(resp)

def _parse_json_maybe(text: str):
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{"); end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try: return json.loads(text[start:end+1])
            except Exception: return None
    return None

# ---------- Reusable compute + render ----------
def compute_forecast(days: int = 30):
    """Compute and return (result_dict, metrics_dict). No UI. Call once, render many times."""
    proj = st.session_state.get("selected_project")
    projects = st.session_state.get("projects", {})
    df = projects.get(proj) if proj in projects else None
    df = _prep_df(df)
    if df.empty:
        return {"empty": True}, {"period_days": days}
    metrics = _last_n_days_metrics(df, days=days)
    model, err = _get_gemini()

    if err:
        status, emoji = _local_status(metrics)
        obj = {
            "status": status,
            "emoji": emoji,
            "headline": _fallback_headline(status, metrics),
            "explanation": "",
            "actions": ["Pre-commit a small saving", "Cap top category for 2 weeks"],
            "score": 65 if status in ("CLEAR_SKIES", "PARTLY_CLOUDY") else 35,
        }
        return obj, metrics

    try:
        raw = _call_gemini(model, metrics)
        obj = _parse_json_maybe(raw) or {}
    except Exception:
        obj = {}

    if not obj or "status" not in obj:
        status, emoji = _local_status(metrics)
        obj = {
            "status": status,
            "emoji": emoji,
            "headline": _fallback_headline(status, metrics),
            "explanation": "",
            "actions": ["Pre-commit a small saving", "Cap top category for 2 weeks"],
            "score": 65 if status in ("CLEAR_SKIES", "PARTLY_CLOUDY") else 35,
        }
    return obj, metrics

def render_forecast_from(obj: dict, metrics: dict, title="Financial Forecast"):
    """Render UI from a precomputed object (so you can show it in multiple places)."""
    st.subheader(title)
    if obj.get("empty"):
        st.info("Add a few transactions to get your first forecast.")
        return
    emoji = obj.get("emoji", "🌤️")
    headline = obj.get("headline", "Your short-term outlook")
    explanation = obj.get("explanation", "")
    actions = obj.get("actions", []) or []
    score = obj.get("score", None)

    _status_badge(emoji, headline)
    if explanation:
        st.caption(explanation)
    if score is not None:
        st.progress(int(max(0, min(100, score))))
    if actions:
        st.markdown("**Suggested next steps**")
        for a in actions[:3]:
            st.markdown(f"- {a}")

    with st.expander("What I looked at"):
        c = metrics.get("current", {}); p = metrics.get("previous", {})
        st.write(
            {
                "current_income": c.get("income"),
                "current_expense": c.get("expense"),
                "current_net": c.get("net"),
                "savings_rate_pct": c.get("savings_rate_pct"),
                "previous_net": p.get("net"),
                "top_categories": c.get("top_categories"),
                "category_spikes": metrics.get("category_spikes"),
            }
        )

# Backward-compatible wrapper (optional)
def render_forecast():
    obj, metrics = compute_forecast(days=30)
    render_forecast_from(obj, metrics)

# ---------- UI bits ----------
def _status_badge(emoji: str, headline: str):
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:.75rem;
                    padding:.9rem 1rem;border-radius:16px;
                    border:1px solid rgba(255,255,255,.12);
                    background:linear-gradient(135deg, rgba(124,58,237,.18), rgba(6,182,212,.12));
                    box-shadow:0 10px 30px rgba(124,58,237,.25);">
            <div style="font-size:1.6rem">{emoji}</div>
            <div style="font-weight:700">{headline}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def _fallback_headline(status, m):
    net = m.get("current", {}).get("net", 0)
    sr = m.get("current", {}).get("savings_rate_pct", 0)
    if status == "CLEAR_SKIES": return f"Clear skies — healthy net (₹{net:,.0f}) and {sr:.0f}% savings rate."
    if status == "PARTLY_CLOUDY": return "Partly cloudy — mostly on track with a few minor hotspots."
    if status == "LIGHT_SHOWERS": return "Light showers — caution: spending is pressuring savings."
    return "Thunderstorms — urgent attention needed to stabilize cash flow."

