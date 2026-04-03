import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 設定網頁標題與圖示
st.set_page_config(page_title="GOOGL 估值監控儀表板", layout="wide")

# 自定義 CSS
st.markdown("""
    <style>
    .main { background-color: #0d0f12; color: #e8eaf0; }
    .stMetric { background-color: #1a1e25; padding: 15px; border-radius: 10px; border: 1px solid #2d323d; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 數據抓取函式 ---
@st.cache_data(ttl=3600)
def get_stock_data(ticker):
    data = yf.Ticker(ticker)
    curr = data.history(period="1d")['Close'].iloc[-1]
    return round(curr, 2)

# --- 2. 側邊欄參數 ---
st.sidebar.header("📊 估值模型參數")
pe_mult = st.sidebar.slider("相對估值 (P/E 倍數)", 15.0, 30.0, 22.0)
cloud_mult = st.sidebar.slider("雲端業務 (EV/Sales)", 10.0, 20.0, 14.0)
search_mult = st.sidebar.slider("搜尋業務 (EV/Sales)", 10.0, 20.0, 16.0)

# --- 3. 核心邏輯計算 (放在 try 裡面確保安全) ---
try:
    # 這裡所有的程式碼都必須有正確的縮排
    current_price = get_stock_data("GOOGL")
    
    # 模型 A: 相對估值
    val_relative = 10.81 * pe_mult
    
    # 模型 B: SOTP 分部加總
    val_sotp = ((95 * search_mult) + (58.7 * cloud_mult) + (60 * 9) + 50) / 12.3
    
    # 模型 C: DCF
    val_dcf = 195.0 
    
    # 綜合目標價
    target_price = (val_relative * 0.3) + (val_sotp * 0.5) + (val_dcf * 0.2)

    # --- 4. 網頁前端顯示 ---
    st.title("🚀 Alphabet (GOOGL) 估值監控儀表板")
    st.write(f"最後更新: {datetime.now().strftime('%H:%M:%S')}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("目前股價", f"${current_price}")
    col2.metric("綜合目標價", f"${target_price:.2f}")
    
    diff = target_price - current_price
    diff_pct = (diff / current_price) * 100
    col3.metric("潛在空間", f"${diff:.2f}", f"{diff_pct:.2f}%")
    
    status = "✅ 具安全邊際" if diff > 0 else "⚠️ 目前溢價"
    col4.metric("投資狀態", status)

    st.markdown("---")

    # 視覺化圖表
    st.subheader("股價與各模型估值對比")
    fig = go.Figure()
    models = ['相對估值', 'SOTP加總', 'DCF價值', '綜合目標']
    values = [val_relative, val_sotp, val_dcf, target_price]
    
    fig.add_trace(go.Bar(x=models, y=values, marker_color='#4a9eff'))
    fig.add_hline(y=current_price, line_dash="dash", line_color="red", annotation_text=f"現價 ${current_price}")
    
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

# 這是 try 的備案，必須寫在最左邊，不能有縮排
except Exception as e:
    st.error(f"程式執行出錯：{e}")
