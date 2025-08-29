# ui/sidebar.py
import re
import streamlit as st
import pandas as pd
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

# =================== CONSTANTS ===================
MAX_AMOUNT_DEC = Decimal("999999999999.9999999999")   # manual max (12 digits + 10 decimals)
SLIDER_MIN = 0.0
SLIDER_MAX = 100_000.0
SLIDER_STEP = 10_000.0

DEFAULT_CATEGORIES = [
    "Income", "Groceries", "Utilities", "Transport", "Investment", "Rent",
    "Dining", "Shopping", "Healthcare", "Education", "Other"
]

# =================== STATE HELPERS ===================
def _ensure_state():
    if "projects" not in st.session_state:
        st.session_state.projects = {
            "Default": pd.DataFrame(columns=["date", "category", "amount", "note"])
        }
    if "selected_project" not in st.session_state:
        st.session_state.selected_project = next(iter(st.session_state.projects.keys()))
    if "last_project" not in st.session_state:
        st.session_state.last_project = st.session_state.selected_project

def _parse_date(val) -> date:
    if isinstance(val, date):
        return val
    s = str(val)
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d").date()
        except Exception:
            return datetime.today().date()

# =================== AMOUNT PARSING ===================
_amount_sanitize_re = re.compile(r"[^\d\.]")  # keep digits and dot

def _normalize_amount_text(text: str) -> str:
    """
    Accepts '₹12,000.50', 'INR 15000', '12,000', '15 000.25' -> '12000.50'.
    """
    if not text:
        return ""
    t = str(text).strip()
    t = (t.replace(",", " ")
           .replace("\u00A0", " ")
           .replace("INR", "")
           .replace("inr", "")
           .replace("Rs.", "")
           .replace("Rs", "")
           .replace("rs", "")
           .replace("रु", "")
           .replace("₹", ""))
    t = _amount_sanitize_re.sub("", t)
    if t.count(".") > 1:
        head, *rest = t.split(".")
        t = head + "." + "".join(rest)
    return t.strip()

def _decimal_from_text(text: str) -> Decimal | None:
    norm = _normalize_amount_text(text)
    if norm == "":
        return None
    try:
        d = Decimal(norm)
    except (InvalidOperation, ValueError):
        return None
    if d < 0 or d > MAX_AMOUNT_DEC:
        return None
    # cap to <= 10 decimals
    q = Decimal("0.0000000001")
    return d.quantize(q) if d.as_tuple().exponent < -10 else d

# =================== DATA GUARANTEES ===================
def _force_numeric(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    return df

def _append_transaction(df: pd.DataFrame, dt, category, amount_dec: Decimal, note: str) -> pd.DataFrame:
    row = {
        "date": str(dt),
        "category": category,
        "amount": float(amount_dec),  # numeric for aggregations
        "note": (note or "").strip(),
    }
    return _force_numeric(pd.concat([df, pd.DataFrame([row])], ignore_index=True))

def _update_transaction(df: pd.DataFrame, idx: int, dt, category, amount_dec: Decimal, note: str) -> pd.DataFrame:
    df = df.copy()
    df.loc[idx, "date"] = str(dt)
    df.loc[idx, "category"] = category
    df.loc[idx, "amount"] = float(amount_dec)
    df.loc[idx, "note"] = (note or "").strip()
    return _force_numeric(df)

def _rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass

# =================== FIELD CLEAR HELPERS ===================
def _clear_add_fields():
    for k in ["add_date", "add_cat", "add_note", "add_amount_text", "add_amount_slider", "add_amount_mode"]:
        if k in st.session_state:
            del st.session_state[k]

def _clear_edit_fields():
    for k in ["edit_date", "edit_cat", "edit_note", "edit_amount_text", "edit_amount_slider", "edit_amount_mode"]:
        if k in st.session_state:
            del st.session_state[k]

# =================== AMOUNT UI (NO FORMS) ===================
def amount_block(prefix: str, default_val: Decimal) -> Decimal | None:
    """
    Render amount UI with two modes (slider/manual). Returns Decimal or None if invalid.
    NO forms used, so values are read directly from st.session_state.
    """
    st.markdown("**Amount**")

    mode_key = f"{prefix}_amount_mode"
    slider_key = f"{prefix}_amount_slider"
    text_key = f"{prefix}_amount_text"

    # Persist mode choice
    if mode_key not in st.session_state:
        st.session_state[mode_key] = "Use slider (bar)"

    st.radio(
        "Choose input method",
        ["Use slider (bar)", "Type exact value"],
        key=mode_key,
        horizontal=True,
    )

    if st.session_state[mode_key] == "Use slider (bar)":
        start_val = float(default_val or 0)
        start_val = max(SLIDER_MIN, min(start_val, SLIDER_MAX))
        st.slider(
            "Slide to set amount",
            min_value=SLIDER_MIN,
            max_value=SLIDER_MAX,
            value=start_val,
            step=SLIDER_STEP,
            help="Bar increases/decreases in ₹10,000 steps (0 → 100,000).",
            key=slider_key,
        )
        val_f = float(st.session_state.get(slider_key, start_val))
        return Decimal(str(val_f)).quantize(Decimal("0.0000000001"))

    # Manual
    st.text_input(
        "Enter exact amount (up to 999999999999.9999999999)",
        value=f"{default_val}",
        placeholder="e.g., ₹12,000.50 or 12345.6789",
        key=text_key,
        help="Paste values like '₹12,000.50' or 'INR 15000'.",
    )
    return _decimal_from_text(st.session_state.get(text_key, f"{default_val}"))

# =================== MAIN SIDEBAR ===================
def render_sidebar():
    """Renders the sidebar for project and data management."""
    _ensure_state()

    with st.sidebar:
        st.header("Project Management")

        # --- Project selection ---
        project_options = list(st.session_state.projects.keys())
        try:
            selected_index = project_options.index(st.session_state.selected_project)
        except Exception:
            selected_index = 0

        st.session_state.selected_project = st.selectbox(
            "Current Project",
            project_options,
            index=selected_index,
            placeholder="Select or create a project",
        )

        # Reset volatile state if project changes
        if st.session_state.last_project != st.session_state.selected_project:
            st.session_state.last_project = st.session_state.selected_project
            _clear_add_fields()
            _clear_edit_fields()
            if "messages" in st.session_state:
                st.session_state.messages = []

        # --- Create new project (no form) ---
        with st.expander("➕ New Project", expanded=False):
            name = st.text_input("Project name", key="new_project_name")
            if st.button("Create", use_container_width=True):
                name = (name or "").strip()
                if name and name not in st.session_state.projects:
                    st.session_state.projects[name] = pd.DataFrame(columns=["date", "category", "amount", "note"])
                    st.session_state.selected_project = name
                    st.success(f"Project '{name}' created.")
                    _rerun()
                else:
                    st.error("Name cannot be empty or already exist.")

        st.divider()

        # --- Transactions ---
        proj = st.session_state.selected_project
        if not proj:
            return

        st.subheader("Transactions")
        df = _force_numeric(st.session_state.projects[proj])

        # ========== ADD TRANSACTION (NO FORMS) ==========
        with st.expander("➕ Add Transaction", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                add_date = st.date_input("Date", value=datetime.today().date(), key="add_date")
            with c2:
                add_cat = st.selectbox("Category", DEFAULT_CATEGORIES, index=0, key="add_cat")

            add_amount = amount_block("add", default_val=Decimal("0"))
            add_note = st.text_input("Note (optional)", key="add_note")

            if st.button("Add", type="primary", use_container_width=True):
                if add_amount is None:
                    st.error("Please enter a valid amount (up to 999999999999.9999999999).")
                else:
                    st.session_state.projects[proj] = _append_transaction(
                        df, add_date, add_cat, add_amount, add_note
                    )
                    st.success(f"Added ₹{float(add_amount):,.2f}")
                    _clear_add_fields()
                    _rerun()

        # ========== EDIT / DELETE (NO FORMS) ==========
        if not df.empty:
            with st.expander("✏️ Edit / Delete Transaction", expanded=False):
                # Selection
                choices = []
                for idx, row in df.reset_index().iterrows():
                    ridx = int(row["index"])
                    label = f"{ridx}: {row['date']} • {row['category']} • ₹{row['amount']:.2f} • {(str(row.get('note',''))[:24])}"
                    choices.append((ridx, label))

                selected_idx = st.selectbox(
                    "Pick a transaction",
                    options=[c[0] for c in choices],
                    format_func=lambda k: dict(choices).get(k, str(k)),
                    key="edit_row_idx",
                )

                cur = df.loc[selected_idx]
                e1, e2 = st.columns(2)
                with e1:
                    edit_date = st.date_input("Date", value=_parse_date(cur["date"]), key="edit_date")
                with e2:
                    edit_cat = st.selectbox(
                        "Category",
                        DEFAULT_CATEGORIES,
                        index=DEFAULT_CATEGORIES.index(cur["category"]) if cur["category"] in DEFAULT_CATEGORIES else 0,
                        key="edit_cat",
                    )

                edit_amount = amount_block("edit", default_val=Decimal(str(cur["amount"])))
                edit_note = st.text_input("Note (optional)", value=str(cur.get("note", "")), key="edit_note")

                c3, c4 = st.columns(2)
                with c3:
                    if st.button("Save Changes", use_container_width=True):
                        if edit_amount is None:
                            st.error("Please enter a valid amount (up to 999999999999.9999999999).")
                        else:
                            new_df = _update_transaction(df, selected_idx, edit_date, edit_cat, edit_amount, edit_note)
                            st.session_state.projects[proj] = new_df
                            st.success(f"Updated to ₹{float(edit_amount):,.2f}")
                            _clear_edit_fields()
                            _rerun()
                with c4:
                    if st.button("Delete", use_container_width=True):
                        new_df = df.drop(index=selected_idx).reset_index(drop=True)
                        st.session_state.projects[proj] = _force_numeric(new_df)
                        st.success("Transaction deleted.")
                        _clear_edit_fields()
                        _rerun()

        # Show data (latest first)
        df = _force_numeric(st.session_state.projects[proj])
        st.dataframe(
            df.sort_values(by="date", ascending=False),
            hide_index=True,
            use_container_width=True,
        )





