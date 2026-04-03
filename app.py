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
st.caption("單位校準精確版：三種估值模型 × 指標檢驗")
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
    current_price = 297.0

# ─────────────────────────────────────────
# 3. 側邊欄
# ─────────────────────────────────────────
st.sidebar.header("📋 本季財報數字")
cloud_growth    = st.sidebar.number_input("Cloud 季增速 (%)",        value=35.0, step=0.1)
search_growth   = st.sidebar.number_input("Search 廣告增速 (%)",     value=12.0, step=0.1)
fcf_growth      = st.sidebar.number_input("自由現金流年增速 (%)",    value=10.0, step=0.1)
cloud_margin    = st.sidebar.number_input("Cloud 營業利潤率 (%)",    value=17.0, step=0.1)
capex_rev_ratio = st.sidebar.number_input("CapEx / Revenue 比率 (%)", value=16.0, step=0.1)
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
fcf_growth_dcf = st.sidebar.slider("DCF：FCF 成長率 (%)",      5.0, 25.0, 12.0)
wacc          = st.sidebar.slider("DCF：折現率 WACC (%)",      7.0, 13.0, 9.0, step=0.1)

# ─────────────────────────────────────────
# 4. 估值計算 (單位校準)
# ─────────────────────────────────────────

# 模型 A：相對估值 ($/股)
val_relative = eps_ttm * pe_ratio

# 模型 B：SOTP (總市值 $B / 億股 * 10 = $/股)
sotp_search  = search_ebitda * search_mult
sotp_cloud   = cloud_rev * cloud_mult
sotp_youtube = youtube_val
sotp_total_b = sotp_search + sotp_cloud + sotp_youtube + 50.0 
val_sotp = (sotp_total_b * 10) / shares_b 

# 模型 C：DCF (標準 10 年模型)
terminal_growth = 0.025 # 永續成長率設為 2.5%
total_pv = 0.0
for t in range(1, 11):
    cf = fcf_base * ((1 + fcf_growth_dcf / 100) ** t)
    total_pv += cf / ((1 + wacc / 100) ** t)
terminal_cf  = fcf_base * ((1 + fcf_growth_dcf / 100) ** 10) * (1 + terminal_growth)
terminal_val = terminal_cf / ((wacc / 100) - terminal_growth)
total_pv    += terminal_val / ((1 + wacc / 100) ** 10)
val_dcf  = (total_pv * 10) / shares_b 

# 綜合加權
composite = val_relative * 0.3 + val_dcf * 0.2 + val_sotp * 0.5
upside_pct = (composite - current_price) / current_price * 100

# ─────────────────────────────────────────
# 5. 指標檢驗邏
