# core/analytics.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt



@st.cache_data(show_spinner="Forecasting future expenses...")
def get_forecast(df: pd.DataFrame) -> str:
    """
    Generates a financial forecast summary using a simple linear trend model.
    This provides a more robust forecast than the previous version.
    """
    if df.empty or len(df) < 3:
        return "Not enough transaction data to generate a forecast. Please add more entries."
    
    # Filter out income to forecast expenses only
    expense_df = df[df['category'] != 'Income'].copy()
    if len(expense_df) < 3:
        return "Not enough expense data to generate a forecast. Please add more expense entries."

    expense_df["date"] = pd.to_datetime(expense_df["date"])
    
    # Aggregate expenses by day
    daily_expenses = expense_df.groupby(expense_df["date"].dt.date)["amount"].sum().reset_index()
    daily_expenses["ordinal"] = pd.to_datetime(daily_expenses["date"]).map(datetime.toordinal)

    # Simple linear regression
    coeffs = np.polyfit(daily_expenses["ordinal"], daily_expenses["amount"], 1)
    poly = np.poly1d(coeffs)
    
    last_day_ord = daily_expenses["ordinal"].max()
    future_ord = np.arange(last_day_ord + 1, last_day_ord + 31)
    
    # Predict future daily expenses and ensure they are not negative
    future_preds = poly(future_ord)
    future_preds[future_preds < 0] = 0
    
    total_forecast = float(np.sum(future_preds))
    avg_daily_spend = expense_df.groupby(expense_df['date'].dt.date)['amount'].sum().mean()
    
    return (
        f"### 🗓️ 30-Day Expense Forecast\n\n"
        f"Based on your recent spending habits, you are projected to spend approximately **₹{total_forecast:,.2f}** over the next 30 days.\n\n"
        f"*Your average daily spend has been **₹{avg_daily_spend:,.2f}**.*\n\n"
        f"> **Disclaimer:** This is a simple trend-based projection and may not account for large, irregular expenses."
    )

def _prep_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "category", "amount", "note"])
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["amount"] = pd.to_numeric(out["amount"], errors="coerce").fillna(0.0)
    out["category"] = out["category"].astype(str)
    return out.dropna(subset=["date"])

# ---------- Matplotlib charts ----------
def create_spending_pie_chart(df_cat_sum: pd.DataFrame):
    """
    Expects columns: category, amount (expenses only).
    Returns a Matplotlib Figure.
    """
    if df_cat_sum is None or df_cat_sum.empty:
        return None

    labels = df_cat_sum["category"].astype(str).tolist()
    values = df_cat_sum["amount"].astype(float).tolist()

    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    # donut pie
    wedges, texts = ax.pie(values, startangle=90, wedgeprops=dict(width=0.45))
    # center hole
    centre_circle = plt.Circle((0, 0), 0.70, fc="white", alpha=0.0)  # transparent center (looks good on dark)
    ax.add_artist(centre_circle)
    ax.set(aspect="equal", title="Spending by Category")

    # simple legend on right
    ax.legend(wedges, labels, title="", loc="center left", bbox_to_anchor=(1.0, 0.5))
    fig.tight_layout()
    return fig

def create_income_expense_bar_chart(df_long: pd.DataFrame):
    """
    Expects long df with columns: date, amount, type ∈ {'Income','Expense'}.
    Returns a Matplotlib Figure.
    """
    if df_long is None or df_long.empty:
        return None

    df_long = df_long.sort_values("date")
    dates = df_long["date"].dt.date.unique()

    # split series
    inc = df_long[df_long["type"] == "Income"].groupby("date")["amount"].sum().reindex(df_long["date"].sort_values().unique(), fill_value=0)
    exp = df_long[df_long["type"] == "Expense"].groupby("date")["amount"].sum().reindex(df_long["date"].sort_values().unique(), fill_value=0)

    x = pd.to_datetime(inc.index).to_pydatetime()
    fig, ax = plt.subplots(figsize=(7, 4.2))
    width = 0.4

    ax.bar([d for d in x], inc.values, width=width, label="Income")
    ax.bar([d for d in x], -exp.values, width=width, label="Expense")  # show expenses downward for quick read

    ax.set_title("Income vs Expense")
    ax.set_ylabel("Amount")
    ax.axhline(0, linewidth=1)
    ax.legend(loc="upper left")
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig

# ---------- Safe renderer for Streamlit ----------
def st_matplotlib_safe(fig):
    """Render a Matplotlib figure if present; otherwise show a friendly note."""
    if fig is None:
        st.info("No data to display.")
        return
    st.pyplot(fig, use_container_width=True)
