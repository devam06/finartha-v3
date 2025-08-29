# >>> UI ENHANCER: do not move (needs to run first) >>>

try:
    from ui.theme import inject_css as _inject_ui_css
    _inject_ui_css()
except Exception:
    # don't break app if UI skin fails
    pass
# <<< UI ENHANCER <<<

# main.py
import streamlit as st
import pandas as pd

# Import UI modules

from ui.forecast import compute_forecast, render_forecast_from
from ui.theme import section_card  # optional: for glass card wrapper
from ui.sidebar import render_sidebar
from ui.reports import render_reports_tab
from ui.planning import render_planning_tab
from ui.chat import render_chat_tab
from ui.guides import render_guides_tab
from ui.market import render_market_tab # <- ADD THIS IMPORT

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="FinBuddy AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SESSION STATE INITIALIZATION (MODIFIED) ---
def initialize_session_state():
    """Initializes session state variables if they don't exist."""
    if "projects" not in st.session_state:
        st.session_state.projects = {} # Start with no projects
    if "selected_project" not in st.session_state:
        st.session_state.selected_project = None # No project selected initially
    if "messages" not in st.session_state:
        st.session_state.messages = []

# --- 3. MAIN APP LAYOUT (MODIFIED) ---
def main():
    """Main function to render the Streamlit app."""
    initialize_session_state()
    render_sidebar()

    st.title("FinBuddy AI Assistant 🤖")

    if not st.session_state.selected_project:
        st.info("👋 Welcome to FinBuddy! Create or select a project in the sidebar to get started.")
        st.markdown("""
        **FinBuddy helps you manage your finances with the power of AI.**
        - **Track** your income and expenses effortlessly.
        - **Visualize** your spending habits on the Dashboard.
        - **Plan** your budget and savings goals.
        - **Chat** with an AI for financial insights.
        - **Explore** real-time stock market data.
        """)
        st.stop()
    
    df = st.session_state.projects.get(st.session_state.selected_project, pd.DataFrame())

    # --- TABS FOR NAVIGATION (MODIFIED) ---
    chat_tab, reports_tab, planning_tab, market_tab, guides_tab = st.tabs(
        ["💬 Chat", "📊 Dashboard & Reports", "🎯 Planning", "📈 Market Info", "📚 Guides"]
    )

    with chat_tab:
        render_chat_tab(df)
    with reports_tab:
        render_reports_tab(df)
    with planning_tab:
        render_planning_tab(df)
    with market_tab:
        render_market_tab() # <- ADD THIS
    with guides_tab:
        render_guides_tab()

# --- 4. APP ENTRYPOINT ---
if __name__ == "__main__":
    main()

forecast_obj, forecast_metrics = compute_forecast(days=30)
tabs = st.tabs(["Forecast"])

# --- Dashboard tab ---
with tabs[0]:
    with section_card():
        render_forecast_from(forecast_obj, forecast_metrics, title="Financial Forecast")

    # ... your other Dashboard widgets/charts

# --- Reports tab ---

    # ... your existing report tables/plots
