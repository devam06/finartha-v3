# core/stock_market.py
import json
import streamlit as st
import pandas as pd
from .ai_services import get_ai_response  # safe wrapper we added earlier

@st.cache_data(ttl=300)  # Cache data for 5 minutes
def get_stock_data(ticker_symbol: str):
    """Fetch 1Y price history + basic info for a ticker. Returns (info, history_df) or (None, error_str)."""
    try:
        import yfinance as yf  # lazy import so missing dep doesn't crash module import
    except Exception as e:
        return None, f"yfinance not installed or failed to import: {e}"

    try:
        ticker_symbol = (ticker_symbol or "").strip()
        if not ticker_symbol:
            return None, "Empty ticker symbol."

        t = yf.Ticker(ticker_symbol)
        info = t.info or {}

        # Basic validity check
        has_price = ("currentPrice" in info) or ("regularMarketPrice" in info)
        if not has_price:
            return None, (
                f"Could not find data for '{ticker_symbol}'. "
                "Check the symbol (e.g., 'MSFT' for US, 'RELIANCE.NS' for India)."
            )

        hist = t.history(period="1y")
        if isinstance(hist, pd.DataFrame) and not hist.empty:
            # Ensure a datetime index for plotting
            try:
                hist.index = pd.to_datetime(hist.index)
            except Exception:
                pass

        return info, hist
    except Exception as e:
        return None, f"Error while fetching data: {e}"

# NOTE: We intentionally removed create_price_chart() because the Market tab
# now builds a Matplotlib chart internally in ui/market.py (_price_fig).

def get_stock_analysis(info: dict) -> str:
    """
    Uses Gemini (via core.ai_services.get_ai_response) to generate a neutral,
    data-driven snapshot. Never uses advisory language.
    """
    # Keep payload concise
    relevant_info = {
        "Company Name": info.get("longName"),
        "Symbol": info.get("symbol"),
        "Sector": info.get("sector"),
        "Industry": info.get("industry"),
        "Business Summary": info.get("longBusinessSummary"),
        "Current Price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "Market Cap": info.get("marketCap"),
        "52-Week High": info.get("fiftyTwoWeekHigh"),
        "52-Week Low": info.get("fiftyTwoWeekLow"),
        "Volume": info.get("volume"),
        "P/E Ratio": info.get("trailingPE"),
        "Currency": info.get("currency"),
    }

    prompt = f"""
You are a financial data analyst. Provide a neutral, objective summary of the company
based ONLY on the JSON below. Do NOT give investment advice.

JSON:
{json.dumps(relevant_info, ensure_ascii=False)}

FORMAT:
1) 1 short paragraph describing the business.
2) Key metrics as concise bullet points.
3) "Fundamental Snapshot" with 2–3 neutral observations (e.g., what a high/low P/E might imply).
4) Mandatory disclaimer:
   "Disclaimer: This is an AI-generated analysis based on public data and is for informational purposes only.
    It is not financial advice. Please consult a qualified financial advisor before making any investment decisions."

Rules:
- Avoid words like buy/sell/hold or prescriptive advice.
- No price predictions.
""".strip()

    try:
        return get_ai_response(prompt)
    except Exception as e:
        # get_ai_response already handles most errors gracefully; this is a final guard.
        return f"An error occurred during AI analysis: {e}"
