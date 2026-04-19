import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Amimar SMC Scanner", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Amimar SMC Pro Scanner")

assets = {
    "Bitcoin (BTC)": "BTC-USD",
    "XAUUSD (Gold)": "XAUUSD=X",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "NAS100 (Nasdaq)": "^NDX"
}

def calculate_smc(df):
    df = df.copy()
    # حساب الـ Body ومتوسط الحركة
    df['Body'] = (df['Close'] - df['Open']).abs()
    avg_body = df['Body'].rolling(10).mean()
    
    # FVG
    df['FVG_Bull'] = df['Low'] > df['High'].shift(2)
    df['FVG_Bear'] = df['High'] < df['Low'].shift(2)
    
    # Order Blocks
    df['OB_Bull'] = (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Close'] > df['Open']) & (df['Body'] > avg_body * 1.5)
    df['OB_Bear'] = (df['Close'].shift(1) > df['Open'].shift(1)) & (df['Close'] < df['Open']) & (df['Body'] > avg_body * 1.5)
    
    # CHoCH
    df['CHoCH_Bull'] = df['Close'] > df['High'].shift(1).rolling(20).max()
    df['CHoCH_Bear'] = df['Close'] < df['Low'].shift(1).rolling(20).min()
    return df

@st.cache_data(ttl=60)
def fetch_all_data():
    results = {}
    for name, symbol in assets.items():
        try:
            # تحميل البيانات
            data = yf.download(symbol, period="5d", interval="15m", progress=False)
            
            if not data.empty:
                # --- هاد السطر هو الحل للمشكل اللي ظهر ليك ---
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                
                results[name] = calculate_smc(data)
        except Exception as e:
            st.error(f"Error loading {name}: {str(e)}")
    return results

data_dict = fetch_all_data()

# --- DASHBOARD SUMMARY ---
st.subheader("🚀 Quick Signals Summary")
if data_dict:
    cols = st.columns(len(data_dict))
    for i, (name, df) in enumerate(data_dict.items()):
        last = df.iloc[-1]
        status = "Bullish 🚀" if df['CHoCH_Bull'].iloc[-3:].any() else ("Bearish 🩸" if df['CHoCH_Bear'].iloc[-3:].any() else "Neutral ⚖️")
        with cols[i]:
            st.metric(name.split()[0], f"{float(last['Close']):.2f}", status)

# --- DETAILED ANALYSIS ---
st.markdown("---")
if data_dict:
    tabs = st.tabs(list(data_dict.keys()))
    for i, (name, df) in enumerate(data_dict.items()):
        with tabs[i]:
            col1, col2 = st.columns(2)
            with col1:
                st.write("🔍 **Latest FVGs**")
                if df['FVG_Bull'].iloc[-5:].any(): st.success("🟢 Bullish FVG Found")
                if df['FVG_Bear'].iloc[-5:].any(): st.error("🔴 Bearish FVG Found")
            with col2:
                st.write("📦 **Order Blocks**")
                if df['OB_Bull'].iloc[-10:].any(): st.info("🟢 Bullish OB")
                if df['OB_Bear'].iloc[-10:].any(): st.warning("🔴 Bearish OB")

st.caption(f"Last Scan: {datetime.now().strftime('%H:%M:%S')}")
