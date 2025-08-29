# ui/reports.py
import streamlit as st
import pandas as pd
from core.analytics import create_spending_pie_chart, create_income_expense_bar_chart

# ui/reports.py
import streamlit as st
import pandas as pd
from core.analytics import (
    create_spending_pie_chart,        # now returns a Matplotlib Figure
    create_income_expense_bar_chart,  # now returns a Matplotlib Figure
)

def render_reports_tab(df: pd.DataFrame):
    """Renders the dashboard with visual reports (Matplotlib)."""
    st.subheader("Financial Dashboard")

    if df is None or df.empty:
        st.warning("No transaction data available. Please add transactions in the sidebar to view reports.")
        return

    # --- Normalize data once ---
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["category"] = df["category"].astype(str)
    df = df.dropna(subset=["date"])

    # --- Key Metrics ---
    total_income = df[df["category"].str.strip().str.lower() == "income"]["amount"].sum()
    total_expense = df[df["category"].str.strip().str.lower() != "income"]["amount"].sum()
    net_savings = total_income - total_expense

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Income", f"₹{total_income:,.2f}", delta_color="normal")
    c2.metric("Total Expenses", f"₹{total_expense:,.2f}", delta_color="inverse")
    c3.metric("Net Savings", f"₹{net_savings:,.2f}", delta=f"{net_savings:,.2f}")

    st.markdown("---")

    # --- Visualizations (Matplotlib) ---
    col1, col2 = st.columns(2)

    # Spending by Category (donut pie)
    with col1:
        st.subheader("Spending by Category")
        exp_only = df[df["category"].str.strip().str.lower() != "income"]
        cat_sum = (
            exp_only.groupby("category", as_index=False)["amount"]
            .sum()
            .sort_values("amount", ascending=False)
        )
        fig1 = create_spending_pie_chart(cat_sum)  # Matplotlib Figure
        if fig1 is not None:
            st.pyplot(fig1, use_container_width=True)
        else:
            st.info("No expense data to display.")

    # Income vs. Expenses (bar; expenses shown downward)
    with col2:
        st.subheader("Income vs. Expenses")
        long_df = df.copy()
        long_df["type"] = long_df["category"].str.strip().str.lower().eq("income").map({True: "Income", False: "Expense"})
        long_df = long_df[["date", "amount", "type"]]
        fig2 = create_income_expense_bar_chart(long_df)  # Matplotlib Figure
        if fig2 is not None:
            st.pyplot(fig2, use_container_width=True)
        else:
            st.info("No income/expense data to display.")

    # Raw table (latest first)
    st.markdown("### Transactions (latest first)")
    st.dataframe(df.sort_values("date", ascending=False), use_container_width=True, hide_index=True)
