import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Amimar SMC Scanner", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .stMetric { background-color: #1E2127; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Amimar SMC Pro Scanner")

# الرموز - جربت ليك هاد الرموز اللي كيعطيو داتا مستقرة ف الويكاند
assets = {
    "Gold (XAUUSD)": "GC=F",   # الذهب (Futures) كيعطي آخر ثمن إغلاق ديما
    "Bitcoin (BTC)": "BTC-USD",
    "EURUSD": "EURUSD=X",
    "NAS100 (Nasdaq)": "^NDX"
}

@st.cache_data(ttl=60)
def get_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # محاولة جلب داتا يومية لضمان وجود السعر
        df = ticker.history(period="5d", interval="1d")
        
        # إيلا بغينا الـ SMC نجبدو داتا 15 دقيقة
        df_15m = ticker.history(period="2d", interval="15m")
        
        if not df.empty:
            last_price = df['Close'].iloc[-1]
            return df_15m if not df_15m.empty else df, last_price
        return None, 0
    except:
        return None, 0

def calculate_smc(df):
    if df is None or df.empty: return None
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df['Body'] = (df['Close'] - df['Open']).abs()
    avg_body = df['Body'].rolling(10).mean()
    df['CHoCH_Bull'] = df['Close'] > df['High'].shift(1).rolling(15).max()
    df['CHoCH_Bear'] = df['Close'] < df['Low'].shift(1).rolling(15).min()
    return df

# --- عرض الأثمنة ---
st.subheader("🚀 Live Market Prices")
cols = st.columns(len(assets))

for i, (name, symbol) in enumerate(assets.items()):
    df, price = get_data(symbol)
    
    with cols[i]:
        # إيلا كان الذهب، كنضربو الثمن فـ 1 (للتأكد) ونعرضوه
        display_name = name.split()[0]
        st.metric(label=display_name, value=f"{float(price):.2f}")
        
        smc_df = calculate_smc(df)
        if smc_df is not None:
            if smc_df['CHoCH_Bull'].iloc[-1]: st.caption("Bullish 🚀")
            elif smc_df['CHoCH_Bear'].iloc[-1]: st.caption("Bearish 🩸")
            else: st.caption("Neutral ⚖️")
        else:
            st.caption("Market Closed")

st.markdown("---")
st.info("💡 ملاحظة: الذهب (Gold) معروض بسعر العقود الآجلة لضمان الظهور في الويكاند.")
st.caption(f"Refreshed: {datetime.now().strftime('%H:%M:%S')}")
