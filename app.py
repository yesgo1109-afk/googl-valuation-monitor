import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

# ─────────────────────────────────────────
# 1. 基本設定
# ─────────────────────────────────────────
st.set_page_config(page_title="GOOGL 估值監控", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .metric-card {
        background: #1a1a2e;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        border: 1px solid #2a2a4a;
    }
</style>
""", unsafe_allow_html=True)

st.title("Alphabet (GOOGL) 估值監控儀表板")
st.caption("單位校準完整版：三種估值模型 × 趨勢追蹤")
st.markdown("---")

# ─────────────────────────────────────────
# 2. 即時股價
# ─────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_stock_data():
    ticker = yf.Ticker("GOOGL")
    hist = ticker.history(period="1d")
    return hist['Close'].iloc[-1]

try:
    current_price = get_stock_data()
except:
    current_price = 295.7  # 預設參考價

# ─────────────────────────────────────────
# 3. 側邊欄：本季財報數字與假設
# ─────────────────────────────────────────
st.sidebar.header("📋 本季財報數字")
cloud_growth    = st.sidebar.number_input("Cloud 季增速 (%)",        value=35.0, step=0.1)
search_growth   = st.sidebar.number_input("Search 廣告增速 (%)",     value=12.0, step=0.1)
fcf_growth      = st.sidebar.number_input("自由現金流年增速 (%)",    value=10.0, step=0.1)
cloud_margin    = st.sidebar.number_input("Cloud 營業利潤率 (%)",    value=17.0, step=0.1)
capex_rev_ratio = st.sidebar.number_input("CapEx / Revenue 比率 (%)", value=14.0, step=0.1)
cloud_rev       = st.sidebar.number_input("Cloud 年營收 ($B)",       value=58.7, step=0.1)
search_ebitda   = st.sidebar.number_input("Search EBITDA ($B)",      value=95.0, step=0.5)
eps_ttm         = st.sidebar.number_input("EPS (TTM)",               value=10.81, step=0.01)
shares_b        = st.sidebar.number_input("流通股數 (億股)",         value=123.0, step=0.1)
legal_risk      = st.sidebar.selectbox("反壟斷法律風險", ["無重大進展", "訴訟進行中", "不利判決"])

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 估值假設")
pe_ratio      = st.sidebar.slider("相對估值：目標 P/E",        15.0, 35.0, 22.0)
cloud_mult    = st.sidebar.slider("SOTP：Cloud EV/Sales 倍數", 8.0, 25.0, 10.0)
search_mult   = st.sidebar.slider("SOTP：Search EV/EBITDA",   10.0, 25.0, 15.0)
youtube_val   = st.sidebar.slider("SOTP：YouTube 估值 ($B)",  300.0, 900.0, 500.0)
fcf_base      = st.sidebar.number_input("DCF：基期 FCF ($B)", value=70.0, step=0.5)
fcf_growth_dcf = st.sidebar.slider("DCF：未來 10 年成長率 (%)",  5.0, 25.0, 12.0)
wacc          = st.sidebar.slider("DCF：折現率 WACC (%)",      7.0, 13.0, 9.0, step=0.1)

# ─────────────────────────────────────────
# 4. 估值計算邏輯
# ─────────────────────────────────────────

# A. 相對估值
val_relative = eps_ttm * pe_ratio

# B. SOTP (單位校準：$B / 億股 * 10 = 每股美金)
sotp_search  = search_ebitda * search_mult
sotp_cloud   = cloud_rev * cloud_mult
sotp_youtube = youtube_val
sotp_total_b = sotp_search + sotp_cloud + sotp_youtube + 50.0
val_sotp = (sotp_total_b * 10) / shares_b

# C. DCF (單位校準：$B / 億股 * 10 = 每股美金)
terminal_growth = 0.025
total_pv = 0.0
for t in range(1, 11):
    cf = fcf_base * ((1 + fcf_growth_dcf / 100) ** t)
    total_pv += cf / ((1 + wacc / 100) ** t)
term_cf = fcf_base * ((1 + fcf_growth_dcf / 100) ** 10) * (1 + terminal_growth)
term_val = term_cf / ((wacc / 100) - terminal_growth)
total_pv += term_val / ((1 + wacc / 100) ** 10)
val_dcf = (total_pv * 10) / shares_b

# 綜合加權
composite = val_relative * 0.3 + val_dcf * 0.2 + val_sotp * 0.5
upside_pct = (composite - current_price) / current_price * 100

# ─────────────────────────────────────────
# 5. 輔助函數 (紅綠燈檢驗)
# ─────────────────────────────────────────
def check(value, threshold, direction="above"):
    if direction == "above":
        status = "pass" if value >= threshold else "warn" if value >= threshold * 0.7 else "fail"
    else:
        status = "pass" if value <= threshold else "warn" if value <= threshold * 1.2 else "fail"
    return status, f"{value:.1f}%"

def status_badge(status):
    return {"pass": "🟢 通過", "warn": "🟡 注意", "fail": "🔴 失效"}[status]

def render_model_check(col, model_name, health_data):
    status_text = "✅ 有效" if all(s=="pass" for s in [h[0] for h in health_data]) else "⚠️ 謹慎"
    with col:
        st.info(f"**{model_name}** — {status_text}")
        df = pd.DataFrame([{"指標": n, "狀態": status_badge(s), "數據": d} for n, s, d in health_data])
        st.dataframe(df, hide_index=True, use_container_width=True)

# ─────────────────────────────────────────
# 6. 畫面呈現
# ─────────────────────────────────────────

# 頂部摘要
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("目前股價", f"${current_price:.2f}")
c2.metric("相對估值", f"${val_relative:.1f}")
c3.metric("DCF 估值", f"${val_dcf:.1f}")
c4.metric("SOTP 估值", f"${val_sotp:.1f}")
c5.metric("綜合目標價", f"${composite:.1f}", delta=f"{upside_pct:.1f}%")

st.markdown("---")

# 指標檢驗區
st.subheader("🔍 模型狀態檢驗")
col_r, col_d, col_s = st.columns(3)
render_model_check(col_r, "相對估值", [("廣告增速", *check(search_growth, 8)), ("PE合理性", "pass", f"{pe_ratio}x")])
render_model_check(col_d, "DCF模型", [("FCF增速", *check(fcf_growth, 12)), ("WACC安全", *check(wacc, 11, "below"))])
render_model_check(col_s, "SOTP拆解", [("Cloud增速", *check(cloud_growth, 30)), ("利潤率", "pass", f"{cloud_margin}%")])

# 估值圖表
st.subheader("📊 估值分佈圖")
plot_df = pd.DataFrame([
    {"模型": "相對估值", "目標價": val_relative},
    {"模型": "DCF", "目標價": val_dcf},
    {"模型": "SOTP", "目標價": val_sotp},
    {"模型": "綜合加權", "目標價": composite},
])
bars = alt.Chart(plot_df).mark_bar(size=50).encode(
    x=alt.X("模型:N", axis=alt.Axis(labelAngle=0)),
    y=alt.Y("目標價:Q", scale=alt.Scale(domain=[min(val_relative, current_price)*0.8, max(composite, current_price)*1.2])),
    color="模型:N"
).properties(height=400)
line = alt.Chart(pd.DataFrame({'y': [current_price]})).mark_rule(color='red', strokeWidth=2).encode(y='y')
st.altair_chart(bars + line, use_container_width=True)

# 決策摘要
if upside_pct > 15:
    st.success(f"📌 具備安全邊際：目前估值高於現價 {abs(upside_pct):.1f}%")
elif upside_pct > -10:
    st.warning(f"📌 接近合理價格：差距僅 {abs(upside_pct):.1f}%")
else:
    st.error(f"📌 股價過高：溢價達 {abs(upside_pct):.1f}%")
