import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Amimar SMC Scanner", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .stMetric { background-color: #1E2127; padding: 10px; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Amimar SMC Pro Scanner")

assets = {
    "Gold (XAUUSD)": "XAUUSD=X",
    "Bitcoin (BTC)": "BTC-USD",
    "EURUSD": "EURUSD=X",
    "NAS100 (Nasdaq)": "^NDX"
}

def calculate_smc(df):
    try:
        if df is None or len(df) < 10: return None
        df = df.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df['Body'] = (df['Close'] - df['Open']).abs()
        avg_body = df['Body'].rolling(10).mean()
        df['FVG_Bull'] = (df['Low'] > df['High'].shift(2))
        df['OB_Bull'] = (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Close'] > df['Open']) & (df['Body'] > avg_body * 1.5)
        df['CHoCH_Bull'] = df['Close'] > df['High'].shift(1).rolling(20).max()
        df['CHoCH_Bear'] = df['Close'] < df['Low'].shift(1).rolling(20).min()
        return df
    except:
        return None

@st.cache_data(ttl=60)
def get_asset_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # محاولة جلب داتا فريم صغير
        df = ticker.history(period="5d", interval="15m")
        if df.empty:
            df = ticker.history(period="5d", interval="1d")
        
        # جلب آخر ثمن حي (حتى لو السوق مغلق)
        info = ticker.fast_info
        last_price = info.get('last_price', None)
        
        return df, last_price
    except:
        return None, None

# --- الـ DASHBOARD ---
st.subheader("🚀 Live Market Prices")
cols = st.columns(len(assets))

processed_data = {}

for i, (name, symbol) in enumerate(assets.items()):
    df, live_price = get_asset_data(symbol)
    
    # إيلا ما لقا الداتا، كياخد آخر ثمن إغلاق من الـ df
    display_price = live_price if live_price else (df['Close'].iloc[-1] if not df.empty else 0)
    
    with cols[i]:
        st.metric(label=name, value=f"{display_price:.2f}")
        
        # تحليل SMC إيلا توفرت الداتا
        smc_df = calculate_smc(df)
        if smc_df is not None:
            processed_data[name] = smc_df
            status = "Bullish 🚀" if smc_df['CHoCH_Bull'].iloc[-1] else ("Bearish 🩸" if smc_df['CHoCH_Bear'].iloc[-1] else "Neutral ⚖️")
            st.caption(status)
        else:
            st.caption("Market Closed (OANDA Style)")

# --- DETAILS ---
st.markdown("---")
if processed_data:
    tabs = st.tabs(list(processed_data.keys()))
    for i, name in enumerate(processed_data.keys()):
        with tabs[i]:
            df = processed_data[name]
            c1, c2 = st.columns(2)
            with c1:
                st.write("🔍 **Smart Money Signals**")
                if df['FVG_Bull'].tail(5).any(): st.success("🟢 FVG Found")
                else: st.write("No Signal")
            with c2:
                st.write("📦 **Order Blocks**")
                if df['OB_Bull'].tail(10).any(): st.info("🟢 Strong OB")
                else: st.write("Searching...")
else:
    st.info("SMC Analysis is waiting for market open. Prices are shown above.")

st.caption(f"Refreshed at: {datetime.now().strftime('%H:%M:%S')}")
                    if df['OB_Bull'].iloc[-5:].any(): st.info("📦 Order Block Active")

