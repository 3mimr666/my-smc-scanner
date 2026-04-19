import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Amimar SMC Pro", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .stMetric { background-color: #1E2127; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Amimar SMC Pro Scanner")

# رجعنا لرموز الـ Spot (الذهب العادي)
assets = {
    "Gold": "XAUUSD=X",  # الذهب اللي بغيتي (Spot)
    "Bitcoin": "BTC-USD",
    "EURUSD": "EURUSD=X",
    "NAS100": "^NDX"
}

def calculate_smc(df):
    if df is None or len(df) < 15: return None
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df['Body'] = (df['Close'] - df['Open']).abs()
    avg_body = df['Body'].rolling(10).mean()
    
    # FVG
    df['FVG_Bull'] = (df['Low'] > df['High'].shift(2))
    df['FVG_Bear'] = (df['High'] < df['Low'].shift(2))
    
    # Order Blocks
    df['OB_Bull'] = (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Close'] > df['Open']) & (df['Body'] > avg_body * 1.5)
    df['OB_Bear'] = (df['Close'].shift(1) > df['Open'].shift(1)) & (df['Close'] < df['Open']) & (df['Body'] > avg_body * 1.5)
    
    # CHoCH
    df['CHoCH_Bull'] = df['Close'] > df['High'].shift(1).rolling(20).max()
    df['CHoCH_Bear'] = df['Close'] < df['Low'].shift(1).rolling(20).min()
    return df

@st.cache_data(ttl=60)
def fetch_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # كنجيبو داتا ديال 5 أيام بـ 15 دقيقة
        data = ticker.history(period="5d", interval="15m")
        
        # هاد السطر هو السر: إيلا كانت الداتا خاوية (ويكاند)، كيجيب الداتا اليومية باش يلقى السعر
        if data.empty:
            data = ticker.history(period="1mo", interval="1d")
            
        return data
    except:
        return None

# --- الـ DASHBOARD ---
data_dict = {}
for name, sym in assets.items():
    df = fetch_data(sym)
    if df is not None and not df.empty:
        # تأكد من تنظيف الأعمدة قبل الحساب
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        data_dict[name] = calculate_smc(df)

if data_dict:
    cols = st.columns(len(data_dict))
    for i, (name, df) in enumerate(data_dict.items()):
        # كياخد آخر ثمن إغلاق مسجل باش ما يعطيش 0.00
        last_price = float(df['Close'].dropna().iloc[-1])
        status = "Bullish 🚀" if df['CHoCH_Bull'].iloc[-1] else ("Bearish 🩸" if df['CHoCH_Bear'].iloc[-1] else "Neutral ⚖️")
        with cols[i]:
            st.metric(label=name, value=f"{last_price:.2f}")
            st.caption(status)

st.markdown("---")

if data_dict:
    tabs = st.tabs(list(data_dict.keys()))
    for i, (name, df) in enumerate(data_dict.items()):
        with tabs[i]:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🔍 SMC Signals")
                if df['FVG_Bull'].tail(5).any(): st.success("🟢 Bullish FVG")
                elif df['FVG_Bear'].tail(5).any(): st.error("🔴 Bearish FVG")
                else: st.write("No FVG Found")
            with c2:
                st.subheader("📦 Order Blocks")
                if df['OB_Bull'].tail(10).any(): st.info("🔵 Bullish OB")
                elif df['OB_Bear'].tail(10).any(): st.warning("🟠 Bearish OB")
                else: st.write("No OB Found")

st.caption(f"Refreshed: {datetime.now().strftime('%H:%M:%S')} | Mode: Spot Price")
