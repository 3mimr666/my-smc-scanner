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

st.title("📊 Amimar SMC Pro (Fixed Spot Data)")

# الرموز اللي بغيتي
assets = {
    "Gold (Spot)": "XAUUSD=X",
    "Bitcoin": "BTC-USD",
    "EURUSD": "EURUSD=X",
    "NAS100": "^NDX"
}

def calculate_smc(df):
    if df is None or len(df) < 10: return None
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # حسابات SMC سريعة
    df['CHoCH_Bull'] = df['Close'] > df['High'].shift(1).rolling(10).max()
    df['FVG_Bull'] = (df['Low'] > df['High'].shift(2))
    df['OB_Bull'] = (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Close'] > df['Open'])
    return df

@st.cache_data(ttl=300) # كاش لـ 5 دقائق باش ما يتبلوكاوش السيرفرات
def fetch_robust_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        
        # 1. كنحاولوا نجيبو داتا تاريخية قريبة (آخر 7 أيام)
        df = ticker.history(period="7d", interval="1d")
        
        # 2. إيلا الذهب عصل (عطانا خاوي)، كنطلبو "آخر ثمن معروف" بطريقة مباشرة
        if df.empty or df['Close'].isnull().all():
            # كنطلبو داتا قديمة شوية باش نلقاو آخر إغلاق حقيقي
            df = ticker.history(start=(datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'))
            
        return df
    except:
        return None

# --- الـ DASHBOARD ---
cols = st.columns(len(assets))

for i, (name, symbol) in enumerate(assets.items()):
    df = fetch_robust_data(symbol)
    
    with cols[i]:
        if df is not None and not df.empty:
            # تنظيف الداتا من القيم الخاوية (NaN)
            valid_df = df.dropna(subset=['Close'])
            if not valid_df.empty:
                last_price = float(valid_df['Close'].iloc[-1])
                smc_df = calculate_smc(valid_df)
                
                st.metric(label=name, value=f"{last_price:.2f}")
                
                if smc_df is not None:
                    status = "Bullish 🚀" if smc_df['CHoCH_Bull'].iloc[-1] else "Neutral ⚖️"
                    st.caption(status)
                else:
                    st.caption("Hold Position")
            else:
                st.metric(label=name, value="No Data")
        else:
            st.metric(label=name, value="Syncing...")

st.markdown("---")
st.info("ℹ️ هاد النسخة كتجبد آخر سعر إغلاق حقيقي للذهب (Spot) باش ما تبقاش تطلع ليك Offline ف الويكاند.")
st.caption(f"Refreshed: {datetime.now().strftime('%H:%M:%S')}")
