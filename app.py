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
    .section-header {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        color: #888;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("Alphabet (GOOGL) 估值監控儀表板")
st.caption("三種估值模型 × 指標檢驗 × 季度趨勢")
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
# 3. 側邊欄：分為「本季財報數字」和「估值假設」
# ─────────────────────────────────────────
st.sidebar.header("📋 本季財報數字")
st.sidebar.caption("每季財報後更新這區，程式自動判斷模型狀態")

cloud_growth    = st.sidebar.number_input("Cloud 季增速 (%)",        value=48.0, step=0.1)
search_growth   = st.sidebar.number_input("Search 廣告增速 (%)",     value=17.0, step=0.1)
fcf_growth      = st.sidebar.number_input("自由現金流年增速 (%)",    value=0.7,  step=0.1)
cloud_margin    = st.sidebar.number_input("Cloud 營業利潤率 (%)",    value=17.0, step=0.1)
capex_rev_ratio = st.sidebar.number_input("CapEx / Revenue 比率 (%)", value=16.0, step=0.1)
cloud_rev       = st.sidebar.number_input("Cloud 年營收 ($B)",       value=58.7, step=0.1)
search_ebitda   = st.sidebar.number_input("Search EBITDA ($B)",      value=95.0, step=0.5)
eps_ttm         = st.sidebar.number_input("EPS（TTM）",               value=10.81, step=0.01)
shares_b        = st.sidebar.number_input("流通股數（億股）",         value=123.0, step=0.5)
legal_risk      = st.sidebar.selectbox("反壟斷法律風險",
                    ["無重大進展", "訴訟進行中", "不利判決"])

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 估值假設")

pe_ratio      = st.sidebar.slider("相對估值：目標 P/E",        15.0, 35.0, 20.0)
cloud_mult    = st.sidebar.slider("SOTP：Cloud EV/Sales 倍數", 8.0, 25.0, 14.0)
search_mult   = st.sidebar.slider("SOTP：Search EV/EBITDA",   10.0, 25.0, 16.0)
youtube_val   = st.sidebar.slider("SOTP：YouTube 估值 ($B)",  300.0, 900.0, 600.0)
fcf_base      = st.sidebar.number_input("DCF：基期 FCF ($B)", value=73.3, step=0.5)
fcf_growth_dcf = st.sidebar.slider("DCF：FCF 成長率 (%)",     5.0, 25.0, 13.0)
wacc          = st.sidebar.slider("DCF：折現率 WACC (%)",     7.0, 13.0, 9.5, step=0.1)

# ─────────────────────────────────────────
# 4. 估值計算
# ─────────────────────────────────────────

# 相對估值
val_relative = eps_ttm * pe_ratio

# SOTP
sotp_search  = search_ebitda * search_mult
sotp_cloud   = cloud_rev * cloud_mult
sotp_youtube = youtube_val
sotp_other   = 50.0
sotp_total_b = sotp_search + sotp_cloud + sotp_youtube + sotp_other
val_sotp     = sotp_total_b / (shares_b / 10)   # $B → per share

# DCF（10年 + 終值）
terminal_growth = 0.03
total_pv = 0.0
for t in range(1, 11):
    cf = fcf_base * ((1 + fcf_growth_dcf / 100) ** t)
    total_pv += cf / ((1 + wacc / 100) ** t)
terminal_cf  = fcf_base * ((1 + fcf_growth_dcf / 100) ** 10) * (1 + terminal_growth)
terminal_val = terminal_cf / ((wacc / 100) - terminal_growth)
total_pv    += terminal_val / ((1 + wacc / 100) ** 10)
val_dcf      = (total_pv / (shares_b / 10)) * 1000   # $B → per share

# 綜合加權
composite = val_relative * 0.3 + val_dcf * 0.2 + val_sotp * 0.5
upside_pct = (composite - current_price) / current_price * 100

# ─────────────────────────────────────────
# 5. 指標檢驗邏輯
# ─────────────────────────────────────────

def check(value, threshold, direction="above", label=""):
    """回傳 (pass/warn/fail, 說明文字)"""
    if direction == "above":
        if value >= threshold:
            return "pass", f"{value:.1f}% ≥ 門檻 {threshold}%"
        elif value >= threshold * 0.7:
            return "warn", f"{value:.1f}% 接近門檻 {threshold}%"
        else:
            return "fail", f"{value:.1f}% 低於門檻 {threshold}%"
    elif direction == "below":
        if value <= threshold:
            return "pass", f"{value:.1f}% ≤ 門檻 {threshold}%"
        elif value <= threshold * 1.2:
            return "warn", f"{value:.1f}% 略超門檻 {threshold}%"
        else:
            return "fail", f"{value:.1f}% 遠超門檻 {threshold}%"
    elif direction == "improving":
        if value > 0:
            return "pass", f"+{value:.1f}%，持續改善"
        elif value > -5:
            return "warn", f"{value:.1f}%，趨於停滯"
        else:
            return "fail", f"{value:.1f}%，明顯惡化"

def legal_check(risk):
    if risk == "無重大進展":
        return "pass", "無分拆風險"
    elif risk == "訴訟進行中":
        return "warn", "法律不確定性存在"
    else:
        return "fail", "重大不利判決"

def status_badge(status):
    if status == "pass":
        return "🟢 通過"
    elif status == "warn":
        return "🟡 注意"
    else:
        return "🔴 失效"

def model_health(checks):
    """根據各項檢驗回傳模型整體狀態"""
    statuses = [c[0] for c in checks]
    if all(s == "pass" for s in statuses):
        return "✅ 有效", "success"
    elif "fail" in statuses:
        return "❌ 失效", "error"
    else:
        return "⚠️ 謹慎", "warning"

# 各模型的指標檢驗
checks_relative = [
    ("Search 廣告增速",   *check(search_growth,   8,  "above")),
    ("P/E 折價 vs 同業",  *check(23 - pe_ratio,   3,  "above")),  # 同業約23x
    ("反壟斷法律風險",    *legal_check(legal_risk)),
]

checks_dcf = [
    ("FCF 年增速",         *check(fcf_growth,      12, "above")),
    ("CapEx/Revenue 比率", *check(capex_rev_ratio, 18, "below")),
    ("WACC 環境",          *check(wacc,            11, "below")),
]

checks_sotp = [
    ("Cloud 季增速",      *check(cloud_growth,  30, "above")),
    ("Cloud 利潤率趨勢",  *check(cloud_margin,   0, "improving")),
    ("Cloud 增速加速",    *check(cloud_growth - 30, 0, "above")),
]

health_relative, type_relative = model_health(checks_relative)
health_dcf,      type_dcf      = model_health(checks_dcf)
health_sotp,     type_sotp     = model_health(checks_sotp)

# ─────────────────────────────────────────
# 6. 歷史數據（手動維護，每季加一筆）
# ─────────────────────────────────────────
history = pd.DataFrame([
    {"季度": "Q1'24", "Cloud增速": 28, "Search增速": 15, "FCF增速":  8, "Cloud利潤率": 9,  "股價": 165, "相對估值": 170, "DCF估值": 175, "SOTP估值": 180},
    {"季度": "Q2'24", "Cloud增速": 29, "Search增速": 14, "FCF增速":  6, "Cloud利潤率": 11, "股價": 175, "相對估值": 172, "DCF估值": 173, "SOTP估值": 182},
    {"季度": "Q3'24", "Cloud增速": 35, "Search增速": 12, "FCF增速":  5, "Cloud利潤率": 13, "股價": 168, "相對估值": 175, "DCF估值": 178, "SOTP估值": 195},
    {"季度": "Q4'24", "Cloud增速": 30, "Search增速": 13, "FCF增速": 10, "Cloud利潤率": 14, "股價": 190, "相對估值": 180, "DCF估值": 185, "SOTP估值": 210},
    {"季度": "Q4'25", "Cloud增速": 48, "Search增速": 17, "FCF增速":  1, "Cloud利潤率": 17, "股價": 297, "相對估值": int(val_relative), "DCF估值": int(val_dcf), "SOTP估值": int(val_sotp)},
])

# ─────────────────────────────────────────
# 7. 畫面呈現
# ─────────────────────────────────────────

# ── 頂部摘要指標 ──
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("目前股價",   f"${current_price:.2f}")
c2.metric("相對估值",   f"${val_relative:.0f}")
c3.metric("DCF 估值",   f"${val_dcf:.0f}")
c4.metric("SOTP 估值",  f"${val_sotp:.0f}")
delta_label = f"{'▲' if upside_pct > 0 else '▼'} {abs(upside_pct):.1f}%"
c5.metric("綜合目標價", f"${composite:.0f}",
          delta=delta_label,
          delta_color="normal" if upside_pct > 0 else "inverse")

st.markdown("---")

# ── Section A：指標檢驗 ──
st.subheader("🔍 指標檢驗 — 三種模型當季狀態")
st.caption("根據本季財報數字，自動判斷每個估值模型的成立條件是否達標")

col_r, col_d, col_s = st.columns(3)

def render_model_check(col, model_name, color, health_text, health_type, checks):
    with col:
        if health_type == "success":
            st.success(f"**{model_name}** — {health_text}")
        elif health_type == "warning":
            st.warning(f"**{model_name}** — {health_text}")
        else:
            st.error(f"**{model_name}** — {health_text}")

        rows = []
        for name, status, desc in checks:
            rows.append({
                "指標":   name,
                "狀態":   status_badge(status),
                "說明":   desc,
            })
        df_check = pd.DataFrame(rows)
        st.dataframe(df_check, hide_index=True, use_container_width=True)

render_model_check(col_r, "相對估值", "blue",  health_relative, type_relative, checks_relative)
render_model_check(col_d, "DCF",      "teal",  health_dcf,      type_dcf,      checks_dcf)
render_model_check(col_s, "SOTP",     "amber", health_sotp,     type_sotp,     checks_sotp)

st.markdown("---")

# ── Section B：估值比較圖 ──
st.subheader("📊 估值比較 vs 當前股價")

plot_data = pd.DataFrame([
    {"模型": "相對估值", "目標價": round(val_relative, 1)},
    {"模型": "DCF",      "目標價": round(val_dcf, 1)},
    {"模型": "SOTP",     "目標價": round(val_sotp, 1)},
    {"模型": "綜合加權", "目標價": round(composite, 1)},
])

y_min = min(plot_data["目標價"].min(), current_price) * 0.92
y_max = max(plot_data["目標價"].max(), current_price) * 1.06

bars = alt.Chart(plot_data).mark_bar(
    cornerRadiusTopLeft=5, cornerRadiusTopRight=5, size=55
).encode(
    x=alt.X("模型:N", axis=alt.Axis(labelAngle=0, title=None)),
    y=alt.Y("目標價:Q", scale=alt.Scale(domain=[y_min, y_max]), title="美金 ($)"),
    color=alt.Color("模型:N", scale=alt.Scale(
        domain=["相對估值", "DCF", "SOTP", "綜合加權"],
        range=["#4a9eff", "#2fd4a0", "#f0a832", "#b388ff"]
    )),
    tooltip=["模型", "目標價"]
).properties(height=380)

price_line = alt.Chart(pd.DataFrame({"y": [current_price]})).mark_rule(
    color="#ff6b6b", strokeWidth=3, strokeDash=[6, 3]
).encode(y="y:Q")

price_label = alt.Chart(pd.DataFrame({
    "y": [current_price],
    "t": [f"現價 ${current_price:.2f}"]
})).mark_text(
    align="left", dx=8, dy=-12, fontSize=14, fontWeight="bold", color="#ff6b6b"
).encode(y="y:Q", text="t:N")

st.altair_chart(bars + price_line + price_label, use_container_width=True)

# SOTP 拆解
with st.expander("📂 SOTP 分部拆解明細"):
    sotp_detail = pd.DataFrame([
        {"業務":   "Search / 廣告",
         "營收基礎": f"EBITDA ${search_ebitda:.0f}B",
         "倍數":    f"{search_mult:.0f}x EV/EBITDA",
         "估值":    f"${sotp_search:.0f}B"},
        {"業務":   "Google Cloud",
         "營收基礎": f"Revenue ${cloud_rev:.1f}B",
         "倍數":    f"{cloud_mult:.0f}x EV/Sales",
         "估值":    f"${sotp_cloud:.0f}B"},
        {"業務":   "YouTube",
         "營收基礎": "廣告+訂閱 $60B+",
         "倍數":    "直接估值",
         "估值":    f"${sotp_youtube:.0f}B"},
        {"業務":   "Other Bets",
         "營收基礎": "Waymo 等",
         "倍數":    "折扣估值",
         "估值":    f"${sotp_other:.0f}B"},
        {"業務":   "合計",
         "營收基礎": "",
         "倍數":    "",
         "估值":    f"${sotp_total_b:.0f}B → ${val_sotp:.0f}/股"},
    ])
    st.dataframe(sotp_detail, hide_index=True, use_container_width=True)

st.markdown("---")

# ── Section C：歷史趨勢圖 ──
st.subheader("📈 歷史趨勢 — 季度追蹤")
st.caption("方向比單季數字更重要")

tab1, tab2, tab3 = st.tabs(["Cloud & Search 增速", "FCF & 利潤率", "估值 vs 股價"])

with tab1:
    df_melt = history.melt(
        id_vars="季度",
        value_vars=["Cloud增速", "Search增速"],
        var_name="指標", value_name="數值"
    )
    threshold_cloud = pd.DataFrame({
        "季度":  history["季度"],
        "數值":  [30] * len(history),
        "指標":  ["Cloud門檻30%"] * len(history)
    })
    threshold_search = pd.DataFrame({
        "季度":  history["季度"],
        "數值":  [8] * len(history),
        "指標":  ["Search門檻8%"] * len(history)
    })
    df_all = pd.concat([df_melt, threshold_cloud, threshold_search])

    line = alt.Chart(df_melt).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X("季度:N", sort=None),
        y=alt.Y("數值:Q", title="%"),
        color=alt.Color("指標:N", scale=alt.Scale(
            domain=["Cloud增速", "Search增速"],
            range=["#f0a832", "#4a9eff"]
        )),
        tooltip=["季度", "指標", "數值"]
    )
    th_cloud = alt.Chart(threshold_cloud).mark_line(
        strokeDash=[4, 4], strokeWidth=1.5, color="#f0a832", opacity=0.5
    ).encode(x=alt.X("季度:N", sort=None), y="數值:Q")
    th_search = alt.Chart(threshold_search).mark_line(
        strokeDash=[4, 4], strokeWidth=1.5, color="#4a9eff", opacity=0.5
    ).encode(x=alt.X("季度:N", sort=None), y="數值:Q")

    st.altair_chart((line + th_cloud + th_search).properties(height=320),
                    use_container_width=True)

with tab2:
    df_melt2 = history.melt(
        id_vars="季度",
        value_vars=["FCF增速", "Cloud利潤率"],
        var_name="指標", value_name="數值"
    )
    line2 = alt.Chart(df_melt2).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X("季度:N", sort=None),
        y=alt.Y("數值:Q", title="%"),
        color=alt.Color("指標:N", scale=alt.Scale(
            domain=["FCF增速", "Cloud利潤率"],
            range=["#2fd4a0", "#b388ff"]
        )),
        tooltip=["季度", "指標", "數值"]
    )
    st.altair_chart(line2.properties(height=320), use_container_width=True)
    st.caption("FCF增速門檻 12%；Cloud利潤率持續上升才算SOTP有效")

with tab3:
    df_melt3 = history.melt(
        id_vars="季度",
        value_vars=["股價", "相對估值", "DCF估值", "SOTP估值"],
        var_name="指標", value_name="數值"
    )
    colors = {
        "股價":   "#ff6b6b",
        "相對估值": "#4a9eff",
        "DCF估值":  "#2fd4a0",
        "SOTP估值": "#f0a832",
    }
    line3 = alt.Chart(df_melt3).mark_line(point=True, strokeWidth=2).encode(
        x=alt.X("季度:N", sort=None),
        y=alt.Y("數值:Q", title="美金 ($)"),
        color=alt.Color("指標:N", scale=alt.Scale(
            domain=list(colors.keys()),
            range=list(colors.values())
        )),
        strokeDash=alt.condition(
            alt.datum["指標"] == "股價",
            alt.value([1, 0]),
            alt.value([4, 3])
        ),
        tooltip=["季度", "指標", "數值"]
    )
    st.altair_chart(line3.properties(height=320), use_container_width=True)
    st.caption("股價超出所有估值區間時，需重新審視敘事是否已切換")

st.markdown("---")

# ── Section D：決策摘要 ──
st.subheader("🧭 當季決策摘要")

pass_count = sum(1 for checks in [checks_relative, checks_dcf, checks_sotp]
                 for _, status, _ in checks if status == "pass")
total_count = sum(len(c) for c in [checks_relative, checks_dcf, checks_sotp])
warn_count  = sum(1 for checks in [checks_relative, checks_dcf, checks_sotp]
                  for _, status, _ in checks if status == "warn")
fail_count  = sum(1 for checks in [checks_relative, checks_dcf, checks_sotp]
                  for _, status, _ in checks if status == "fail")

col_a, col_b = st.columns([2, 1])

with col_a:
    st.markdown(f"""
    **指標通過率：{pass_count}/{total_count}**

    - 🟢 通過：{pass_count} 項
    - 🟡 注意：{warn_count} 項
    - 🔴 失效：{fail_count} 項

    **有效模型建議權重：**
    - 相對估值 30%（{health_relative}）
    - DCF 20%（{health_dcf}）
    - SOTP 50%（{health_sotp}）

    **綜合目標價：${composite:.0f}**｜目前股價：${current_price:.2f}
    """)

    if upside_pct > 15:
        st.success(f"📌 股價低於合理估值 {abs(upside_pct):.1f}%，具備安全邊際")
    elif upside_pct > -10:
        st.warning(f"📌 股價接近合理估值（差距 {upside_pct:.1f}%），持有觀察")
    else:
        st.error(f"📌 股價超出合理估值 {abs(upside_pct):.1f}%，需重新審視論點")

with col_b:
    st.markdown("**每季需回答的三個問題：**")
    q1 = "✅" if checks_sotp[0][1] == "pass" else ("⚠️" if checks_sotp[0][1] == "warn" else "❌")
    q2 = "✅" if checks_dcf[0][1] == "pass" else ("⚠️" if checks_dcf[0][1] == "warn" else "❌")
    q3 = "✅" if checks_relative[0][1] == "pass" else ("⚠️" if checks_relative[0][1] == "warn" else "❌")
    st.markdown(f"""
    {q1} Cloud 增速仍在門檻以上？

    {q2} FCF 有沒有穩定成長？

    {q3} 廣告收入有沒有被侵蝕？

    三個都 ✅ → 持有論點成立
    出現 ❌ → 降低對應模型權重
    """)

st.markdown("---")
st.caption("本工具為估值學習用途，不構成投資建議｜資料來源：Alphabet SEC 8-K 財報｜每季財報後更新側邊欄數字")
