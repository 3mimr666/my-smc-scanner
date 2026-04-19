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

st.title("📊 Amimar SMC Pro (Auto-Fix Mode)")

# الرموز الأساسية (Spot)
assets_config = {
    "Gold": {"spot": "XAUUSD=X", "backup": "GC=F"},
    "Bitcoin": {"spot": "BTC-USD", "backup": "BTC-USD"},
    "EURUSD": {"spot": "EURUSD=X", "backup": "EURUSD=X"},
    "NAS100": {"spot": "^NDX", "backup": "^NDX"}
}

def calculate_smc(df):
    if df is None or len(df) < 10: return None
    try:
        df = df.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # تنظيف الداتا
        df = df.ffill().dropna(subset=['Close'])

        # حسابات SMC
        df['Body'] = (df['Close'] - df['Open']).abs()
        df['CHoCH_Bull'] = df['Close'] > df['High'].shift(1).rolling(15).max()
        df['CHoCH_Bear'] = df['Close'] < df['Low'].shift(1).rolling(15).min()
        df['FVG_Bull'] = (df['Low'] > df['High'].shift(2))
        df['OB_Bull'] = (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Close'] > df['Open'])
        
        return df
    except:
        return None

@st.cache_data(ttl=60)
def fetch_smart_data(name, config):
    try:
        # 1. محاولة جلب الـ Spot أولاً
        ticker = yf.Ticker(config["spot"])
        df = ticker.history(period="7d", interval="1h")
        
        # 2. إيلا كان الـ Spot خاوي أو السعر 0 (مشكل الويكاند)
        if df.empty or (not df.empty and df['Close'].iloc[-1] == 0):
            ticker = yf.Ticker(config["backup"])
            df = ticker.history(period="7d", interval="1h")
            
        return df
    except:
        return None

# --- DASHBOARD ---
cols = st.columns(len(assets_config))

for i, (name, config) in enumerate(assets_config.items()):
    df = fetch_smart_data(name, config)
    smc_df = calculate_smc(df)
    
    with cols[i]:
        if df is not None and not df.empty:
            last_price = float(df['Close'].iloc[-1])
            st.metric(label=name, value=f"{last_price:.2f}")
            
            if smc_df is not None:
                if smc_df['CHoCH_Bull'].iloc[-1]: st.success("Bullish 🚀")
                elif smc_df['CHoCH_Bear'].iloc[-1]: st.error("Bearish 🩸")
                else: st.info("Neutral ⚖️")
            else:
                st.caption("Scanning...")
        else:
            st.metric(label=name, value="Offline")

st.markdown("---")

# تفاصيل التحليل لضمان الجودة
st.subheader("🔍 Market Analysis Details")
selected_asset = st.selectbox("Choose asset to see details:", list(assets_config.keys()))
df_detail = fetch_smart_data(selected_asset, assets_config[selected_asset])
smc_detail = calculate_smc(df_detail)

if smc_detail is not None:
    c1, c2 = st.columns(2)
    with c1:
        st.write("**Signals:**")
        if smc_detail['FVG_Bull'].tail(10).any(): st.success("✅ FVG Detected")
        else: st.write("No FVG in range")
    with c2:
        st.write("**Structure:**")
        if smc_detail['OB_Bull'].tail(10).any(): st.info("📦 Order Block Active")
        else: st.write("No OB Found")
else:
    st.warning("Could not generate SMC analysis for this asset yet.")

st.caption(f"Last Refresh: {datetime.now().strftime('%H:%M:%S')} | Mode: Smart Backup Active")
