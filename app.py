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

# الرموز اللي كتخدم مزيان ف الويكاند وكتعطي داتا للتحليل
assets = {
    "Gold": "GC=F",   # الذهب (Futures) باش يبان السعر والتحليل ديما
    "Bitcoin": "BTC-USD",
    "EURUSD": "EURUSD=X",
    "NAS100": "^NDX"
}

def calculate_smc(df):
    if df is None or len(df) < 20: return None
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # حسابات SMC
    df['Body'] = (df['Close'] - df['Open']).abs()
    avg_body = df['Body'].rolling(10).mean()
    
    # Fair Value Gaps
    df['FVG_Bull'] = (df['Low'] > df['High'].shift(2))
    df['FVG_Bear'] = (df['High'] < df['Low'].shift(2))
    
    # Order Blocks
    df['OB_Bull'] = (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Close'] > df['Open']) & (df['Body'] > avg_body * 1.5)
    df['OB_Bear'] = (df['Close'].shift(1) > df['Open'].shift(1)) & (df['Close'] < df['Open']) & (df['Body'] > avg_body * 1.5)
    
    # Structure Break (CHoCH)
    df['CHoCH_Bull'] = df['Close'] > df['High'].shift(1).rolling(20).max()
    df['CHoCH_Bear'] = df['Close'] < df['Low'].shift(1).rolling(20).min()
    return df

@st.cache_data(ttl=60)
def fetch_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # كنجيبو داتا ديال 5 أيام بـ فريم 15 دقيقة باش نضمنو كاين ما يتحلل
        data = ticker.history(period="5d", interval="15m")
        
        # إيلا كانت الداتا ديال 15 دقيقة خاوية (بسباب الويكاند)، كنجيبو اليومية
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
        data_dict[name] = calculate_smc(df)

# عرض الأثمنة والتحليل السريع
if data_dict:
    cols = st.columns(len(data_dict))
    for i, (name, df) in enumerate(data_dict.items()):
        last_price = float(df['Close'].iloc[-1])
        status = "Bullish 🚀" if df['CHoCH_Bull'].iloc[-1] else ("Bearish 🩸" if df['CHoCH_Bear'].iloc[-1] else "Neutral ⚖️")
        with cols[i]:
            st.metric(label=name, value=f"{last_price:.2f}")
            st.caption(status)

st.markdown("---")

# تفاصيل التحليل (التابات)
if data_dict:
    tabs = st.tabs(list(data_dict.keys()))
    for i, (name, df) in enumerate(data_dict.items()):
        with tabs[i]:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🔍 Smart Money Signals")
                # كنشوفو آخر 5 شمعات واش فيهم إشارة
                if df['FVG_Bull'].tail(5).any(): st.success("🟢 Bullish FVG Detected")
                if df['FVG_Bear'].tail(5).any(): st.error("🔴 Bearish FVG Detected")
                if not df['FVG_Bull'].tail(5).any() and not df['FVG_Bear'].tail(5).any():
                    st.write("No FVG signals in the last candles.")
            
            with c2:
                st.subheader("📦 Supply & Demand")
                if df['OB_Bull'].tail(10).any(): st.info("🔵 Bullish Order Block")
                if df['OB_Bear'].tail(10).any(): st.warning("🟠 Bearish Order Block")
                if not df['OB_Bull'].tail(10).any() and not df['OB_Bear'].tail(10).any():
                    st.write("No strong Order Blocks found.")

st.caption(f"Refreshed: {datetime.now().strftime('%H:%M:%S')} | Full Analysis Mode")
