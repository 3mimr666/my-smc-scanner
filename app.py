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

# الرموز اللي كتكون متطابقة مع OANDA فـ Yahoo Finance
assets = {
    "Gold (XAUUSD)": "XAUUSD=X",  # السعر الفوري العالمي
    "Bitcoin (BTC)": "BTC-USD",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "NAS100 (Nasdaq)": "^NDX"
}

def calculate_smc(df):
    df = df.copy()
    if df.empty: return df
    
    # تنظيف المولتيايندكس (حل مشكل الخطأ اللي طلع ليك)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # حساب الـ SMC
    df['Body'] = (df['Close'] - df['Open']).abs()
    avg_body = df['Body'].rolling(10).mean()
    
    df['FVG_Bull'] = (df['Low'] > df['High'].shift(2))
    df['FVG_Bear'] = (df['High'] < df['Low'].shift(2))
    
    df['OB_Bull'] = (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Close'] > df['Open']) & (df['Body'] > avg_body * 1.5)
    df['OB_Bear'] = (df['Close'].shift(1) > df['Open'].shift(1)) & (df['Close'] < df['Open']) & (df['Body'] > avg_body * 1.5)
    
    df['CHoCH_Bull'] = df['Close'] > df['High'].shift(1).rolling(20).max()
    df['CHoCH_Bear'] = df['Close'] < df['Low'].shift(1).rolling(20).min()
    return df

@st.cache_data(ttl=30) # تحديث كل 30 ثانية
def fetch_all_data():
    results = {}
    for name, symbol in assets.items():
        try:
            # كنستعملو هاد الطريقة باش نجيبو أدق سعر إغلاق
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="5d", interval="15m")
            
            if not data.empty:
                results[name] = calculate_smc(data)
        except:
            continue
    return results

data_dict = fetch_all_data()

# --- DISPLAY ---
if data_dict:
    cols = st.columns(len(data_dict))
    for i, (name, df) in enumerate(data_dict.items()):
        last_price = df['Close'].iloc[-1]
        
        # تحديد السعر واش هابط ولا طالع مقارنة بالشمعة اللي قبل
        delta = float(last_price - df['Close'].iloc[-2])
        
        with cols[i]:
            st.metric(label=name.split()[0], value=f"{float(last_price):.2f}", delta=f"{delta:.2f}")

    # تفاصيل الـ SMC
    tabs = st.tabs(list(data_dict.keys()))
    for i, (name, df) in enumerate(data_dict.items()):
        with tabs[i]:
            st.write(f"### {name} Analysis")
            c1, c2 = st.columns(2)
            with c1:
                if df['CHoCH_Bull'].iloc[-5:].any(): st.success("🚀 Bullish CHoCH (Structure Break)")
                if df['CHoCH_Bear'].iloc[-5:].any(): st.error("🩸 Bearish CHoCH (Structure Break)")
            with c2:
                if df['FVG_Bull'].iloc[-3:].any(): st.info("🟢 FVG Bullish")
                if df['OB_Bull'].iloc[-5:].any(): st.info("📦 Order Block Bullish")

st.caption(f"Last Refresh: {datetime.now().strftime('%H:%M:%S')} | Data Source: Spot Market (OANDA Style)")
