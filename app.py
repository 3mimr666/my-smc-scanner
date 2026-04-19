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

st.title("📊 Amimar SMC Pro Scanner (Spot Price)")

assets = {
    "Gold (XAUUSD)": "XAUUSD=X",
    "Bitcoin (BTC)": "BTC-USD",
    "EURUSD": "EURUSD=X",
    "NAS100 (Nasdaq)": "^NDX"
}

def calculate_smc(df):
    if df is None or len(df) < 5: return None
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # حسابات مبسطة باش تخدم على أي فريم (يومي أو 15د)
    df['Body'] = (df['Close'] - df['Open']).abs()
    avg_body = df['Body'].rolling(min(10, len(df))).mean()
    
    df['CHoCH_Bull'] = df['Close'] > df['High'].shift(1).rolling(min(15, len(df))).max()
    df['CHoCH_Bear'] = df['Close'] < df['Low'].shift(1).rolling(min(15, len(df))).min()
    
    df['FVG_Bull'] = (df['Low'] > df['High'].shift(2))
    df['OB_Bull'] = (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Close'] > df['Open'])
    
    return df

@st.cache_data(ttl=60)
def fetch_spot_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # 1. كنجيبو الداتا اليومية أولاً باش نضمنو السعر (موجودة ديما)
        df_daily = ticker.history(period="1mo", interval="1d")
        
        # 2. كنحاولوا نجيبو داتا 15 دقيقة
        try:
            df_15m = ticker.history(period="5d", interval="15m")
            if not df_15m.empty:
                return df_15m
        except:
            pass
            
        return df_daily
    except:
        return None

# --- الـ DASHBOARD ---
cols = st.columns(len(assets))

for i, (name, symbol) in enumerate(assets.items()):
    df = fetch_spot_data(symbol)
    
    if df is not None and not df.empty:
        # تنظيف الأعمدة
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        last_price = float(df['Close'].iloc[-1])
        smc_df = calculate_smc(df)
        
        with cols[i]:
            st.metric(label=name.split()[0], value=f"{last_price:.2f}")
            if smc_df is not None:
                status = "Bullish 🚀" if smc_df['CHoCH_Bull'].iloc[-1] else ("Bearish 🩸" if smc_df['CHoCH_Bear'].iloc[-1] else "Neutral ⚖️")
                st.caption(status)
            else:
                st.caption("Analyzing...")
                
        # عرض التفاصيل فـ أسفل الصفحة إيلا كليكيتي
        with st.expander(f"Details for {name}"):
            if smc_df is not None:
                c1, c2 = st.columns(2)
                with c1:
                    st.write("**Signals:**")
                    if smc_df['FVG_Bull'].tail(10).any(): st.success("FVG Found")
                with c2:
                    st.write("**Structure:**")
                    if smc_df['OB_Bull'].tail(10).any(): st.info("Order Block Found")
    else:
        with cols[i]:
            st.metric(label=name.split()[0], value="OFFLINE")

st.caption(f"Last Sync: {datetime.now().strftime('%H:%M:%S')} | Source: Spot Market Data")
