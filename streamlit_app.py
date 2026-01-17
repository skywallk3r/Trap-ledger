import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# --- CONFIGURATION & DATA LOADING ---
DB_FILE = "inventory_db.json"
OZ_TO_G = 28.3495

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {"stock_g": 0.0, "revenue": 0.0, "costs": 0.0, "history": []}

def save_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

data = load_data()

# --- UI HEADER ---
st.set_page_config(page_title="Material Tracker", layout="wide")
st.title("⚖️ Raw Material Inventory & Sales")

# --- SIDEBAR: QUICK STATS ---
st.sidebar.header("Current Status")
stock_oz = data["stock_g"] / OZ_TO_G
st.sidebar.metric("Stock (Grams)", f"{data['stock_g']:.2f}g")
st.sidebar.metric("Stock (Ounces)", f"{stock_oz:.2f}oz")

if data["stock_g"] < 100:
    st.sidebar.warning("⚠️ Low Stock Alert!")

# --- MAIN INTERFACE: ACTION TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Add Stock / Sale", "📜 History"])

with tab1:
    col1, col2, col3 = st.columns(3)
    profit = data["revenue"] - data["costs"]
    col1.metric("Total Revenue", f"${data['revenue']:,.2f}")
    col2.metric("Total Costs", f"${data['costs']:,.2f}")
    col3.metric("Net Profit", f"${profit:,.2f}", delta=f"{profit:.2f}")

    if data["history"]:
        df = pd.DataFrame(data["history"])
        st.line_chart(df.set_index("date")["balance_g"])
        st.caption("Inventory Level Over Time (Grams)")

with tab2:
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Restock Material")
        r_amt = st.number_input("Amount to Add", min_value=0.0)
        r_unit = st.selectbox("Unit", ["g", "oz"], key="r_unit")
        r_cost = st.number_input("Total Cost of Purchase ($)", min_value=0.0)
        
        if st.button("Confirm Restock"):
            qty = r_amt * OZ_TO_G if r_unit == "oz" else r_amt
            data["stock_g"] += qty
            data["costs"] += r_cost
            data["history"].append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "action": "RESTOCK", "change_g": qty, "money": -r_cost, "balance_g": data["stock_g"]
            })
            save_data(data)
            st.success(f"Added {r_amt}{r_unit}")
            st.rerun()

    with c2:
        st.subheader("Record a Sale")
        s_amt = st.number_input("Amount Sold", min_value=0.0)
        s_unit = st.selectbox("Unit", ["g", "oz"], key="s_unit")
        s_price = st.number_input("Sale Price ($)", min_value=0.0)
        
        if st.button("Confirm Sale"):
            qty = s_amt * OZ_TO_G if s_unit == "oz" else s_amt
            if qty <= data["stock_g"]:
                data["stock_g"] -= qty
                data["revenue"] += s_price
                data["history"].append({
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "action": "SALE", "change_g": -qty, "money": s_price, "balance_g": data["stock_g"]
                })
                save_data(data)
                st.success(f"Sold {s_amt}{s_unit}")
                st.rerun()
            else:
                st.error("Not enough stock!")

with tab3:
    st.subheader("Transaction Log")
    if data["history"]:
        history_df = pd.DataFrame(data["history"])
        st.dataframe(history_df, use_container_width=True)
        
        csv_data = history_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV for Excel", data=csv_data, file_name="inventory_history.csv")
