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

st.title("📊 Amimar SMC Pro Scanner (OANDA Data Style)")

# القائمة الأساسية
assets = {
    "Gold (XAUUSD)": "XAUUSD=X",
    "Bitcoin (BTC)": "BTC-USD",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "NAS100 (Nasdaq)": "^NDX"
}

def calculate_smc(df):
    if df is None or df.empty: return None
    df = df.copy()
    
    # تنظيف الأعمدة
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # حسابات SMC أساسية
    df['Body'] = (df['Close'] - df['Open']).abs()
    avg_body = df['Body'].rolling(10).mean()
    
    df['FVG_Bull'] = (df['Low'] > df['High'].shift(2))
    df['FVG_Bear'] = (df['High'] < df['Low'].shift(2))
    
    df['OB_Bull'] = (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Close'] > df['Open']) & (df['Body'] > avg_body * 1.5)
    df['OB_Bear'] = (df['Close'].shift(1) > df['Open'].shift(1)) & (df['Close'] < df['Open']) & (df['Body'] > avg_body * 1.5)
    
    df['CHoCH_Bull'] = df['Close'] > df['High'].shift(1).rolling(20).max()
    df['CHoCH_Bear'] = df['Close'] < df['Low'].shift(1).rolling(20).min()
    return df

@st.cache_data(ttl=60)
def fetch_all_data():
    results = {}
    for name, symbol in assets.items():
        try:
            # محاولة جلب داتا 15 دقيقة (للمضاربة)
            data = yf.download(symbol, period="5d", interval="15m", progress=False, auto_adjust=True)
            
            # إيلا كانت خاوية (بسباب الويكاند)، جيب داتا يومية باش يبان الثمن
            if data.empty:
                data = yf.download(symbol, period="5d", interval="1d", progress=False, auto_adjust=True)
            
            if not data.empty:
                results[name] = calculate_smc(data)
        except Exception as e:
            continue
    return results

data_dict = fetch_all_data()

# --- DISPLAY ---
if data_dict:
    cols = st.columns(len(data_dict))
    for i, (name, df) in enumerate(data_dict.items()):
        if df is None or df.empty: continue
        
        last_price = float(df['Close'].iloc[-1])
        # حساب التغير (Delta)
        prev_price = float(df['Close'].iloc[-2])
        change = last_price - prev_price
        
        status = "Bullish 🚀" if df['CHoCH_Bull'].iloc[-3:].any() else ("Bearish 🩸" if df['CHoCH_Bear'].iloc[-3:].any() else "Neutral ⚖️")
        
        with cols[i]:
            st.metric(label=name.split()[0], value=f"{last_price:.2f}", delta=f"{change:.2f}")
            st.caption(status)

    st.markdown("---")
    tabs = st.tabs(list(data_dict.keys()))
    for i, (name, df) in enumerate(data_dict.items()):
        with tabs[i]:
            c1, c2 = st.columns(2)
            with c1:
                st.write("🔍 **FVG Status**")
                if df['FVG_Bull'].iloc[-5:].any(): st.success("🟢 FVG Bullish")
                elif df['FVG_Bear'].iloc[-5:].any(): st.error("🔴 FVG Bearish")
                else: st.write("⚪ No recent FVG")
            with c2:
                st.write("📦 **Structure (OB)**")
                if df['OB_Bull'].iloc[-10:].any(): st.info("🟢 OB Bullish")
                elif df['OB_Bear'].iloc[-10:].any(): st.warning("🔴 OB Bearish")
                else: st.write("⚪ No clear OB")

st.caption(f"Last Update: {datetime.now().strftime('%H:%M:%S')} | Weekend Mode Active")
