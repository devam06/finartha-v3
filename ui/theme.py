# ui/theme.py
import streamlit as st
from contextlib import contextmanager

def apply_theme():
    """High-end animated aurora + glassmorphism theme (safe if page_config already set)."""
    if not st.session_state.get("_ui_pgcfg_done", False):
        try:
            st.set_page_config(
                page_title="Finartha",
                page_icon="💠",
                layout="wide",
                initial_sidebar_state="expanded",
            )
        except Exception:
            # Page config was already set somewhere else—ignore.
            pass
        st.session_state["_ui_pgcfg_done"] = True

    css = """
    <style>
    /* Fonts (optional) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    :root{
      --brand-1:#7C3AED; /* violet */
      --brand-2:#06B6D4; /* cyan */
      --brand-3:#22D3EE; /* light cyan */
      --brand-4:#F59E0B; /* amber */
      --bg-1:#050714;
      --bg-2:#0A0F2B;
      --text-1:#E9ECF8;
      --muted:#A4ACB9;
      --card:#0c1333cc;
    }

    html, body, .stApp {
      font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans';
    }

    /* Aurora Backdrop */
    .stApp {
      background:
        radial-gradient(1200px 800px at 10% 5%, rgba(124,58,237,.18), transparent 45%),
        radial-gradient(900px 700px at 90% 0%, rgba(34,211,238,.16), transparent 40%),
        linear-gradient(180deg, var(--bg-1), var(--bg-1));
      color: var(--text-1);
      position: relative;
      overflow-x: hidden;
    }
    .stApp::before,
    .stApp::after{
      content:"";
      position: fixed;
      width: 80vmax;
      height: 80vmax;
      left: -10vmax;
      top: -20vmax;
      z-index: -2;
      background: radial-gradient(circle at 50% 50%,
                  rgba(124,58,237,.25), rgba(6,182,212,.15) 40%, transparent 60%);
      filter: blur(45px) saturate(140%);
      animation: floaty 26s ease-in-out infinite alternate;
      pointer-events: none;
    }
    .stApp::after{
      left: auto;
      right: -10vmax;
      top: 10vmax;
      background: radial-gradient(circle at 50% 50%,
                  rgba(34,211,238,.15), rgba(245,158,11,.12) 40%, transparent 60%);
      animation-duration: 34s;
    }
    @keyframes floaty {
      0%   { transform: translate3d(0,0,0) rotate(0deg) scale(1); }
      100% { transform: translate3d(3vmax,2vmax,0) rotate(8deg) scale(1.06); }
    }

    /* Container & Scrollbar */
    .block-container { max-width: 1200px; padding-top: 1.25rem; padding-bottom: 4rem; }
    ::-webkit-scrollbar{ width: 10px; height: 10px }
    ::-webkit-scrollbar-thumb{ background: linear-gradient(180deg, var(--brand-2), var(--brand-1)); border-radius: 10px }
    ::-webkit-scrollbar-track{ background: rgba(255,255,255,0.05) }

    /* Hero */
    .hero{
      position: relative;
      padding: 22px 22px;
      border-radius: 20px;
      background: linear-gradient(135deg, rgba(124,58,237,.18), rgba(6,182,212,.12));
      border: 1px solid rgba(255,255,255,.08);
      box-shadow: 0 30px 80px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.06);
      overflow: hidden;
    }
    .hero .glow{
      position:absolute; inset:-2px;
      background: conic-gradient(from 180deg, rgba(124,58,237,.25), rgba(6,182,212,.25), rgba(245,158,11,.15), rgba(124,58,237,.25));
      filter: blur(30px) saturate(160%);
      opacity:.35; z-index:-1;
      animation: hue 16s linear infinite;
    }
    @keyframes hue{ to{ filter:hue-rotate(360deg) blur(30px) saturate(160%);} }
    .hero h1{
      margin: 0 0 .25rem 0;
      font-weight: 800;
      font-size: clamp(26px, 4vw, 40px);
      letter-spacing: .2px;
      background: linear-gradient(90deg, #fff, #b9c2ff 40%, #c5fff5 70%, #fff);
      -webkit-background-clip: text; background-clip: text; color: transparent;
      background-size: 200% 100%;
      animation: shimmer 9s linear infinite;
    }
    .hero p{ margin:.25rem 0 0 0; color: var(--muted) }
    @keyframes shimmer{ 0%{background-position:0% 0} 100%{background-position:200% 0} }

    /* Glass cards & KPI */
    .glass{
      background: rgba(12,19,51,.68);
      border: 1px solid rgba(255,255,255,.06);
      border-radius: 18px;
      padding: 16px;
      box-shadow: 0 20px 60px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.06);
      backdrop-filter: blur(10px);
    }
    .metric-card{
      background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02));
      border: 1px solid rgba(255,255,255,.08);
      border-radius: 16px;
      padding: 14px 16px;
      box-shadow: 0 16px 40px rgba(0,0,0,.30);
      position: relative;
    }
    .metric-card::before{
      content:""; position:absolute; inset:-1px;
      border-radius: 16px;
      background: linear-gradient(135deg, rgba(124,58,237,.35), rgba(6,182,212,.22));
      filter: blur(12px); opacity:.25; z-index:-1;
    }

    /* Tabs, Buttons, Inputs */
    .stTabs [role="tablist"]{ gap:.5rem; }
    .stTabs [role="tab"]{
      padding: .5rem 1rem; border-radius: 12px;
      background: rgba(14,20,48,.7);
      border: 1px solid rgba(255,255,255,.06);
    }
    .stTabs [aria-selected="true"]{
      background: linear-gradient(180deg, rgba(124,58,237,.22), rgba(6,182,212,.14));
      border: 1px solid rgba(124,58,237,.5);
      box-shadow: 0 10px 30px rgba(124,58,237,.25);
    }

    .stButton>button{
      position: relative;
      border-radius: 14px;
      border: 1px solid rgba(255,255,255,.10);
      padding: .6rem 1rem;
      font-weight: 600;
      background: linear-gradient(180deg, rgba(124,58,237,.30), rgba(124,58,237,.20));
      color: #fff;
      box-shadow: 0 10px 30px rgba(124,58,237,.25);
      transition: transform .12s ease, filter .12s ease, box-shadow .2s ease;
    }
    .stButton>button:hover{
      transform: translateY(-1px);
      filter: brightness(1.05);
      box-shadow: 0 14px 40px rgba(124,58,237,.35);
    }

    .stTextInput input, .stNumberInput input, .stDateInput input, textarea, .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"]>div{
      background: rgba(8,12,30,.70) !important;
      border-radius: 12px !important;
      border: 1px solid rgba(255,255,255,.10) !important;
      color: var(--text-1) !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"]{
      background: linear-gradient(180deg, rgba(12,19,51,.72), rgba(12,19,51,.58)) !important;
      border-right: 1px solid rgba(255,255,255,.06);
      box-shadow: 10px 0 40px rgba(0,0,0,.35);
    }

    /* Alerts & Tables */
    .stAlert{ border-radius: 14px; border: 1px solid rgba(255,255,255,.08); }
    .stAlert div[role="alert"]{ backdrop-filter: blur(6px); }
    .stDataFrame, .stTable{ border-radius: 12px; overflow: hidden; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def hero(title: str, subtitle: str = ""):
    st.markdown(f'''
        <div class="hero">
          <div class="glow"></div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
    ''', unsafe_allow_html=True)


def kpi_row(items):
    """items: list of tuples -> (label:str, value:str, help:str)"""
    cols = st.columns(len(items))
    for i, (label, value, helptext) in enumerate(items):
        with cols[i]:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(label, value, help=helptext)
            st.markdown('</div>', unsafe_allow_html=True)


@contextmanager
def section_card():
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    try:
        yield
    finally:
        st.markdown('</div>', unsafe_allow_html=True)

