# ledger_app_polished_complete.py
# Full working version - all tabs with inputs - dark theme - Jan 17, 2026

import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
import io

# Page config
st.set_page_config(
    page_title="Luke's Ledger 🌿",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for smooth dark theme
st.markdown("""
    <style>
    .stApp { background: #0f121a; color: #e0e0ff; }
    section[data-testid="stSidebar"] { background: #0a0d14 !important; }
    .stButton > button { background: #2e7d32; color: white; border-radius: 10px; padding: 12px 24px; font-weight: 600; }
    .stButton > button:hover { background: #1b5e20; }
    .stTabs [data-baseweb="tab-list"] { background: #161b22; border-radius: 12px; padding: 6px; }
    .stTabs [data-baseweb="tab"] { color: #b0b0ff !important; border-radius: 8px; }
    .stTabs [aria-selected="true"] { background: #2e7d32 !important; color: white !important; }
    .metric-card { background: #1a1f2e; border-radius: 16px; padding: 20px; border: 1px solid #2a334a; }
    hr { border-color: #2a334a; }
    input, select { background: #1e2230 !important; color: white !important; border: 1px solid #2a334a !important; border-radius: 10px !important; }
    </style>
""", unsafe_allow_html=True)

DATA_FILE = "ledger_data.json"
OZ_TO_G = 28.3495

# Load data
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

# Helpers
def g_to_display(g):
    return g / OZ_TO_G if st.session_state.get("display_unit", "grams") == "ounces" else g

def display_to_g(v):
    return v * OZ_TO_G if st.session_state.get("display_unit", "grams") == "ounces" else v

def total_stock_g():
    return ledger["vault_g"] + ledger["will_g"] + ledger["luke_g"]

def inventory_value():
    return round(total_stock_g() * ledger["avg_cost_per_g"], 2)

def profit_margin():
    return round(ledger["total_gross_profit"] / ledger["total_revenue"] * 100, 1) if ledger["total_revenue"] > 0 else 0.0

def add_transaction(desc, changes, cost_change=0.0, revenue=0.0, cogs=0.0, notes=""):
    now = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    gross_profit = round(revenue - cogs, 2)
    entry = {
        "Date": now,
        "Description": desc,
        "Notes": notes,
        **{k.capitalize() + " Δ (g)": v for k, v in changes.items() if k in ["vault", "will", "luke"]},
        "Total Stock (g)": total_stock_g(),
        "Avg $/g": round(ledger["avg_cost_per_g"], 4),
        "Inv Value ($)": inventory_value(),
        "Cash After ($)": round(ledger["cash"], 2),
        "Revenue ($)": revenue,
        "COGS ($)": cogs,
        "Profit ($)": gross_profit
    }
    if cost_change: entry["Cost Added ($)"] = cost_change
    st.session_state.history.insert(0, entry)
    with open(DATA_FILE, "w") as f:
        json.dump({"ledger": ledger, "history": st.session_state.history}, f, indent=4)

# Sidebar
with st.sidebar:
    st.title("🌿 Luke's Ledger")
    st.session_state.display_unit = st.radio("Display weights in", ["grams", "ounces"], horizontal=True)
    st.metric("Cash Balance", f"${ledger['cash']:,.2f}")
    st.metric("Team Size", ledger["employees"])
    if st.button("Reset Data", type="secondary"):
        if st.checkbox("Confirm - delete all"):
            if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
            st.session_state.clear()
            st.rerun()

# Dashboard
st.title("📊 Ledger Dashboard")
cols = st.columns(4)
cols[0].metric("Total Stock", f"{g_to_display(total_stock_g()):.2f}")
cols[1].metric("Inventory Value", f"${inventory_value():,.2f}")
cols[2].metric("Total Revenue", f"${ledger['total_revenue']:,.2f}")
cols[3].metric("Gross Profit", f"${ledger['total_gross_profit']:,.2f}", delta=f"{profit_margin():.1f}%")

st.divider()

# Tabs - ALL FULLY IMPLEMENTED
tab1, tab2, tab3, tab4 = st.tabs(["📥 Receive Stock", "📤 Sell Stock", "↔ Move Stock", "💰 Cash / Team"])

with tab1:
    st.subheader("Receive / Add Stock")
    col1, col2 = st.columns([3, 1])
    add_amt = col1.number_input("Amount to add", min_value=0.0, step=0.1, value=0.0)
    add_unit = col2.selectbox("Unit", ["grams", "ounces"])
    add_g = display_to_g(add_amt)
    add_loc = st.selectbox("Add to location", ["Vault", "Will", "Luke"])
    add_cost = st.number_input("Cost paid for this ($)", min_value=0.0, step=1.0)
    add_notes = st.text_input("Batch/Notes (optional)")
    if st.button("Confirm Add", use_container_width=True) and add_g > 0:
        key = f"{add_loc.lower()}_g"
        old_total = total_stock_g()
        ledger[key] += add_g
        if add_cost > 0:
            new_total = total_stock_g()
            prev_cost = old_total * ledger["avg_cost_per_g"]
            ledger["avg_cost_per_g"] = (prev_cost + add_cost) / new_total if new_total > 0 else 0
        add_transaction(f"Added {add_amt:.2f} {add_unit} to {add_loc}", {add_loc.lower(): add_g}, cost_change=add_cost, notes=add_notes)
        st.success("Stock added successfully!")

with tab2:
    st.subheader("Sell / Remove Stock")
    col1, col2 = st.columns([3, 1])
    sell_amt = col1.number_input("Amount sold", min_value=0.0, step=0.1, value=0.0)
    sell_unit = col2.selectbox("Unit", ["grams", "ounces"], key="sell_u")
    sell_g = display_to_g(sell_amt)
    sell_loc = st.selectbox("From location", ["Vault", "Will", "Luke"])
    sell_cash = st.number_input("Cash received ($)", min_value=0.0, step=1.0)
    if st.button("Confirm Sale", use_container_width=True) and sell_g > 0:
        key = f"{sell_loc.lower()}_g"
        if ledger[key] >= sell_g:
            cogs = round(sell_g * ledger["avg_cost_per_g"], 2)
            ledger[key] -= sell_g
            ledger["cash"] += sell_cash
            ledger["total_revenue"] += sell_cash
            ledger["total_cogs"] += cogs
            ledger["total_gross_profit"] += (sell_cash - cogs)
            add_transaction(f"Sold {sell_amt:.2f} {sell_unit} from {sell_loc}", {sell_loc.lower(): -sell_g}, revenue=sell_cash, cogs=cogs)
            st.success(f"Sale recorded! Profit: ${sell_cash - cogs:,.2f}")
        else:
            st.error("Not enough stock!")

with tab3:
    st.subheader("Move Stock Between Locations")
    col1, col2, col3 = st.columns(3)
    from_loc = col1.selectbox("From", ["Vault", "Will", "Luke"])
    to_loc = col2.selectbox("To", ["Vault", "Will", "Luke"])
    move_amt = col3.number_input("Amount", min_value=0.0, step=0.1, value=0.0)
    move_unit = st.selectbox("Unit", ["grams", "ounces"], key="move_u")
    move_g = display_to_g(move_amt)
    if st.button("Confirm Move", use_container_width=True) and move_g > 0 and from_loc != to_loc:
        from_key = f"{from_loc.lower()}_g"
        to_key = f"{to_loc.lower()}_g"
        if ledger[from_key] >= move_g:
            ledger[from_key] -= move_g
            ledger[to_key] += move_g
            add_transaction(f"Moved {move_amt:.2f} {move_unit} {from_loc} → {to_loc}", {from_loc.lower(): -move_g, to_loc.lower(): move_g})
            st.success("Moved successfully!")
        else:
            st.error("Not enough in source location!")

with tab4:
    st.subheader("Adjust Cash / Employees")
    new_cash = st.number_input("New Cash Balance ($)", value=ledger["cash"], step=1.0)
    new_emp = st.number_input("New Employee Count", value=ledger["employees"], step=1, min_value=0)
    if st.button("Update Values", use_container_width=True):
        delta_cash = new_cash - ledger["cash"]
        delta_emp = new_emp - ledger["employees"]
        ledger["cash"] = new_cash
        ledger["employees"] = new_emp
        changes = {}
        if delta_cash != 0: changes["cash"] = delta_cash
        if delta_emp != 0: changes["employees"] = delta_emp
        if changes:
            add_transaction("Manual adjustment", changes)
        st.success("Values updated!")

# History
st.divider()
with st.expander("📜 Transaction History"):
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        csv = io.StringIO()
        df.to_csv(csv, index=False)
        st.download_button("Export CSV", csv.getvalue(), file_name="ledger_history.csv", mime="text/csv")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions yet.")

# Auto-save
with open(DATA_FILE, "w") as f:
    json.dump({"ledger": ledger, "history": st.session_state.history}, f, indent=4)