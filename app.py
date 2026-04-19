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

st.title("📊 Amimar SMC Pro Scanner (OANDA Style)")

# الرموز مرتبة
assets = {
    "Gold (XAUUSD)": "XAUUSD=X",
    "Bitcoin (BTC)": "BTC-USD",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "NAS100 (Nasdaq)": "^NDX"
}

def calculate_smc(df):
    if df is None or len(df) < 20: return None
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df['Body'] = (df['Close'] - df['Open']).abs()
    avg_body = df['Body'].rolling(10).mean()
    
    df['FVG_Bull'] = (df['Low'] > df['High'].shift(2))
    df['FVG_Bear'] = (df['High'] < df['Low'].shift(2))
    
    df['OB_Bull'] = (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Close'] > df['Open']) & (df['Body'] > avg_body * 1.5)
    df['OB_Bear'] = (df['Close'].shift(1) > df['Open'].shift(1)) & (df['Close'] < df['Open']) & (df['Body'] > avg_body * 1.5)
    
    df['CHoCH_Bull'] = df['Close'] > df['High'].shift(1).rolling(20).max()
    df['CHoCH_Bear'] = df['Close'] < df['Low'].shift(1).rolling(20).min()
    return df

@st.cache_data(ttl=60)
def fetch_all_data():
    results = {}
    for name, symbol in assets.items():
        try:
            ticker = yf.Ticker(symbol)
            # محاولة جلب البيانات بـ 3 طرق لضمان الظهور
            data = ticker.history(period="5d", interval="15m")
            
            if data.empty:
                data = ticker.history(period="1mo", interval="1d")
            
            # إيلا بقات خاوية، كنصاوبو شمعة وهمية بآخر ثمن معروف (باش ما يغبرش الذهب)
            if data.empty:
                last_price = ticker.fast_info['last_price']
                data = pd.DataFrame([{
                    'Open': last_price, 'High': last_price, 
                    'Low': last_price, 'Close': last_price
                }], index=[datetime.now()])
            
            results[name] = calculate_smc(data)
        except:
            continue
    return results

data_dict = fetch_all_data()

# --- DISPLAY ---
if data_dict:
    cols = st.columns(len(data_dict))
    for i, (name, df) in enumerate(data_dict.items()):
        # استخراج آخر ثمن
        if df is not None:
            current_price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-2]) if len(df) > 1 else current_price
            diff = current_price - prev_price
        else:
            # حالة طارئة إيلا الداتا منعدمة
            t = yf.Ticker(assets[name])
            current_price = t.fast_info['last_price']
            diff = 0

        with cols[i]:
            st.metric(label=name.split()[0], value=f"{current_price:.2f}", delta=f"{diff:.2f}")
            if df is not None:
                status = "Bullish 🚀" if df['CHoCH_Bull'].iloc[-3:].any() else ("Bearish 🩸" if df['CHoCH_Bear'].iloc[-3:].any() else "Neutral ⚖️")
                st.caption(status)

    st.markdown("---")
    # عرض التابات (Tabs)
    valid_keys = [k for k, v in data_dict.items() if v is not None]
    if valid_keys:
        tabs = st.tabs(valid_keys)
        for i, name in enumerate(valid_keys):
            df = data_dict[name]
            with tabs[i]:
                c1, c2 = st.columns(2)
                with c1:
                    if df['CHoCH_Bull'].iloc[-5:].any(): st.success("🚀 Structure: Bullish Break")
                    elif df['CHoCH_Bear'].iloc[-5:].any(): st.error("🩸 Structure: Bearish Break")
                    else: st.write("⚖️ Structure: Range")
                with c2:
                    if df['FVG_Bull'].iloc[-3:].any(): st.info("🟢 FVG Found")
                    if df['OB_Bull'].iloc[-5:].any(): st.info("📦 Order Block Active")

st.caption(f"Last Update: {datetime.now().strftime('%H:%M:%S')} | Forced Price Sync Active")
