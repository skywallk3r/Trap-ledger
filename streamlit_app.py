# ledger_app_streamlit_advanced.py
# Run with: streamlit run ledger_app_streamlit_advanced.py

import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

DATA_FILE = "ledger_data.json"

# ── Constants ────────────────────────────────────────────────────────────────
OZ_TO_G = 28.3495  # Standard conversion (more precise than 28)

# ── Load or initialize data ──────────────────────────────────────────────────
if "ledger" not in st.session_state:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            loaded = json.load(f)
            st.session_state.ledger = loaded.get("ledger", {
                "vault_g": 0.0,
                "will_g": 0.0,
                "luke_g": 0.0,
                "avg_cost_per_g": 0.0,  # $ per gram
                "cash": 0.0,
                "employees": 2
            })
            st.session_state.history = loaded.get("history", [])
    else:
        st.session_state.ledger = {
            "vault_g": 0.0,
            "will_g": 0.0,
            "luke_g": 0.0,
            "avg_cost_per_g": 0.0,
            "cash": 0.0,
            "employees": 2
        }
        st.session_state.history = []

ledger = st.session_state.ledger

# ── Helper functions ─────────────────────────────────────────────────────────
def g_to_display(g):
    unit = st.session_state.get("display_unit", "grams")
    if unit == "ounces":
        return g / OZ_TO_G
    return g

def display_to_g(value):
    unit = st.session_state.get("display_unit", "grams")
    if unit == "ounces":
        return value * OZ_TO_G
    return value

def total_stock_g():
    return ledger["vault_g"] + ledger["will_g"] + ledger["luke_g"]

def inventory_value():
    return round(total_stock_g() * ledger["avg_cost_per_g"], 2)

def add_transaction(desc, changes, cost_change=0.0):
    now = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    entry = {
        "Date": now,
        "Description": desc,
        "Vault Δ (g)": changes.get("vault", 0.0),
        "Will Δ (g)": changes.get("will", 0.0),
        "Luke Δ (g)": changes.get("luke", 0.0),
        "Total Stock After (g)": total_stock_g(),
        "Avg $/g After": round(ledger["avg_cost_per_g"], 4),
        "Inventory Value After ($)": inventory_value(),
        "Cash Δ ($)": changes.get("cash", 0.0),
        "Cash After ($)": round(ledger["cash"], 2),
        "Employees Δ": changes.get("employees", 0),
    }
    if cost_change != 0:
        entry["Cost Added ($)"] = cost_change
    st.session_state.history.insert(0, entry)
    save_data()

def save_data():
    data = {
        "ledger": ledger,
        "history": st.session_state.history
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ── UI ───────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Luke's Advanced Ledger", layout="wide")
st.title("📒 Luke's Product Ledger (1 Item)")
st.caption("Tracking weight (g/oz), locations (Vault/Will/Luke), cash, team & inventory cost basis • Bloomington, MN")

# Display Unit Preference
st.session_state.display_unit = st.selectbox("Display weights in:", ["grams", "ounces"], index=0)

# Current Snapshot ────────────────────────────────
cols = st.columns(5)
cols[0].metric("Total Stock", f"{g_to_display(total_stock_g()):.2f} {'g' if st.session_state.display_unit == 'grams' else 'oz'}")
cols[1].metric("Vault", f"{g_to_display(ledger['vault_g']):.2f}")
cols[2].metric("On Will", f"{g_to_display(ledger['will_g']):.2f}")
cols[3].metric("On Luke", f"{g_to_display(ledger['luke_g']):.2f}")
cols[4].metric("Inventory Value (owed)", f"${inventory_value():,.2f}")

st.metric("Cash Balance", f"${ledger['cash']:,.2f}")
st.metric("Team Size", ledger["employees"])
st.caption(f"Average cost: ${ledger['avg_cost_per_g']:.4f} per gram")

st.divider()

# Quick Actions Tabs ───────────────────────────────────
st.subheader("Quick Actions")

tab1, tab2, tab3, tab4 = st.tabs(["Add/Receive Stock", "Sell/Remove Stock", "Move Between Locations", "Cash & Team"])

with tab1:  # Add/Receive (e.g. buy more product)
    col_a, col_b, col_c = st.columns([2, 1, 2])
    with col_a:
        add_amount_disp = st.number_input("Amount to add", min_value=0.0, step=0.01, value=0.0)
    with col_b:
        add_unit = st.selectbox("Unit", ["grams", "ounces"], key="add_unit")
    add_amount_g = add_amount_disp * OZ_TO_G if add_unit == "ounces" else add_amount_disp

    location_add = st.selectbox("Add to which location?", ["Vault", "Will", "Luke"])
    cost_paid = st.number_input("Total cost paid for this addition ($)", min_value=0.0, step=0.01, value=0.0)

    if st.button("✓ Receive / Add Stock", use_container_width=True) and add_amount_g > 0:
        key = {"Vault": "vault_g", "Will": "will_g", "Luke": "luke_g"}[location_add]
        old_total_g = total_stock_g()
        ledger[key] += add_amount_g

        if add_amount_g > 0 and cost_paid > 0:
            new_total_g = total_stock_g()
            total_cost_before = old_total_g * ledger["avg_cost_per_g"]
            ledger["avg_cost_per_g"] = (total_cost_before + cost_paid) / new_total_g if new_total_g > 0 else 0.0

        add_transaction(f"Added {add_amount_disp:.2f} {add_unit} to {location_add} (cost ${cost_paid:,.2f})", 
                        {location_add.lower(): add_amount_g}, cost_change=cost_paid)
        st.success("Stock & cost updated!")

with tab2:  # Sell/Remove
    col_d, col_e, col_f = st.columns([2, 1, 2])
    with col_d:
        remove_disp = st.number_input("Amount to remove/sell", min_value=0.0, step=0.01, value=0.0)
    with col_e:
        remove_unit = st.selectbox("Unit", ["grams", "ounces"], key="remove_unit")
    remove_g = remove_disp * OZ_TO_G if remove_unit == "ounces" else remove_disp

    location_remove = st.selectbox("Remove from which location?", ["Vault", "Will", "Luke"])
    cash_received = st.number_input("Cash received from sale (optional)", min_value=0.0, step=0.01, value=0.0)

    if st.button("↓ Sell / Remove", use_container_width=True) and remove_g > 0:
        key = {"Vault": "vault_g", "Will": "will_g", "Luke": "luke_g"}[location_remove]
        if ledger[key] >= remove_g:
            ledger[key] -= remove_g
            add_transaction(f"Removed {remove_disp:.2f} {remove_unit} from {location_remove}", 
                            {location_remove.lower(): -remove_g}, cost_change=0.0)
            if cash_received > 0:
                ledger["cash"] += cash_received
                add_transaction(f"Cash in from sale: ${cash_received:,.2f}", {"cash": cash_received})
            st.success("Removed!")
        else:
            st.error("Not enough in that location!")

with tab3:  # Move between people/locations
    col_from, col_to, col_amt = st.columns(3)
    with col_from:
        from_loc = st.selectbox("From", ["Vault", "Will", "Luke"], key="from_loc")
    with col_to:
        to_loc = st.selectbox("To", ["Vault", "Will", "Luke"], key="to_loc")
    with col_amt:
        move_disp = st.number_input("Amount to move", min_value=0.0, step=0.01)
        move_unit = st.selectbox("Unit", ["grams", "ounces"], key="move_unit")
    move_g = move_disp * OZ_TO_G if move_unit == "ounces" else move_disp

    if st.button("↔ Move Stock", use_container_width=True) and move_g > 0 and from_loc != to_loc:
        from_key = {"Vault": "vault_g", "Will": "will_g", "Luke": "luke_g"}[from_loc]
        to_key = {"Vault": "vault_g", "Will": "will_g", "Luke": "luke_g"}[to_loc]
        if ledger[from_key] >= move_g:
            ledger[from_key] -= move_g
            ledger[to_key] += move_g
            add_transaction(f"Moved {move_disp:.2f} {move_unit} from {from_loc} → {to_loc}", 
                            {from_loc.lower(): -move_g, to_loc.lower(): move_g})
            st.success("Moved!")
        else:
            st.error("Not enough to move!")

with tab4:  # Cash & Employees
    new_cash = st.number_input("Update Cash Balance ($)", value=ledger["cash"], step=0.01)
    new_employees = st.number_input("Update Employees", value=ledger["employees"], step=1, min_value=0)
    if st.button("Update Cash / Team", use_container_width=True):
        delta_cash = new_cash - ledger["cash"]
        delta_emp = new_employees - ledger["employees"]
        ledger["cash"] = new_cash
        ledger["employees"] = new_employees
        changes = {}
        if delta_cash != 0: changes["cash"] = delta_cash
        if delta_emp != 0: changes["employees"] = delta_emp
        if changes:
            add_transaction("Manual cash/team update", changes)

# History ─────────────────────────────────────────────
st.divider()
st.subheader("Transaction History")

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(
        df.style.format({
            col: "\( {:,.2f}" for col in df.columns if " \)" in col
        }).format({
            col: "{:.2f}" for col in df.columns if "(g)" in col or "Stock" in col
        }),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No transactions yet — start adding/receiving stock above!")

# Safety net save
save_data()