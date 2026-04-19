import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Amimar SMC Scanner", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .signal-card { background-color: #1E2127; padding: 10px; border-radius: 8px; border-left: 5px solid #00C853; margin-bottom: 5px; }
    .bear-card { border-left: 5px solid #FF3D00; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Amimar SMC Pro Scanner")

# إضافة البيتكوين للقائمة
assets = {
    "Bitcoin (BTC)": "BTC-USD",
    "XAUUSD (Gold)": "XAUUSD=X",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "NAS100 (Nasdaq)": "^NDX"
}

def calculate_smc(df):
    df = df.copy()
    # FVG (Fair Value Gap)
    df['FVG_Bull'] = df['Low'] > df['High'].shift(2)
    df['FVG_Bear'] = df['High'] < df['Low'].shift(2)
    
    # OB (Order Block)
    df['Body'] = abs(df['Close'] - df['Open'])
    avg_body = df['Body'].rolling(10).mean()
    df['OB_Bull'] = (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Close'] > df['Open']) & (df['Body'] > avg_body * 1.5)
    df['OB_Bear'] = (df['Close'].shift(1) > df['Open'].shift(1)) & (df['Close'] < df['Open']) & (df['Body'] > avg_body * 1.5)
    
    # CHoCH (Change of Character - Break of 20-period structure)
    df['CHoCH_Bull'] = df['Close'] > df['High'].shift(1).rolling(20).max()
    df['CHoCH_Bear'] = df['Close'] < df['Low'].shift(1).rolling(20).min()
    return df

@st.cache_data(ttl=60)
def fetch_all_data():
    results = {}
    for name, symbol in assets.items():
        try:
            # كنستعملو 5 أيام باش يكون عندنا داتا كافية للحساب
            data = yf.download(symbol, period="5d", interval="15m", progress=False)
            if not data.empty:
                results[name] = calculate_smc(data)
        except Exception as e:
            st.error(f"Error loading {name}: {e}")
    return results

data_dict = fetch_all_data()

# --- 1. DASHBOARD SUMMARY ---
st.subheader("🚀 Quick Signals Summary")
if data_dict:
    # تقسيم الأعمدة على حسب عدد العملات
    cols = st.columns(len(data_dict))
    for i, (name, df) in enumerate(data_dict.items()):
        last = df.iloc[-1]
        # تحديد الإشارة بناءً على آخر 3 شمعات
        if df['CHoCH_Bull'].iloc[-3:].any():
            recent_choch = "Bullish 🚀"
        elif df['CHoCH_Bear'].iloc[-3:].any():
            recent_choch = "Bearish 🩸"
        else:
            recent_choch = "Neutral ⚖️"
            
        with cols[i]:
            # تنظيف السمية باش تبان قصيرة في الميتريك
            short_name = name.split()[0]
            st.metric(short_name, f"{last['Close']:.2f}", recent_choch)

# --- 2. DETAILED ANALYSIS ---
st.markdown("---")
if data_dict:
    tabs = st.tabs(list(data_dict.keys()))
    for i, (name, df) in enumerate(data_dict.items()):
        with tabs[i]:
            latest = df.iloc[-1]
            
            # تنبيهات CHoCH
            if df['CHoCH_Bull'].iloc[-3:].any():
                st.success(f"🔥 BULLISH CHoCH detected on {name} (M15)!")
            elif df['CHoCH_Bear'].iloc[-3:].any():
                st.error(f"⚠️ BEARISH CHoCH detected on {name} (M15)!")

            col1, col2 = st.columns(2)
            with col1:
                st.write("🔍 **Latest FVGs (M15)**")
                if df['FVG_Bull'].iloc[-5:].any(): st.write("🟢 Bullish FVG active")
                if df['FVG_Bear'].iloc[-5:].any(): st.write("🔴 Bearish FVG active")
                if not df['FVG_Bull'].iloc[-5:].any() and not df['FVG_Bear'].iloc[-5:].any():
                    st.write("⚪ No active FVG in last 5 candles")
            
            with col2:
                st.write("📦 **Order Blocks**")
                if df['OB_Bull'].iloc[-10:].any(): st.write("🟢 Bullish OB formed")
                if df['OB_Bear'].iloc[-10:].any(): st.write("🔴 Bearish OB formed")
                if not df['OB_Bull'].iloc[-10:].any() and not df['OB_Bear'].iloc[-10:].any():
                    st.write("⚪ No major OB in last 10 candles")

st.caption(f"Last Scan: {datetime.now().strftime('%H:%M:%S')} | Data from Yahoo Finance | Optimized for M15.")
