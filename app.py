import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Amimar SMC Scanner", page_icon="📈", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .signal-card { background-color: #1E2127; padding: 10px; border-radius: 8px; border-left: 5px solid #00C853; margin-bottom: 5px; }
    .bear-card { border-left: 5px solid #FF3D00; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 SMC Pro Scanner")

# العملات اللي بغيتي تتبع (زدت ليك البيتكوين دابا)
assets = {
    "XAUUSD (Gold)": "XAUUSD=X",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "NAS100 (Nasdaq)": "^NDX",
    "BTCUSD (Crypto)": "BTC-USD"
}

def calculate_smc(df):
    df = df.copy()
    # FVG
    df['FVG_Bull'] = df['Low'] > df['High'].shift(2)
    df['FVG_Bear'] = df['High'] < df['Low'].shift(2)
    # OB
    df['Body'] = abs(df['Close'] - df['Open'])
    avg_body = df['Body'].rolling(10).mean()
    df['OB_Bull'] = (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Close'] > df['Open']) & (df['Body'] > avg_body * 1.5)
    df['OB_Bear'] = (df['Close'].shift(1) > df['Open'].shift(1)) & (df['Close'] < df['Open']) & (df['Body'] > avg_body * 1.5)
    # CHoCH (Break of 20-period structure)
    df['CHoCH_Bull'] = df['Close'] > df['High'].shift(1).rolling(20).max()
    df['CHoCH_Bear'] = df['Close'] < df['Low'].shift(1).rolling(20).min()
    return df

@st.cache_data(ttl=60)
def fetch_all_data():
    results = {}
    for name, symbol in assets.items():
        data = yf.download(symbol, period="5d", interval="15m", progress=False)
        if not data.empty:
            results[name] = calculate_smc(data)
    return results

data_dict = fetch_all_data()

# --- 1. DASHBOARD SUMMARY (الخلاصة السريعة) ---
st.subheader("🚀 Quick Signals Summary")
cols = st.columns(len(assets))

for i, (name, df) in enumerate(data_dict.items()):
    last = df.iloc[-1]
    recent_choch = "Bullish 🚀" if df['CHoCH_Bull'].iloc[-3:].any() else ("Bearish 🩸" if df['CHoCH_Bear'].iloc[-3:].any() else "Neutral ⚖️")
    with cols[i]:
        st.metric(name.split()[0], f"{last['Close']:.2f}", recent_choch)

# --- 2. DETAILED ANALYSIS ---
st.markdown("---")
tabs = st.tabs(list(assets.keys()))

for i, (name, df) in enumerate(data_dict.items()):
    with tabs[i]:
        latest = df.iloc[-1]
        
        # Alerts for CHoCH
        if df['CHoCH_Bull'].iloc[-3:].any():
            st.success(f"🔥 BULLISH CHoCH detected on {name} (M15)!")
        elif df['CHoCH_Bear'].iloc[-3:].any():
            st.error(f"⚠️ BEARISH CHoCH detected on {name} (M15)!")

        col1, col2 = st.columns(2)
        with col1:
            st.write("🔍 **Latest FVGs**")
            if df['FVG_Bull'].iloc[-5:].any(): st.write("🟢 Bullish FVG active")
            if df['FVG_Bear'].iloc[-5:].any(): st.write("🔴 Bearish FVG active")
        
        with col2:
            st.write("📦 **Order Blocks**")
            if df['OB_Bull'].iloc[-10:].any(): st.write("🟢 Bullish OB formed")
            if df['OB_Bear'].iloc[-10:].any(): st.write("🔴 Bearish OB formed")

st.caption(f"Last Scan: {datetime.now().strftime('%H:%M:%S')} | NAS100 added.")
