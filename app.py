import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

# 1. 網頁基本設定
st.set_page_config(page_title="GOOGL 精準估值監控", layout="wide")

st.title("📊 Alphabet (GOOGL) 專業估值儀表板")
st.markdown("---")

# 2. 抓取即時數據
@st.cache_data(ttl=3600)
def get_stock_data():
    ticker = "GOOGL"
    data = yf.Ticker(ticker).history(period="1d")
    return data['Close'].iloc[-1]

try:
    current_price = get_stock_data()
except:
    current_price = 295.77 

# 3. 側邊欄：調整假設
st.sidebar.header("⚙️ 模型參數調整")
pe_ratio = st.sidebar.slider("1. 相對估值：預期 P/E", 15.0, 35.0, 22.0)
cloud_mult = st.sidebar.slider("2. SOTP：雲端業務倍數", 5.0, 25.0, 14.0)
# 這個 220 是你可以手動調整的 DCF 基礎值
dcf_val = st.sidebar.number_input("3. DCF：手動設定內在價值", value=220.0, step=1.0)

# 4. 估值邏輯計算
val_relative = 10.81 * pe_ratio
val_sotp = ((95 * 16) + (58.7 * cloud_mult) + 100) / 12.3
# 綜合合理價：採加權平均 (可依個人喜好調整權重)
composite_price = (val_relative * 0.4) + (val_sotp * 0.4) + (dcf_val * 0.2)

# 5. 視覺化圖表與表格數據準備
plot_data = [
    {'模型名稱': '1. 相對估值', '估值金額': val_relative, 'color': '#FF4B4B'},
    {'模型名稱': '2. SOTP 加總', '估值金額': val_sotp, 'color': '#00CC96'},
    {'模型名稱': '3. DCF 價值', '估值金額': dcf_val, 'color': '#1F77B4'},
    {'模型名稱': '4. 綜合目標', '估值金額': composite_price, 'color': '#9467BD'}
]
df_plot = pd.DataFrame(plot_data)

# 修正序號：從 1 開始，且不顯示顏色欄位
df_display = df_plot[['模型名稱', '估值金額']].copy()
df_display.index = range(1, len(df_display) + 1)
df_display['估值金額'] = df_display['估值金額'].map('${:,.2f}'.format)

# 計算座標軸顯示範圍
all_values = [val_relative, val_sotp, dcf_val, composite_price, current_price]
y_min = min(all_values) * 0.95
y_max = max(all_values) * 1.05

# 畫長條圖
bars = alt.Chart(df_plot).mark_bar(size=60, cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
    x=alt.X('模型名稱:N', axis=alt.Axis(labelAngle=0, title=None)),
    y=alt.Y('估值金額:Q', title='美金 ($)', scale=alt.Scale(domain=[y_min, y_max])),
    color=alt.Color('color:N', scale=None)
).properties(height=500)

# 畫現價虛線
price_line = alt.Chart(pd.DataFrame({'y': [current_price]})).mark_rule(
    color='#FF8C00', strokeWidth=4, strokeDash=[8, 4]
).encode(y='y:Q')

# 現價標籤
price_label = alt.Chart(pd.DataFrame({'y': [current_price], 't': [f'➔ 目前現價: ${current_price:.2f}']})).mark_text(
    align='left', dx=10, dy=-15, fontSize=18, fontWeight='bold', color='#FF8C00'
).encode(y='y:Q', text='t:N')

# 6. 呈現結果
col1, col2 = st.columns([3, 1])

with col1:
    st.altair_chart(bars + price_line + price_label, use_container_width=True)
    st.write("### 📋 估值數據明細")
    # 這裡顯示修改後的表格
    st.table(df_display)

with col2:
    st.metric("目前股價", f"${current_price:.2f}")
    st.metric("綜合合理價", f"${composite_price:.2f}")
    
    diff = ((current_price / composite_price) - 1) * 100
    st.metric("溢價/折價 %", f"{diff:.2f}%", delta=f"{diff:.2f}%", delta_color="inverse")
    
    if current_price > composite_price:
        st.error("⚠️ 目前股價偏高")
    else:
        st.success("✅ 具備安全邊際")

st.info(f"💡 數據領會：這是一個『活的』工具，你可以調整左側參數來觀察合理價的變化。")
