# ledger_app_streamlit_with_history.py
# Run with: streamlit run ledger_app_streamlit_with_history.py
# Requires: pip install streamlit pandas

import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

DATA_FILE = "ledger_data.json"

# ── Load or initialize data ──────────────────────────────────────────────────
if "ledger" not in st.session_state:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            loaded = json.load(f)
            st.session_state.ledger = {
                "inventory": loaded.get("inventory", 0),
                "money": loaded.get("money", 0.0),
                "employees": loaded.get("employees", 2),
            }
            st.session_state.history = loaded.get("history", [])
    else:
        st.session_state.ledger = {"inventory": 0, "money": 0.0, "employees": 2}
        st.session_state.history = []

# ── Helper: Add transaction ──────────────────────────────────────────────────
def add_transaction(description, changes):
    now = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    entry = {
        "Date": now,
        "Description": description,
        "Inventory Δ": changes.get("inventory", 0),
        "Money Δ ($)": changes.get("money", 0.0),
        "Employees Δ": changes.get("employees", 0),
        "Inventory After": st.session_state.ledger["inventory"],
        "Money After ($)": round(st.session_state.ledger["money"], 2),
        "Employees After": st.session_state.ledger["employees"],
    }
    st.session_state.history.insert(0, entry)  # newest first
    save_data()

def save_data():
    data = {
        "inventory": st.session_state.ledger["inventory"],
        "money": st.session_state.ledger["money"],
        "employees": st.session_state.ledger["employees"],
        "history": st.session_state.history
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ── UI ───────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Luke's Ledger + History", layout="wide")
st.title("📒 Luke's Ledger Tracker")
st.caption("With full transaction history — Bloomington, MN 🏙️")

# Current Snapshot ────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Inventory", f"{st.session_state.ledger['inventory']:,}")
col2.metric("Cash Balance", f"${st.session_state.ledger['money']:,.2f}")
col3.metric("Team Size", st.session_state.ledger["employees"])

st.divider()

# Quick Actions ───────────────────────────────────
st.subheader("Quick Transactions")

tab1, tab2, tab3 = st.tabs(["Inventory", "Money", "Employees"])

with tab1:
    col_a, col_b = st.columns(2)
    with col_a:
        inv_add = st.number_input("Add to Inventory", min_value=0, step=1, value=0, key="inv_add")
        if st.button("✓ Add Inventory", use_container_width=True):
            if inv_add > 0:
                st.session_state.ledger["inventory"] += inv_add
                add_transaction(f"Added {inv_add} items", {"inventory": inv_add})
                st.success(f"Added {inv_add} to inventory!")
    with col_b:
        inv_sub = st.number_input("Remove from Inventory", min_value=0, step=1, value=0, key="inv_sub")
        if st.button("− Remove Inventory", use_container_width=True):
            if inv_sub > 0 and inv_sub <= st.session_state.ledger["inventory"]:
                st.session_state.ledger["inventory"] -= inv_sub
                add_transaction(f"Removed {inv_sub} items", {"inventory": -inv_sub})
                st.success(f"Removed {inv_sub} from inventory!")
            elif inv_sub > st.session_state.ledger["inventory"]:
                st.error("Not enough inventory!")

with tab2:
    col_c, col_d = st.columns(2)
    with col_c:
        money_in = st.number_input("Money In (+)", min_value=0.0, step=0.01, value=0.0, format="%.2f")
        if st.button("↑ Receive Money", use_container_width=True):
            if money_in > 0:
                st.session_state.ledger["money"] += money_in
                add_transaction(f"Received ${money_in:,.2f}", {"money": money_in})
                st.success(f"Added ${money_in:,.2f}!")
    with col_d:
        money_out = st.number_input("Money Out (−)", min_value=0.0, step=0.01, value=0.0, format="%.2f")
        if st.button("↓ Spend Money", use_container_width=True):
            if money_out > 0 and money_out <= st.session_state.ledger["money"]:
                st.session_state.ledger["money"] -= money_out
                add_transaction(f"Spent ${money_out:,.2f}", {"money": -money_out})
                st.success(f"Spent ${money_out:,.2f}!")
            elif money_out > st.session_state.ledger["money"]:
                st.error("Not enough money!")

with tab3:
    emp_change = st.number_input("Change Employees (±)", min_value=-10, max_value=10, step=1, value=0)
    if st.button("Update Team Size", use_container_width=True):
        if emp_change != 0:
            new_total = st.session_state.ledger["employees"] + emp_change
            if new_total >= 0:
                st.session_state.ledger["employees"] = new_total
                add_transaction(f"Team size changed by {emp_change:+}", {"employees": emp_change})
                st.success(f"Team size updated to {new_total}")
            else:
                st.error("Can't have negative employees!")

# History Log ─────────────────────────────────────
st.divider()
st.subheader("Transaction History")

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(
        df.style.format({
            "Money Δ (\( )": " \){:,.2f}",
            "Money After (\( )": " \){:,.2f}",
            "Inventory Δ": "{:+,}",
            "Employees Δ": "{:+}",
        }),
        use_container_width=True,
        hide_index=True,
    )

    if st.button("Clear History (irreversible)", type="secondary"):
        if st.session_state.history:
            if st.checkbox("Yes, I'm sure — delete all history"):
                st.session_state.history = []
                save_data()
                st.success("History cleared!")
                st.rerun()
else:
    st.info("No transactions yet. Make your first move above! 🚀")

# Auto-save on every rerun (safety net)
save_data()