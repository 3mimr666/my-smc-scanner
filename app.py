import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Amimar SMC Pro", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .stMetric { background-color: #1E2127; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Amimar SMC Pro (Final Fix)")

# الرموز - جرب هاد الرمز الجديد للذهب كيعطي داتا Spot مستقرة
assets = {
    "Gold (Spot)": "XAU-USD", # تغيير بسيط ف الرمز باش نجبدو داتا أصح
    "Bitcoin": "BTC-USD",
    "EURUSD": "EURUSD=X",
    "NAS100": "^NDX"
}

def calculate_smc(df):
    if df is None or len(df) < 5: return None
    try:
        df = df.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # تنظيف الداتا من أي قيم خاوية بسباب الويكاند
        df = df.ffill().dropna()

        # حسابات SMC
        df['CHoCH_Bull'] = df['Close'] > df['High'].shift(1).rolling(min(10, len(df))).max()
        df['CHoCH_Bear'] = df['Close'] < df['Low'].shift(1).rolling(10).min()
        
        # FVG & Order Blocks
        df['FVG_Bull'] = (df['Low'] > df['High'].shift(2))
        df['OB_Bull'] = (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Close'] > df['Open'])
        
        return df
    except:
        return None

@st.cache_data(ttl=60)
def fetch_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # كنطلبو داتا كافية للتحليل (7 أيام)
        df = ticker.history(period="7d", interval="1h") # فريم ساعة كيكون أضمن ف الويكاند
        
        if df.empty:
            df = ticker.history(period="1mo", interval="1d")
            
        return df
    except:
        return None

# --- عرض النتائج ---
cols = st.columns(len(assets))

for i, (name, symbol) in enumerate(assets.items()):
    df = fetch_data(symbol)
    smc_df = calculate_smc(df)
    
    with cols[i]:
        if df is not None and not df.empty:
            # كياخد آخر سعر إغلاق حقيقي
            last_price = float(df['Close'].dropna().iloc[-1])
            st.metric(label=name, value=f"{last_price:.2f}")
            
            if smc_df is not None:
                if smc_df['CHoCH_Bull'].iloc[-1]: st.success("Bullish 🚀")
                elif smc_df['CHoCH_Bear'].iloc[-1]: st.error("Bearish 🩸")
                else: st.info("Neutral ⚖️")
            else:
                st.caption("Analyzing Structure...")
        else:
            st.metric(label=name, value="Market Closed")
            st.caption("Waiting for Data")

st.markdown("---")
# تفاصيل التحليل لضمان أنها رجعات
if 'Gold (Spot)' in assets:
    df_gold = fetch_data(assets["Gold (Spot)"])
    smc_gold = calculate_smc(df_gold)
    if smc_gold is not None:
        st.subheader("🔍 Gold SMC Details")
        c1, c2 = st.columns(2)
        with c1:
            if smc_gold['FVG_Bull'].tail(5).any(): st.success("✅ Bullish FVG Found")
            else: st.write("No FVG in current range")
        with c2:
            if smc_gold['OB_Bull'].tail(5).any(): st.info("📦 Order Block Active")
            else: st.write("Scanning for OB...")

st.caption(f"Last Scan: {datetime.now().strftime('%H:%M:%S')} | Spot Analysis Mode")
