# streamlit_app.py
# Complete fixed version - dark theme, all tabs, low stock alerts, summaries, reconciliation
# Fixed KeyError on empty history / missing columns - Jan 17, 2026

import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import io

# ── Page config & polished dark theme ────────────────────────────────────────
st.set_page_config(page_title="Luke's Ledger 🌿", page_icon="🌿", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background: #0f121a; color: #e0e0ff; }
    section[data-testid="stSidebar"] { background: #0a0d14 !important; }
    .stButton > button { background: #2e7d32; color: white; border-radius: 10px; padding: 12px 24px; font-weight: 600; }
    .stButton > button:hover { background: #1b5e20; }
    .stTabs [data-baseweb="tab-list"] { background: #161b22; border-radius: 12px; padding: 6px; }
    .stTabs [aria-selected="true"] { background: #2e7d32 !important; color: white !important; }
    .alert-red { color: #ff5252; font-weight: bold; }
    .alert-orange { color: #ffb74d; font-weight: bold; }
    hr { border-color: #2a334a; }
    input, select { background: #1e2230 !important; color: white !important; border: 1px solid #2a334a !important; border-radius: 10px !important; }
    </style>
""", unsafe_allow_html=True)

DATA_FILE = "ledger_data.json"
OZ_TO_G = 28.3495

# Low stock thresholds (grams)
TOTAL_LOW = 50.0
VAULT_LOW = 20.0
LOCATION_LOW = 10.0

# ── Load / Initialize data ───────────────────────────────────────────────────
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

# ── Helper functions ─────────────────────────────────────────────────────────
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

def add_transaction(desc, changes, cost_change=0.0, revenue=0.0, cogs=0.0, notes="", adjustment=False):
    now = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    gross_profit = round(revenue - cogs, 2)
    entry = {
        "Date": now,
        "Description": desc + (" [ADJUSTMENT]" if adjustment else ""),
        "Notes": notes,
        **{k.capitalize() + " Δ (g)": v for k, v in changes.items() if k in ["vault", "will", "luke"]},
        "Total Stock (g)": total_stock_g(),
        "Avg $/g": round(ledger["avg_cost_per_g"], 4),
        "Inv Value ($)": inventory_value(),
        "Cash After ($)": round(ledger["cash"], 2),
        "Revenue ($)": revenue,          # always included
        "COGS ($)": cogs,
        "Profit ($)": gross_profit
    }
    if cost_change:
        entry["Cost Added ($)"] = cost_change
    st.session_state.history.insert(0, entry)
    save_data()

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({"ledger": ledger, "history": st.session_state.history}, f, indent=4)

def get_df_history():
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        df['Date'] = pd.to_datetime(df['Date'], format="%Y-%m-%d %I:%M %p", errors='coerce')
        return df
    return pd.DataFrame()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🌿 Luke's Ledger")
    st.session_state.display_unit = st.radio("Display weights in", ["grams", "ounces"], horizontal=True)
    st.metric("Cash Balance", f"${ledger['cash']:,.2f}")
    st.metric("Team Size", ledger["employees"])

# ── Low Stock Alerts ─────────────────────────────────────────────────────────
st.title("📊 Ledger Dashboard")

total_g = total_stock_g()
vault_g = ledger["vault_g"]
will_g = ledger["will_g"]
luke_g = ledger["luke_g"]

alerts = []
if total_g < TOTAL_LOW:
    alerts.append(f"**Total stock low**: {g_to_display(total_g):.2f} — Replenish soon!")
if vault_g < VAULT_LOW:
    alerts.append(f"**Vault low**: {g_to_display(vault_g):.2f} — Secure backup critical!")
if min(vault_g, will_g, luke_g) < LOCATION_LOW:
    alerts.append("**Critical low in one or more locations** — Check now!")

if alerts:
    for msg in alerts:
        st.markdown(f"<p class='alert-red'>{msg}</p>", unsafe_allow_html=True)
    st.warning("Low stock alert — take action!")

# Main metrics
cols = st.columns(4)
cols[0].metric("Total Stock", f"{g_to_display(total_g):.2f}")
cols[1].metric("Inventory Value", f"${inventory_value():,.2f}")
cols[2].metric("Total Revenue", f"${ledger['total_revenue']:,.2f}")
cols[3].metric("Gross Profit", f"${ledger['total_gross_profit']:,.2f}", delta=f"{profit_margin():.1f}%")

st.divider()

# ── Safe Daily/Weekly Summaries (this fixes the KeyError) ────────────────────
st.subheader("Quick Performance Summary")

df_hist = get_df_history()

if df_hist.empty:
    st.info("No transactions yet — summaries will appear after you add or sell stock.")
else:
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)

    today_df = df_hist[df_hist['Date'].dt.date == today]
    week_df = df_hist[df_hist['Date'].dt.date >= week_ago]

    # Safe column access with default 0
    today_rev = today_df.get('Revenue ($)', pd.Series(0)).sum()
    today_profit = today_df.get('Profit ($)', pd.Series(0)).sum()
    week_rev = week_df.get('Revenue ($)', pd.Series(0)).sum()
    week_profit = week_df.get('Profit ($)', pd.Series(0)).sum()

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Today's Revenue", f"${today_rev:,.2f}")
    s2.metric("Today's Profit", f"${today_profit:,.2f}")
    s3.metric("This Week Revenue", f"${week_rev:,.2f}")
    s4.metric("This Week Profit", f"${week_profit:,.2f}")

st.divider()

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📥 Receive", "📤 Sell", "↔ Move", "💰 Adjustments", "🔍 Reconcile"])

with tab1:
    st.subheader("Receive Stock")
    col1, col2 = st.columns([3,1])
    add_amt = col1.number_input("Amount", min_value=0.0, step=0.1)
    add_unit = col2.selectbox("Unit", ["grams", "ounces"])
    add_g = display_to_g(add_amt)
    add_loc = st.selectbox("To", ["Vault", "Will", "Luke"])
    add_cost = st.number_input("Cost Paid ($)", min_value=0.0)
    add_notes = st.text_input("Notes")
    if st.button("Add Stock", use_container_width=True) and add_g > 0:
        key = f"{add_loc.lower()}_g"
        old = total_stock_g()
        ledger[key] += add_g
        if add_cost > 0:
            new = total_stock_g()
            ledger["avg_cost_per_g"] = (old * ledger["avg_cost_per_g"] + add_cost) / new if new > 0 else 0
        add_transaction(f"Added {add_amt:.2f} {add_unit} to {add_loc}", {add_loc.lower(): add_g}, cost_change=add_cost, notes=add_notes)
        st.success("Added!")

with tab2:
    st.subheader("Sell Stock")
    col1, col2 = st.columns([3,1])
    sell_amt = col1.number_input("Amount sold", min_value=0.0, step=0.1)
    sell_unit = col2.selectbox("Unit", ["grams", "ounces"], key="sell_unit")
    sell_g = display_to_g(sell_amt)
    sell_loc = st.selectbox("From", ["Vault", "Will", "Luke"])
    sell_cash = st.number_input("Cash Received ($)", min_value=0.0)
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
            st.success(f"Sold! Profit: ${sell_cash - cogs:,.2f}")
        else:
            st.error("Not enough stock!")

with tab3:
    st.subheader("Move Stock")
    col1, col2, col3 = st.columns(3)
    from_loc = col1.selectbox("From", ["Vault", "Will", "Luke"])
    to_loc = col2.selectbox("To", ["Vault", "Will", "Luke"])
    move_amt = col3.number_input("Amount", min_value=0.0, step=0.1)
    move_unit = st.selectbox("Unit", ["grams", "ounces"], key="move_unit")
    move_g = display_to_g(move_amt)
    if st.button("Move", use_container_width=True) and move_g > 0 and from_loc != to_loc:
        from_key = f"{from_loc.lower()}_g"
        to_key = f"{to_loc.lower()}_g"
        if ledger[from_key] >= move_g:
            ledger[from_key] -= move_g
            ledger[to_key] += move_g
            add_transaction(f"Moved {move_amt:.2f} {move_unit} {from_loc} → {to_loc}", {from_loc.lower(): -move_g, to_loc.lower(): move_g})
            st.success("Moved!")
        else:
            st.error("Not enough in source!")

with tab4:
    st.subheader("Adjust Cash / Team")
    new_cash = st.number_input("New Cash ($)", value=ledger["cash"], step=1.0)
    new_emp = st.number_input("New Employees", value=ledger["employees"], step=1, min_value=0)
    if st.button("Update", use_container_width=True):
        delta_cash = new_cash - ledger["cash"]
        delta_emp = new_emp - ledger["employees"]
        ledger["cash"] = new_cash
        ledger["employees"] = new_emp
        changes = {}
        if delta_cash != 0: changes["cash"] = delta_cash
        if delta_emp != 0: changes["employees"] = delta_emp
        if changes:
            add_transaction("Manual adjustment", changes)
        st.success("Updated!")

with tab5:
    st.subheader("Physical Reconciliation")
    st.info("Enter actual counts to compare and adjust.")
    recon_vault = st.number_input("Actual Vault (g)", value=vault_g, step=0.1)
    recon_will = st.number_input("Actual Will (g)", value=will_g, step=0.1)
    recon_luke = st.number_input("Actual Luke (g)", value=luke_g, step=0.1)
    recon_reason = st.text_input("Reason for difference", placeholder="e.g., spillage, error")
    if st.button("Reconcile", use_container_width=True):
        delta_v = recon_vault - vault_g
        delta_w = recon_will - will_g
        delta_l = recon_luke - luke_g
        changes = {}
        if delta_v != 0: changes["vault"] = delta_v; ledger["vault_g"] = recon_vault
        if delta_w != 0: changes["will"] = delta_w; ledger["will_g"] = recon_will
        if delta_l != 0: changes["luke"] = delta_l; ledger["luke_g"] = recon_luke
        if changes:
            add_transaction(f"Reconciliation: V{delta_v:+.2f} W{delta_w:+.2f} L{delta_l:+.2f}", changes, notes=recon_reason, adjustment=True)
            st.success("Reconciled!")
        else:
            st.info("No changes needed.")

# ── History & Export ─────────────────────────────────────────────────────────
st.divider()
with st.expander("📜 History"):
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        csv = io.StringIO()
        df.to_csv(csv, index=False)
        st.download_button("Export CSV", csv.getvalue(), "ledger_history.csv", "text/csv")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions yet.")

save_data()