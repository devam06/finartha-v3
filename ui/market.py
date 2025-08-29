# ui/market.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from core.stock_market import get_stock_data, get_stock_analysis

def _price_fig(history: pd.DataFrame, ticker: str):
    """Create a Matplotlib price chart (with 20D/50D MAs if available)."""
    if history is None or history.empty:
        return None

    df = history.copy()

    # Prefer common price columns; otherwise pick the first numeric column
    price_col = None
    for c in ["Close", "Adj Close", "close", "adj_close", "Price", "price"]:
        if c in df.columns:
            price_col = c
            break
    if price_col is None:
        num_cols = df.select_dtypes(include="number").columns
        if len(num_cols) == 0:
            return None
        price_col = num_cols[0]

    s = pd.to_numeric(df[price_col], errors="coerce").dropna()

    # Ensure datetime index for nicer x-axis formatting
    try:
        s.index = pd.to_datetime(s.index)
    except Exception:
        pass

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(s.index, s.values, linewidth=1.5, label="Price")

    # Add simple moving averages if enough data
    if len(s) >= 20:
        ax.plot(s.index, s.rolling(20).mean(), linewidth=1, linestyle="--", label="20D MA")
    if len(s) >= 50:
        ax.plot(s.index, s.rolling(50).mean(), linewidth=1, linestyle=":", label="50D MA")

    ax.set_title(f"{ticker} — Price")
    ax.set_ylabel("Price")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left")
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig

def render_market_tab():
    """Renders the UI for the stock market information tab (Matplotlib version)."""
    st.subheader("📈 Stock Market Information")

    ticker = st.text_input(
        "Enter Stock Ticker Symbol",
        placeholder="e.g., AAPL, GOOG, or RELIANCE.NS for Indian stocks"
    ).upper()

    if st.button("Get Stock Data", use_container_width=True):
        if ticker:
            with st.spinner(f"Fetching data for {ticker}..."):
                info, history = get_stock_data(ticker)
                st.session_state.stock_info = info
                st.session_state.stock_history = history
        else:
            st.warning("Please enter a stock ticker symbol.")
            st.session_state.stock_info = None
            st.session_state.stock_history = None

    if "stock_info" in st.session_state and st.session_state.stock_info:
        info = st.session_state.stock_info
        history = st.session_state.stock_history

        st.markdown(f"## {info.get('longName', 'N/A')} ({info.get('symbol', 'N/A')})")

        # --- Key Metrics ---
        price = info.get("currentPrice") or info.get("regularMarketPrice", 0) or 0
        prev_close = info.get("previousClose", 0) or 0
        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Last Price", f"{price:,.2f} {info.get('currency', '')}", f"{change:,.2f} ({change_pct:.2f}%)")
        col2.metric("Market Cap", f"{(info.get('marketCap', 0) / 1e9):.2f}B")
        col3.metric("Volume", f"{info.get('volume', 0):,}")

        st.markdown("---")

        # --- Chart (Matplotlib) and Analysis ---
        fig = _price_fig(history, ticker)
        if fig is not None:
            st.pyplot(fig, use_container_width=True)
        else:
            st.info("No price data to chart.")

        if st.button("Generate AI Analysis", use_container_width=True):
            with st.spinner("🤖 FinBuddy is analyzing the data..."):
                analysis = get_stock_analysis(info)
                st.session_state.stock_analysis = analysis

        if "stock_analysis" in st.session_state and st.session_state.stock_analysis:
            st.markdown("### AI-Powered Fundamental Snapshot")
            st.info(st.session_state.stock_analysis)

    elif "stock_info" in st.session_state and st.session_state.stock_info is None:
        st.error(
            "Could not find data. Please check the symbol "
            "(e.g., 'MSFT' for US stocks, 'RELIANCE.NS' for Indian stocks)."
        )
