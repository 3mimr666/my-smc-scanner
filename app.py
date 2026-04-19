import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- PAGE CONFIGURATION (Optimized for Mobile) ---
st.set_page_config(page_title="SMC Scanner", page_icon="📱", layout="centered", initial_sidebar_state="collapsed")

# Custom CSS for mobile-friendly cards and clean UI
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .metric-card { background-color: #1E2127; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    .bullish { color: #00C853; font-weight: bold; }
    .bearish { color: #FF3D00; font-weight: bold; }
    .title { text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">📱 Live SMC Scanner</div>', unsafe_allow_html=True)

# --- SMC CALCULATION LOGIC ---
def calculate_smc(df):
    """Calculates basic SMC concepts: FVG, Order Blocks, and CHoCH"""
    df = df.copy()
    
    # 1. Fair Value Gaps (FVG)
    # Bullish FVG: Low of candle 3 is higher than High of candle 1
    df['FVG_Bull'] = df['Low'] > df['High'].shift(2)
    # Bearish FVG: High of candle 3 is lower than Low of candle 1
    df['FVG_Bear'] = df['High'] < df['Low'].shift(2)

    # 2. Order Blocks (OB) - Simplified
    # Last opposite candle before a strong impulsive move
    df['Body'] = abs(df['Close'] - df['Open'])
    avg_body = df['Body'].rolling(10).mean()
    
    # Bullish OB (Down candle followed by strong up move)
    df['OB_Bull'] = (df['Close'].shift(1) < df['Open'].shift(1)) & \
                    (df['Close'] > df['Open']) & \
                    (df['Body'] > avg_body * 1.5)
                    
    # Bearish OB (Up candle followed by strong down move)
    df['OB_Bear'] = (df['Close'].shift(1) > df['Open'].shift(1)) & \
                    (df['Close'] < df['Open']) & \
                    (df['Body'] > avg_body * 1.5)

    # 3. Change of Character (CHoCH) - Break of 20-period structure
    df['Max_20'] = df['High'].shift(1).rolling(20).max()
    df['Min_20'] = df['Low'].shift(1).rolling(20).min()
    df['CHoCH_Bull'] = df['Close'] > df['Max_20']
    df['CHoCH_Bear'] = df['Close'] < df['Min_20']

    return df

# --- DATA FETCHING ---
@st.cache_data(ttl=60) # Refreshes every 60 seconds automatically
def get_data(ticker):
    # Using Yahoo Finance: XAUUSD=X for Gold, EURUSD=X for Euro
    tkr = yf.Ticker(ticker)
    df = tkr.history(period="5d", interval="15m")
    if not df.empty:
        return calculate_smc(df)
    return pd.DataFrame()

# --- UI DASHBOARD ---
# Add a manual refresh button
if st.button("🔄 Refresh Live Data", use_container_width=True):
    st.cache_data.clear()

assets = {"XAUUSD": "XAUUSD=X", "EURUSD": "EURUSD=X"}
tabs = st.tabs(["🥇 XAUUSD", "💶 EURUSD"])

for i, (name, ticker) in enumerate(assets.items()):
    with tabs[i]:
        df = get_data(ticker)
        
        if df.empty:
            st.error(f"Failed to fetch data for {name}.")
            continue
            
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Current Price Metric
        price_color = "normal"
        if latest['Close'] > prev['Close']: price_color = "inverse"
        
        st.metric(label=f"Current Price ({name})", 
                  value=f"{latest['Close']:.4f}", 
                  delta=f"{latest['Close'] - prev['Close']:.4f}")

        # --- CHoCH ALERTS ---
        # Look for CHoCH in the last 3 candles to keep the alert relevant
        recent_choch_bull = df['CHoCH_Bull'].iloc[-3:].any()
        recent_choch_bear = df['CHoCH_Bear'].iloc[-3:].any()
        
        if recent_choch_bull:
            st.success(f"🚀 **BULLISH CHoCH DETECTED** on M15 ({name})!")
        elif recent_choch_bear:
            st.error(f"🩸 **BEARISH CHoCH DETECTED** on M15 ({name})!")
        else:
            st.info(f"⏳ No structural breaks (CHoCH) in the last 45 mins.")

        # --- ORDER BLOCKS & FVGs ---
        st.markdown("### 🔍 Latest M15 Signals")
        
        # Find the most recent signals by scanning backwards
        latest_fvg_bull = df[df['FVG_Bull']].index.max()
        latest_fvg_bear = df[df['FVG_Bear']].index.max()
        latest_ob_bull = df[df['OB_Bull']].index.max()
        latest_ob_bear = df[df['OB_Bear']].index.max()

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("#### Fair Value Gaps")
            if pd.notna(latest_fvg_bull):
                st.markdown(f"🟢 **Bullish FVG**<br><small>{latest_fvg_bull.strftime('%b %d, %H:%M')}</small>", unsafe_allow_html=True)
            if pd.notna(latest_fvg_bear):
                st.markdown(f"🔴 **Bearish FVG**<br><small>{latest_fvg_bear.strftime('%b %d, %H:%M')}</small>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("#### Order Blocks")
            if pd.notna(latest_ob_bull):
                st.markdown(f"🟢 **Bullish OB**<br><small>{latest_ob_bull.strftime('%b %d, %H:%M')}</small>", unsafe_allow_html=True)
            if pd.notna(latest_ob_bear):
                st.markdown(f"🔴 **Bearish OB**<br><small>{latest_ob_bear.strftime('%b %d, %H:%M')}</small>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (M15 timeframe)")
