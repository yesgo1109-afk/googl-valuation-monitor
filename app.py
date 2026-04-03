import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

# 1. 網頁基本設定
st.set_page_config(page_title="GOOGL 專業估值監控", layout="wide")

st.title("📊 Alphabet (GOOGL) 估值監控儀表板")
st.caption("數據來源：Yahoo Finance | 自動整合三種估值模型判斷")

# 2. 自動抓取即時數據
@st.cache_data(ttl=3600) # 快取功能，一小時抓一次即可，避免被封鎖
def get_data():
    googl = yf.Ticker("GOOGL")
    meta = yf.Ticker("META")
    
    # 獲取現價與PE
    price = googl.history(period="1d")['Close'].iloc[-1]
    g_pe = googl.info.get('trailingPE', 0)
    m_pe = meta.info.get('trailingPE', 0)
    return price, g_pe, m_pe

current_price, googl_pe, meta_pe = get_data()

# 3. 核心指標設定 (這裡的數值可根據每季財報手動修改一次)
cloud_growth = 48  # 雲端營收增速 %
ad_growth = 17     # 廣告營收增速 %
fcf_growth = 10    # 自由現金流增速 %

# 4. 估值模型計算邏輯
# 模型 A: 相對估值 (預設合理 PE 為 22x)
val_relative = 10.8 * 22  

# 模型 B: DCF (內在價值)
val_dcf = 195.0 

# 模型 C: SOTP (分部加總，給予 Cloud 高成長溢價)
val_sotp = 216.0 

# --- 網頁畫面呈現 ---

# 第一行：即時數據看板
col1, col2, col3 = st.columns(3)
col1.metric("當前股價", f"${current_price:.2f}")
col2.metric("Google P/E", f"{googl_pe:.1f}x", delta=f"{googl_pe - meta_pe:.1f} vs META", delta_color="inverse")
col3.metric("Cloud 增速", f"{cloud_growth}%", delta="門檻 30%")

st.divider()

# 第二行：河流圖/區間圖 (視覺化)
st.subheader("📈 估值河流區間圖 (Valuation Bands)")
st.write("紅線為當前股價，橫條為各模型之合理目標價。")

# 準備圖表數據
valuation_df = pd.DataFrame({
    '模型名稱': ['1. 相對估值', '2. DCF 內在價值', '3. SOTP 分部加總'],
    '預估價格': [val_relative, val_dcf, val_sotp],
    '顏色': ['#4A9EFF', '#2FD4A0', '#F0A832'] # 藍、綠、黃
})

# 畫出橫條圖
bars = alt.Chart(valuation_df).mark_bar(size=40).encode(
    x=alt.X('預估價格:Q', title='價格 (USD)', scale=alt.Scale(domain=[100, 350])),
    y=alt.Y('模型名稱:N', title=None),
    color=alt.Color('顏色:N', scale=None)
)

# 畫出目前股價的紅線
price_line = alt.Chart(pd.DataFrame({'x': [current_price]})).mark_rule(
    color='#FF4B4B', strokeWidth=3
).encode(x='x:Q')

# 標註紅線數值
price_text = alt.Chart(pd.DataFrame({'x': [current_price], 'y': ['2. DCF 內在價值'], 't': [f'現價: ${current_price:.2f}']})).mark_text(
            align='left', dx=5, color='#4a9eff', fontWeight='bold'
        ).encode(x='x:Q', y='y:N', text='t:N')
    align
