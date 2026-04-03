import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

# 1. 網頁基本設定 (明亮模式)
st.set_page_config(page_title="GOOGL 精準估值監控", layout="wide")

st.title("📊 Alphabet (GOOGL) 專業估值儀表板")
st.markdown("---")

# 2. 抓取即時數據 (大腦部分)
@st.cache_data(ttl=3600) # 快取一小時，符合你「不需秒秒更新」的需求
def get_stock_data():
    ticker = "GOOGL"
    data = yf.Ticker(ticker).history(period="1d")
    return data['Close'].iloc[-1]

try:
    current_price = get_stock_data()
except:
    current_price = 295.77  # 萬一網路斷掉的備用數值

# 3. 側邊欄：調整假設 (拉桿部分)
st.sidebar.header("⚙️ 模型參數調整")
pe_ratio = st.sidebar.slider("相對估值：預期 P/E", 15.0, 35.0, 22.0)
cloud_mult = st.sidebar.slider("SOTP：雲端業務倍數", 5.0, 25.0, 14.0)
dcf_val = st.sidebar.number_input("DCF：內在價值設定", value=220.0)

# 4. 估值邏輯計算
# 模型 A: 相對估值 (假設 EPS 10.81)
val_relative = 10.81 * pe_ratio

# 模型 B: SOTP 分部加總 (簡化公式)
val_sotp = ((95 * 16) + (58.7 * cloud_mult) + 100) / 12.3

# 模型 C: 綜合目標 (權重分配)
composite_price = (val_relative * 0.4) + (val_sotp * 0.4) + (dcf_val * 0.2)

# 5. 視覺化圖表 (配色與級距優化)
# 準備數據表
df_plot = pd.DataFrame({
    '模型名稱': ['1. 相對估值', '2. SOTP 加總', '3. DCF 價值', '4. 綜合目標'],
    '估值金額': [val_relative, val_sotp, dcf_val, composite_price],
    '顏色': ['#FF4B4B', '#00CC96', '#1F77B4', '#9467BD'] # 高對比配色
})

# 計算座標軸顯示範圍 (解決級距太寬的問題)
all_values = [val_relative, val_sotp, dcf_val, composite_price, current_price]
y_min = min(all_values) * 0.95
y_max = max(all_values) * 1.05

# 畫長條圖
bars = alt.Chart(df_plot).mark_bar(size=60, cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
    x=alt.X('模型名稱:N', axis=alt.Axis(labelAngle=0, title=None)),
    y=alt.Y('估值金額:Q', title='美金 ($)', scale=alt.Scale(domain=[y_min, y_max])),
    color=alt.Color('顏色:N', scale=None)
).properties(height=500)

# 畫現價虛線 (亮橘色，加粗)
price_line = alt.Chart(pd.DataFrame({'y': [current_price]})).mark_rule(
    color='#FF8C00', strokeWidth=4, strokeDash=[8, 4]
).encode(y='y:Q')

# 現價標籤 (顯示在線的旁邊)
price_label = alt.Chart(pd.DataFrame({'y': [current_price], 't': [f'➔ 目前現價: ${current_price:.2f}']})).mark_text(
    align='left', dx=10, dy=-15, fontSize=18, fontWeight='bold', color='#FF8C00'
).encode(y='y:Q', text='t:N')

# 6. 呈現結果
col1, col2 = st.columns([3, 1])

with col1:
    st.altair_chart(bars + price_line + price_label, use_container_width=True)

with col2:
    st.metric("目前股價", f"${current_price:.2f}")
    st.metric("綜合合理價", f"${composite_price:.2f}")
    
    diff = ((current_price / composite_price) - 1) * 100
    st.metric("溢價/折價 %", f"{diff:.2f}%", delta=f"{diff:.2f}%", delta_color="inverse")
    
    if current_price > composite_price:
        st.error("⚠️ 目前股價偏高")
    else:
        st.success("✅ 具備安全邊際")

st.info(f"💡 數據領會：目前現價與綜合目標價的距離為 {abs(current_price - composite_price):.2f} 美元。")
