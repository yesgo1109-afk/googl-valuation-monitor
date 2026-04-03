import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 設定網頁標題與圖示
st.set_page_config(page_title="GOOGL 估值監控儀表板", layout="wide")

# 自定義 CSS 讓介面更有金融終端機的質感
st.markdown("""
    <style>
    .main { background-color: #0d0f12; color: #e8eaf0; }
    .stMetric { background-color: #1a1e25; padding: 15px; border-radius: 10px; border: 1px solid #2d323d; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 數據抓取函式 (這就是大腦) ---
@st.cache_data(ttl=3600)  # 快取功能：一小時內重複開啟網頁不會重新抓取，節省資源
def get_stock_data(ticker):
    data = yf.Ticker(ticker)
    curr = data.history(period="1d")['Close'].iloc[-1]
    return round(curr, 2)

# --- 2. 側邊欄：假設參數調整 (讓你領會模型如何連動) ---
st.sidebar.header("📊 估值模型參數")
st.sidebar.write("你可以手動調整以下數值觀察目標價變化")

# 相對估值參數
pe_mult = st.sidebar.slider("相對估值 (P/E 倍數)", 15.0, 30.0, 22.0)
# SOTP 參數
cloud_mult = st.sidebar.slider("雲端業務 (EV/Sales)", 10.0, 20.0, 14.0)
search_mult = st.sidebar.slider("搜尋業務 (EV/Sales)", 10.0, 20.0, 16.0)

# --- 3. 核心邏輯計算 ---
try:
    current_price = get_stock_data("GOOGL")
    
    # 模型 A: 相對估值 (假設 EPS 10.81)
    val_relative = 10.81 * pe_mult
    
    # 模型 B: SOTP 分部加總 (假設營收數據)
    # 公式：(搜尋價值 + 雲端價值 + 其他) / 股數
    val_sotp = ((95 * search_mult) + (58.7 * cloud_mult) + (60 * 9) + 50) / 12.3
    
    # 模型 C: DCF (簡化設定值)
    val_dcf = 195.0 
    
    # 綜合目標價 (加權平均：SOTP 佔 50%, 相對 30%, DCF 20%)
    target_price = (val_relative * 0.3) + (val_sotp * 0.5) + (val_dcf * 0.2)

    # --- 4. 網頁前端顯示 ---
    st.title("🚀 Alphabet (GOOGL) 估值監控儀表板")
    st.write(f"數據最後更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 第一排：核心指標
    col1, col2, col3, col4 = st.columns(4
