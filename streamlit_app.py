# ledger_app_ultra_polished.py
# Ultra-smooth UI - dark theme, sidebar, responsive, green accents - Jan 2026

import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
import io

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Luke's Ledger 🌿",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS for smooth, premium dark mode look ───────────────────────────
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    .stApp { 
        background: #0f121a; 
        color: #e0e0ff; 
    }
    section[data-testid="stSidebar"] {
        background: #0a0d14 !important;
        border-right: 1px solid #1e2230;
    }
    .stButton > button {
        background: #2e7d32;
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 28px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background: #1b5e20;
        transform: translateY(-2px);
    }
    .stButton > button[kind="secondary"] {
        background: #1e2230;
    }
    h1, h2, h3 { color: #66bb6a; }
    .stTabs [data-baseweb="tab-list"] {
        background: #161b22;
        border-radius: 12px;
        padding: 6px;
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #b0b0ff !important;
        border-radius: 8px;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: #2e7d32 !important;
        color: white !important;
    }
    .metric-card {
        background: #1a1f2e;
        border-radius: 16px;
        padding: 20px 24px;
        border: 1px solid #2a334a;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    hr { border-color: #2a334a; margin: 24px 0; }
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: #1e2230;
        color: white;
        border: 1px solid #2a334a;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

DATA_FILE = "ledger_data.json"
OZ_TO_G = 28.3495

# ── Data loading (unchanged core logic) ──────────────────────────────────────
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

# ── Helper functions (condensed) ─────────────────────────────────────────────
def g_to_display(g): 
    return g / OZ_TO_G if st.session_state.get("display_unit", "grams") == "ounces" else g

def display_to_g(v): 
    return v * OZ_TO_G if st.session_state.get("display_unit", "grams") == "ounces" else v

def total_stock_g(): return ledger["vault_g"] + ledger["will_g"] + ledger["luke_g"]
def inventory_value(): return round(total_stock_g() * ledger["avg_cost_per_g"], 2)
def profit_margin(): 
    return round(ledger["total_gross_profit"] / ledger["total_revenue"] * 100, 1) if ledger["total_revenue"] > 0 else 0.0

def add_transaction(desc, changes, cost_change=0.0, revenue=0.0, cogs=0.0, notes=""):
    now = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    entry = {
        "Date": now, "Description": desc, "Notes": notes.strip(),
        **{f"{k} Δ (g)": v for k, v in changes.items() if k in ["vault", "will", "luke"]},
        "Total Stock (g)": total_stock_g(),
        "Avg $/g": round(ledger["avg_cost_per_g"], 4),
        "Inv Value ($)": inventory_value(),
        **{f"{k} Δ ($)": v for k, v in changes.items() if k == "cash"},
        "Cash ($)": round(ledger["cash"], 2),
        "Revenue (\( )": revenue, "COGS ( \))": cogs,
        "Profit ($)": round(revenue - cogs, 2),
        "Employees Δ": changes.get("employees", 0)
    }
    if cost_change: entry["Cost Added ($)"] = cost_change
    st.session_state.history.insert(0, entry)
    with open(DATA_FILE, "w") as f: json.dump({"ledger": ledger, "history": st.session_state.history}, f, indent=4)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🌿 Luke's Ledger")
    st.caption(f"Bloomington, MN • {datetime.now().strftime('%b %d, %Y')}")
    st.divider()
    
    st.session_state.display_unit = st.radio("Unit", ["grams", "ounces"], horizontal=True)
    
    st.metric("Cash", f"${ledger['cash']:,.2f}", delta_color="normal")
    st.metric("Team", ledger["employees"])
    
    st.divider()
    if st.button("Reset All Data", type="secondary"):
        if st.checkbox("Confirm delete"):
            if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
            st.session_state.clear()
            st.rerun()

# ── Main Content ─────────────────────────────────────────────────────────────
st.title("📊 Operations Dashboard")

# Metrics row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Stock", f"{g_to_display(total_stock_g()):.2f}", border=True)
m2.metric("Inventory Value", f"${inventory_value():,.2f}", border=True)
m3.metric("Revenue", f"${ledger['total_revenue']:,.2f}", border=True)
m4.metric("Gross Profit", f"${ledger['total_gross_profit']:,.2f}", 
          delta=f"{profit_margin():.1f}%" if profit_margin() else None, border=True)

st.divider()

# Action Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📥 Receive", "📤 Sell", "↔ Move", "💰 Adjustments"])

with tab1:
    st.subheader("Receive Stock")
    col1, col2 = st.columns([3,1])
    amt = col1.number_input("Amount", min_value=0.0, step=0.1, value=0.0)
    unit = col2.selectbox("", ["grams", "ounces"])
    amt_g = display_to_g(amt)
    
    loc = st.selectbox("To Location", ["Vault", "Will", "Luke"])
    cost = st.number_input("Cost Paid ($)", min_value=0.0, step=5.0)
    notes = st.text_input("Batch/Notes", placeholder="Batch #45 - Indoor - Supplier X")
    
    if st.button("Confirm Receive", use_container_width=True) and amt_g > 0:
        key = f"{loc.lower()}_g"
        old_total = total_stock_g()
        ledger[key] += amt_g
        if cost > 0:
            new_total = total_stock_g()
            prev_cost = old_total * ledger["avg_cost_per_g"]
            ledger["avg_cost_per_g"] = (prev_cost + cost) / new_total if new_total > 0 else 0
        add_transaction(f"Received {amt:.2f} {unit} → {loc}", {loc.lower(): amt_g}, cost_change=cost, notes=notes)
        st.success("Received successfully!")

# (Add similar clean structure for tab2 Sell, tab3 Move, tab4 Cash/Team from previous versions)

# History section
st.divider()
with st.expander("📜 Full History & Export", expanded=False):
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        st.download_button(
            "📥 Export to CSV", buf.getvalue(),
            file_name=f"ledger_export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv", use_container_width=True
        )
        
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No activity yet — start receiving or selling!")

# Footer
st.markdown("<p style='text-align:center; color:#666; margin-top:40px;'>Luke's Ledger • Built for efficiency • 2026</p>", unsafe_allow_html=True)