import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# --- SETTINGS & THEME ---
st.set_page_config(page_title="Vault Inventory", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for a modern "Dark Glass" look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="metric-container"] {
        background-color: #1e2130;
        border: 1px solid #31333f;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #4F46E5;
        color: white;
        border: none;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        font-weight: 600;
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
DB_FILE = "inventory_v2.json"
G_TO_OZ = 0.035274

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: return json.load(f)
    return {"stock_g": 0.0, "revenue": 0.0, "costs": 0.0, "history": []}

def save_data(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

data = load_data()

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3515/3515228.png", width=80)
    st.title("Vault v2.0")
    st.markdown("---")
    st.write("### 📦 Stock Summary")
    st.metric("In Grams", f"{data['stock_g']:,} g")
    st.metric("In Ounces", f"{data['stock_g'] * G_TO_OZ:.2f} oz")
    
    if data['stock_g'] < 50:
        st.error("🚨 STOCK CRITICALLY LOW")

# --- MAIN DASHBOARD ---
st.title("Business Overview")
profit = data['revenue'] - data['costs']
margin = (profit / data['revenue'] * 100) if data['revenue'] > 0 else 0

# Top Row KPI Cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Gross Revenue", f"${data['revenue']:,.2f}")
col2.metric("Total Expenses", f"${data['costs']:,.2f}")
col3.metric("Net Profit", f"${profit:,.2f}")
col4.metric("Profit Margin", f"{margin:.1f}%")

st.markdown("---")

tab1, tab2 = st.tabs(["⚡ Operations", "📈 Analytics & History"])

with tab1:
    col_left, col_right = st.columns(2)
    
    with col_left:
        with st.container():
            st.subheader("📥 Restock Supply")
            amt = st.number_input("Amount", min_value=0.0, key="res_amt")
            unit = st.segmented_control("Unit", ["Grams", "Ounces"], default="Grams")
            cost = st.number_input("Purchase Price ($)", min_value=0.0)
            
            if st.button("Complete Purchase", type="primary"):
                real_g = amt if unit == "Grams" else amt / G_TO_OZ
                data['stock_g'] += real_g
                data['costs'] += cost
                data['history'].append({"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "type": "IN", "qty": real_g, "val": -cost})
                save_data(data)
                st.toast("Inventory Updated!")
                st.rerun()

    with col_right:
        with st.container():
            st.subheader("📤 Record Sale")
            s_amt = st.number_input("Amount Sold", min_value=0.0, key="sale_amt")
            s_unit = st.segmented_control("Unit", ["Grams", "Ounces"], default="Grams", key="s_unit")
            s_price = st.number_input("Sale Price ($)", min_value=0.0)
            
            if st.button("Finalize Sale"):
                real_g = s_amt if s_unit == "Grams" else s_amt / G_TO_OZ
                if real_g <= data['stock_g']:
                    data['stock_g'] -= real_g
                    data['revenue'] += s_price
                    data['history'].append({"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "type": "OUT", "qty": -real_g, "val": s_price})
                    save_data(data)
                    st.toast("Sale Recorded Successfully")
                    st.rerun()
                else:
                    st.error("Insufficient Stock")

with tab2:
    if data['history']:
        df = pd.DataFrame(data['history'])
        st.subheader("Transaction Records")
        st.dataframe(df, use_container_width=True)
        
        # Modern Charting
        st.subheader("Revenue vs Expense Flow")
        st.area_chart(df, x="date", y="val")
    else:
        st.info("No transaction history found.")
