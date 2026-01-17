# ledger_app_smooth_ui.py
# Enhanced smooth UI version - dark mode ready, sidebar, better metrics & layout

import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
import io

# ── Page config for better mobile/desktop feel ───────────────────────────────
st.set_page_config(
    page_title="Luke's Ledger Pro",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Dark mode + theme tweaks (Streamlit 1.28+ supports this well) ────────────
st.markdown("""
    <style>
    /* Main accent color - green for cannabis vibe */
    :root {
        --primary: #4CAF50;
        --primary-dark: #388E3C;
        --bg-dark: #0E1117;
        --text: #FAFAFA;
    }
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .stButton > button {
        background-color: var(--primary);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: var(--primary-dark);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #161B22;
        border-radius: 8px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #FAFAFA !important;
        border-radius: 6px;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--primary) !important;
        color: white !important;
    }
    h1, h2, h3 { color: #4CAF50; }
    .stMetric { background: #1E1E2E; border-radius: 12px; padding: 16px; }
    hr { border-color: #333; }
    </style>
""", unsafe_allow_html=True)

DATA_FILE = "ledger_data.json"
OZ_TO_G = 28.3495

# ── Load data (same as before) ───────────────────────────────────────────────
if "ledger" not in st.session_state:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            loaded = json.load(f)
            st.session_state.ledger = loaded.get("ledger", {
                "vault_g": 0.0, "will_g": 0.0, "luke_g": 0.0,
                "avg_cost_per_g": 0.0, "cash": 0.0, "employees": 2,
                "total_revenue": 0.0, "total_cogs": 0.0, "total_gross_profit": 0.0
            })
            st.session_state.history = loaded.get("history", [])
    else:
        st.session_state.ledger = {
            "vault_g": 0.0, "will_g": 0.0, "luke_g": 0.0,
            "avg_cost_per_g": 0.0, "cash": 0.0, "employees": 2,
            "total_revenue": 0.0, "total_cogs": 0.0, "total_gross_profit": 0.0
        }
        st.session_state.history = []

ledger = st.session_state.ledger

# ── Helpers (unchanged) ──────────────────────────────────────────────────────
def g_to_display(g):
    unit = st.session_state.get("display_unit", "grams")
    return g / OZ_TO_G if unit == "ounces" else g

def display_to_g(value):
    unit = st.session_state.get("display_unit", "grams")
    return value * OZ_TO_G if unit == "ounces" else value

def total_stock_g():
    return ledger["vault_g"] + ledger["will_g"] + ledger["luke_g"]

def inventory_value():
    return round(total_stock_g() * ledger["avg_cost_per_g"], 2)

def gross_profit_margin():
    return round((ledger["total_gross_profit"] / ledger["total_revenue"] * 100), 1) if ledger["total_revenue"] > 0 else 0.0

def add_transaction(desc, changes, cost_change=0.0, revenue=0.0, cogs=0.0, notes=""):
    now = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    gross_profit = round(revenue - cogs, 2)
    entry = {
        "Date": now, "Description": desc, "Notes": notes.strip() if notes else "",
        "Vault Δ (g)": changes.get("vault", 0.0), "Will Δ (g)": changes.get("will", 0.0), "Luke Δ (g)": changes.get("luke", 0.0),
        "Total Stock After (g)": total_stock_g(), "Avg $/g After": round(ledger["avg_cost_per_g"], 4),
        "Inventory Value After (\( )": inventory_value(), "Cash Δ ( \))": changes.get("cash", 0.0),
        "Cash After (\( )": round(ledger["cash"], 2), "Revenue This Tx ( \))": revenue,
        "COGS This Tx (\( )": cogs, "Gross Profit This Tx ( \))": gross_profit,
        "Employees Δ": changes.get("employees", 0),
    }
    if cost_change != 0: entry["Cost Added ($)"] = cost_change
    st.session_state.history.insert(0, entry)
    save_data()

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({"ledger": ledger, "history": st.session_state.history}, f, indent=4)

# ── Sidebar for global settings ──────────────────────────────────────────────
with st.sidebar:
    st.title("🌿 Luke's Ledger")
    st.session_state.display_unit = st.radio("Weight Unit", ["grams", "ounces"], horizontal=True)
    st.markdown("---")
    st.caption("Bloomington, MN • Jan 2026")
    if st.button("Reset App Data", type="secondary"):
        if st.checkbox("I'm sure - delete everything"):
            if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
            st.session_state.clear()
            st.rerun()

# ── Main Dashboard ───────────────────────────────────────────────────────────
st.title("📊 Ledger Dashboard")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Stock", f"{g_to_display(total_stock_g()):.2f} {'g' if st.session_state.display_unit == 'grams' else 'oz'}", 
            delta=None, delta_color="normal")
col2.metric("Inventory Value", f"${inventory_value():,.2f}", 
            delta=f"{ledger['avg_cost_per_g']:.4f}/g avg")
col3.metric("Total Revenue", f"${ledger['total_revenue']:,.2f}")
col4.metric("Gross Profit", f"${ledger['total_gross_profit']:,.2f}", 
            delta=f"{gross_profit_margin():.1f}% margin" if gross_profit_margin() > 0 else None)

st.markdown("---")

# ── Quick Actions in Tabs ────────────────────────────────────────────────────
st.subheader("Actions")

tab1, tab2, tab3, tab4 = st.tabs(["📥 Receive", "📤 Sell", "↔ Move", "💰 Cash/Team"])

with tab1:
    st.subheader("Receive / Add Stock")
    col_a, col_b = st.columns([3, 1])
    add_amount_disp = col_a.number_input("Amount", min_value=0.0, step=0.1, value=0.0, key="add_amt")
    add_unit = col_b.selectbox("", ["grams", "ounces"], key="add_u")
    add_amount_g = display_to_g(add_amount_disp)
    
    location_add = st.selectbox("Location", ["Vault", "Will", "Luke"])
    cost_paid = st.number_input("Cost Paid ($)", min_value=0.0, step=1.0, value=0.0)
    notes = st.text_input("Batch Notes", placeholder="Batch # - Strain - Notes")
    
    if st.button("Add Stock", use_container_width=True) and add_amount_g > 0:
        key = {"Vault": "vault_g", "Will": "will_g", "Luke": "luke_g"}[location_add]
        old_total = total_stock_g()
        ledger[key] += add_amount_g
        if cost_paid > 0:
            new_total = total_stock_g()
            total_cost_before = old_total * ledger["avg_cost_per_g"]
            ledger["avg_cost_per_g"] = (total_cost_before + cost_paid) / new_total if new_total > 0 else 0
        add_transaction(f"Added {add_amount_disp:.2f} {add_unit} to {location_add}", 
                        {location_add.lower(): add_amount_g}, cost_change=cost_paid, notes=notes)
        st.success("Stock added!")

# Similar cleanups for other tabs (tab2 sell, tab3 move, tab4 cash/team) - copy structure from previous full code
# For brevity here, paste the full tab contents from your last working version and apply the same styling (larger inputs, primary buttons, etc.)

# ── History + Export (collapsible for smoothness) ────────────────────────────
with st.expander("📜 Transaction History", expanded=False):
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button("📥 Export CSV", csv_buffer.getvalue(), 
                           file_name=f"ledger_{datetime.now().strftime('%Y%m%d')}.csv",
                           mime="text/csv", use_container_width=True)
        
        st.dataframe(df.style.format(precision=2), use_container_width=True)
    else:
        st.info("No transactions yet.")

save_data()