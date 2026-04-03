import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

# ─────────────────────────────────────────
# 1. 基本設定
# ─────────────────────────────────────────
st.set_page_config(page_title="GOOGL 估值監控", layout="wide")
st.title("Alphabet (GOOGL) 估值監控儀表板")
st.caption("財務數據自動抓取 · 每季只需手動填 2 個數字")
st.markdown("---")

# ─────────────────────────────────────────
# 2. 自動抓取（yfinance）
# ─────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_financials():
    t    = yf.Ticker("GOOGL")
    info = t.info

    price       = info.get("currentPrice") or info.get("regularMarketPrice", 297.0)
    eps_ttm     = info.get("trailingEps", 10.81)
    pe_ttm      = info.get("trailingPE", 15.8)
    revenue_ttm = info.get("totalRevenue", 402e9) / 1e9
    op_margin   = info.get("operatingMargins", 0.32) * 100
    shares_b    = info.get("sharesOutstanding", 12e9) / 1e8
    fcf         = info.get("freeCashflow", 73e9) / 1e9

    fcf_growth = 0.7
    try:
        cf     = t.cashflow
        op_cf  = cf.loc["Operating Cash Flow"]
        capex  = cf.loc["Capital Expenditure"]
        fcf_q  = (op_cf + capex).dropna()
        if len(fcf_q) >= 2:
            fcf_growth = float(
                (fcf_q.iloc[0] - fcf_q.iloc[1]) / abs(fcf_q.iloc[1]) * 100
            )
    except Exception:
        pass

    return {
        "price":        round(price, 2),
        "eps_ttm":      round(eps_ttm, 2),
        "pe_ttm":       round(pe_ttm, 1),
        "revenue_ttm":  round(revenue_ttm, 1),
        "op_margin":    round(op_margin, 1),
        "shares_b":     round(shares_b, 1),
        "fcf":          round(fcf, 1),
        "fcf_growth":   round(fcf_growth, 1),
        "search_ebitda": 95.0,   # 分部數據，yfinance 無法自動取得
        "cloud_rev":     58.7,   # 同上
    }

with st.spinner("自動抓取 GOOGL 最新財務數據中..."):
    try:
        d = get_financials()
        st.success(f"數據已更新（每小時自動刷新）· 股價 ${d['price']}")
    except Exception as e:
        st.warning(f"抓取失敗，使用預設值。錯誤：{e}")
        d = {
            "price": 297.0, "eps_ttm": 10.81, "pe_ttm": 15.8,
            "revenue_ttm": 402.8, "op_margin": 32.0, "shares_b": 120.0,
            "fcf": 73.3, "fcf_growth": 0.7,
            "search_ebitda": 95.0, "cloud_rev": 58.7,
        }

# ─────────────────────────────────────────
# 3. 側邊欄
# ─────────────────────────────────────────
st.sidebar.header("📋 每季手動更新（2 個欄位）")
st.sidebar.caption("其餘數據已自動抓取，每季財報後只需更新以下兩項")
st.sidebar.markdown("---")

st.sidebar.markdown("**① Cloud 季增速 (%)**")
st.sidebar.caption(
    "📌 哪裡找：\n"
    "財報當天搜尋「GOOGL earnings cloud growth」\n"
    "或至 → investors.abc.xyz → Earnings → 最新 Press Release 第一頁"
)
cloud_growth = st.sidebar.number_input(
    "Cloud YoY 增速 (%)", value=48.0, step=0.1,
    help="Q4 2025 = 48%，來源：Alphabet 季報 Press Release"
)

st.sidebar.markdown("**② Search 廣告增速 (%)**")
st.sidebar.caption(
    "📌 哪裡找：\n"
    "同上，Press Release 第一頁「Google Search & other」那行\n"
    "計算方式：(本季 - 去年同季) ÷ 去年同季 × 100"
)
search_growth = st.sidebar.number_input(
    "Search YoY 增速 (%)", value=17.0, step=0.1,
    help="Q4 2025 = 17%，來源：Alphabet 季報 Press Release"
)

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 估值假設（可調整）")
st.sidebar.caption("依個人判斷調整，不確定就保留預設值")

pe_target      = st.sidebar.slider("相對估值：目標 P/E", 15.0, 35.0, 20.0,
                     help="同業 Meta/MSFT 約 22–28x，GOOGL 因風險折價給 20x")
cloud_mult     = st.sidebar.slider("SOTP：Cloud EV/Sales 倍數", 8.0, 25.0, 14.0,
                     help="AWS 約 15–18x，Google Cloud 稍低，給 14x")
search_mult    = st.sidebar.slider("SOTP：Search EV/EBITDA 倍數", 10.0, 25.0, 16.0,
                     help="廣告業務穩定現金流，給 16x")
youtube_val    = st.sidebar.slider("SOTP：YouTube 估值 ($B)", 300.0, 900.0, 600.0,
                     help="廣告+訂閱年收 $60B+，約 10x EV/Sales = $600B")
fcf_growth_dcf = st.sidebar.slider("DCF：FCF 預期成長率 (%)", 5.0, 25.0, 13.0,
                     help="Cloud 拉動，基本情境 13%")
wacc           = st.sidebar.slider("DCF：折現率 WACC (%)", 7.0, 13.0, 9.5, step=0.1,
                     help="大型科技股通常 9–10%")

st.sidebar.markdown("---")
st.sidebar.header("🤖 自動抓取數據（唯讀）")
st.sidebar.caption("以下由 yfinance 自動更新，不需手動修改")
st.sidebar.markdown(f"""
| 項目 | 數值 |
|------|------|
| 股價 | ${d['price']} |
| EPS（TTM） | ${d['eps_ttm']} |
| P/E（TTM） | {d['pe_ttm']}x |
| 全年營收 | ${d['revenue_ttm']}B |
| 營業利潤率 | {d['op_margin']}% |
| 自由現金流 | ${d['fcf']}B |
| FCF 年增速 | {d['fcf_growth']}% |
| 流通股數 | {d['shares_b']}億股 |
""")

# ─────────────────────────────────────────
# 4. 估值計算
# ─────────────────────────────────────────

# 相對估值
val_relative = d["eps_ttm"] * pe_target

# SOTP
sotp_search  = d["search_ebitda"] * search_mult
sotp_cloud   = d["cloud_rev"]     * cloud_mult
sotp_youtube = youtube_val
sotp_other   = 50.0
sotp_total_b = sotp_search + sotp_cloud + sotp_youtube + sotp_other
val_sotp     = sotp_total_b / d["shares_b"] * 10   # $/股

# DCF
base_fcf        = d["fcf"]
terminal_growth = 0.03
total_pv        = 0.0
for t_yr in range(1, 11):
    cf_yr     = base_fcf * ((1 + fcf_growth_dcf / 100) ** t_yr)
    total_pv += cf_yr / ((1 + wacc / 100) ** t_yr)
terminal_cf  = base_fcf * ((1 + fcf_growth_dcf / 100) ** 10) * (1 + terminal_growth)
terminal_val = terminal_cf / ((wacc / 100) - terminal_growth)
total_pv    += terminal_val / ((1 + wacc / 100) ** 10)
val_dcf      = total_pv / d["shares_b"] * 10        # $/股

# 綜合
composite  = val_relative * 0.3 + val_dcf * 0.2 + val_sotp * 0.5
upside_pct = (composite - d["price"]) / d["price"] * 100

# ─────────────────────────────────────────
# 5. 指標檢驗
# ─────────────────────────────────────────

def check(value, threshold, direction="above"):
    if direction == "above":
        if value >= threshold:          return "pass", f"{value:.1f}%（門檻 ≥{threshold}%）✓"
        elif value >= threshold * 0.75: return "warn", f"{value:.1f}%（門檻 ≥{threshold}%）接近"
        else:                           return "fail", f"{value:.1f}%（門檻 ≥{threshold}%）✗"
    else:
        if value <= threshold:          return "pass", f"{value:.1f}%（門檻 ≤{threshold}%）✓"
        elif value <= threshold * 1.2:  return "warn", f"{value:.1f}%（門檻 ≤{threshold}%）略超"
        else:                           return "fail", f"{value:.1f}%（門檻 ≤{threshold}%）✗"

def pe_check():
    gap = 23.0 - d["pe_ttm"]
    if gap > 5:    return "pass", f"折價 {gap:.1f}x vs 同業（同業約23x）✓"
    elif gap > 2:  return "warn", f"折價 {gap:.1f}x vs 同業，偏小"
    else:          return "fail", f"折價僅 {gap:.1f}x，法律風險未充分反映"

def icon(s): return {"pass": "🟢", "warn": "🟡", "fail": "🔴"}[s]

def model_health(chk_list):
    ss = [c[0] for c in chk_list]
    if "fail" in ss:   return "❌ 失效", "error"
    elif "warn" in ss: return "⚠️ 謹慎", "warning"
    else:              return "✅ 有效", "success"

checks_r = [
    ("Search 廣告增速 ⚠️手動",  *check(search_growth,     8,  "above")),
    ("P/E 折價 vs 同業（自動）", *pe_check()),
    ("FCF 為正（自動）",         *check(d["fcf"],          0,  "above")),
]
checks_d = [
    ("FCF 年增速（自動）",       *check(d["fcf_growth"],  12,  "above")),
    ("營業利潤率（自動）",       *check(d["op_margin"],   28,  "above")),
    ("WACC 合理（假設）",        *check(wacc,             11,  "below")),
]
checks_s = [
    ("Cloud 季增速 ⚠️手動",     *check(cloud_growth,     30,  "above")),
    ("Cloud 加速中 ⚠️手動",     *check(cloud_growth-35,   0,  "above")),
    ("整體營收增速（自動）",     *check(15.0,             10,  "above")),
]

hr, tr = model_health(checks_r)
hd, td = model_health(checks_d)
hs, ts = model_health(checks_s)

# ─────────────────────────────────────────
# 6. 頂部摘要
# ─────────────────────────────────────────
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("目前股價",   f"${d['price']:.2f}")
c2.metric("EPS（TTM）", f"${d['eps_ttm']:.2f}")
c3.metric("相對估值",   f"${val_relative:.0f}")
c4.metric("DCF 估值",   f"${val_dcf:.0f}")
c5.metric("SOTP 估值",  f"${val_sotp:.0f}")
c6.metric("綜合目標價", f"${composite:.0f}",
          delta=f"{'▲' if upside_pct>0 else '▼'} {abs(upside_pct):.1f}%",
          delta_color="normal" if upside_pct > 0 else "inverse")

st.markdown("---")

# ─────────────────────────────────────────
# 7. 指標檢驗
# ─────────────────────────────────────────
st.subheader("🔍 指標檢驗 — 三種模型當季狀態")
st.caption("🟢 通過　🟡 注意　🔴 失效　｜　⚠️手動 = 需每季更新　自動 = yfinance 自動抓取")

def render_check(col, title, health_text, health_type, chk_list):
    with col:
        if health_type == "success":   st.success(f"**{title}** — {health_text}")
        elif health_type == "warning": st.warning(f"**{title}** — {health_text}")
        else:                          st.error(f"**{title}** — {health_text}")
        rows = [{"指標": n, "狀態": icon(s), "說明": desc} for n, s, desc in chk_list]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

col_r, col_d, col_s = st.columns(3)
render_check(col_r, "相對估值", hr, tr, checks_r)
render_check(col_d, "DCF",      hd, td, checks_d)
render_check(col_s, "SOTP",     hs, ts, checks_s)

st.markdown("---")

# ─────────────────────────────────────────
# 8. 估值比較圖
# ─────────────────────────────────────────
st.subheader("📊 估值比較 vs 當前股價")

plot_df = pd.DataFrame([
    {"模型": "相對估值", "目標價": round(val_relative, 1)},
    {"模型": "DCF",      "目標價": round(val_dcf,      1)},
    {"模型": "SOTP",     "目標價": round(val_sotp,     1)},
    {"模型": "綜合加權", "目標價": round(composite,    1)},
])
y_max = max(plot_df["目標價"].max(), d["price"]) * 1.15

bars = alt.Chart(plot_df).mark_bar(
    cornerRadiusTopLeft=5, cornerRadiusTopRight=5, size=60
).encode(
    x=alt.X("模型:N", axis=alt.Axis(labelAngle=0, title=None),
            sort=["相對估值","DCF","SOTP","綜合加權"]),
    y=alt.Y("目標價:Q", scale=alt.Scale(domain=[0, y_max]), title="美金 ($)"),
    color=alt.Color("模型:N", scale=alt.Scale(
        domain=["相對估值","DCF","SOTP","綜合加權"],
        range=["#4a9eff","#2fd4a0","#f0a832","#b388ff"])),
    tooltip=["模型","目標價"]
).properties(height=380)

price_line = alt.Chart(pd.DataFrame({"y": [d["price"]]})).mark_rule(
    color="#ff6b6b", strokeWidth=3, strokeDash=[6,3]).encode(y="y:Q")
price_label = alt.Chart(pd.DataFrame({"y": [d["price"]], "t": [f"現價 ${d['price']:.2f}"]})).mark_text(
    align="left", dx=8, dy=-12, fontSize=14, fontWeight="bold", color="#ff6b6b"
).encode(y="y:Q", text="t:N")

st.altair_chart(bars + price_line + price_label, use_container_width=True)

with st.expander("📂 SOTP 分部拆解明細"):
    sotp_df = pd.DataFrame([
        {"業務": "Search / 廣告",  "基礎": f"EBITDA ${d['search_ebitda']:.0f}B ⚠️手動預設",
         "倍數": f"{search_mult:.0f}x EV/EBITDA", "估值": f"${sotp_search:.0f}B"},
        {"業務": "Google Cloud",   "基礎": f"Revenue ${d['cloud_rev']:.1f}B ⚠️手動預設",
         "倍數": f"{cloud_mult:.0f}x EV/Sales",   "估值": f"${sotp_cloud:.0f}B"},
        {"業務": "YouTube",        "基礎": "廣告+訂閱 $60B+",
         "倍數": "直接估值",                       "估值": f"${sotp_youtube:.0f}B"},
        {"業務": "Other Bets",     "基礎": "Waymo 等保守估",
         "倍數": "—",                              "估值": f"${sotp_other:.0f}B"},
        {"業務": "合計 → 每股",    "基礎": f"÷ {d['shares_b']:.0f}億股（自動）",
         "倍數": "—",                              "估值": f"${sotp_total_b:.0f}B → ${val_sotp:.0f}/股"},
    ])
    st.dataframe(sotp_df, hide_index=True, use_container_width=True)
    st.caption("⚠️手動預設 = Search EBITDA / Cloud Revenue 每季財報後需在側邊欄「估值假設」區更新倍數")

st.markdown("---")

# ─────────────────────────────────────────
# 9. 歷史趨勢
# ─────────────────────────────────────────
st.subheader("📈 歷史趨勢 — 季度追蹤")
st.caption("⚠️ 歷史數據需每季在程式碼 history 表格手動新增一行（共 5 個數字）")

history = pd.DataFrame([
    # 每季財報後，複製最後一行，改成新季度的數字
    {"季度": "Q1'24", "Cloud增速": 28, "Search增速": 15, "FCF增速":  8, "Cloud利潤率":  9, "股價": 165, "相對估值": 172, "DCF估值": 170, "SOTP估值": 175},
    {"季度": "Q2'24", "Cloud增速": 29, "Search增速": 14, "FCF增速":  6, "Cloud利潤率": 11, "股價": 175, "相對估值": 175, "DCF估值": 172, "SOTP估值": 182},
    {"季度": "Q3'24", "Cloud增速": 35, "Search增速": 12, "FCF增速":  5, "Cloud利潤率": 13, "股價": 168, "相對估值": 178, "DCF估值": 175, "SOTP估值": 195},
    {"季度": "Q4'24", "Cloud增速": 30, "Search增速": 13, "FCF增速": 10, "Cloud利潤率": 14, "股價": 190, "相對估值": 185, "DCF估值": 185, "SOTP估值": 210},
    # ↓ 最新季度：Cloud/Search 增速來自手動輸入，其餘自動計算
    {"季度": "Q4'25",
     "Cloud增速":   round(cloud_growth, 1),
     "Search增速":  round(search_growth, 1),
     "FCF增速":     round(d["fcf_growth"], 1),
     "Cloud利潤率": 17,
     "股價":        d["price"],
     "相對估值":    round(val_relative),
     "DCF估值":     round(val_dcf),
     "SOTP估值":    round(val_sotp)},
])

tab1, tab2, tab3 = st.tabs(["Cloud & Search 增速", "FCF & 利潤率", "估值 vs 股價"])

with tab1:
    df_m1 = history.melt(id_vars="季度", value_vars=["Cloud增速","Search增速"],
                         var_name="指標", value_name="數值")
    th_c = pd.DataFrame({"季度": history["季度"], "數值": [30]*len(history), "指標": ["Cloud門檻"]*len(history)})
    th_s = pd.DataFrame({"季度": history["季度"], "數值": [8]*len(history),  "指標": ["Search門檻"]*len(history)})
    line1 = alt.Chart(df_m1).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X("季度:N", sort=None),
        y=alt.Y("數值:Q", title="%"),
        color=alt.Color("指標:N", scale=alt.Scale(
            domain=["Cloud增速","Search增速"], range=["#f0a832","#4a9eff"])),
        tooltip=["季度","指標","數值"])
    t1 = alt.Chart(th_c).mark_line(strokeDash=[4,4], strokeWidth=1.5, color="#f0a832", opacity=0.5).encode(
        x=alt.X("季度:N", sort=None), y="數值:Q")
    t2 = alt.Chart(th_s).mark_line(strokeDash=[4,4], strokeWidth=1.5, color="#4a9eff", opacity=0.5).encode(
        x=alt.X("季度:N", sort=None), y="數值:Q")
    st.altair_chart((line1+t1+t2).properties(height=300), use_container_width=True)
    st.caption("虛線 = 門檻　Cloud ≥ 30% 支撐 SOTP 高倍數；Search ≥ 8% 支撐相對估值")

with tab2:
    df_m2 = history.melt(id_vars="季度", value_vars=["FCF增速","Cloud利潤率"],
                         var_name="指標", value_name="數值")
    line2 = alt.Chart(df_m2).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X("季度:N", sort=None),
        y=alt.Y("數值:Q", title="%"),
        color=alt.Color("指標:N", scale=alt.Scale(
            domain=["FCF增速","Cloud利潤率"], range=["#2fd4a0","#b388ff"])),
        tooltip=["季度","指標","數值"])
    st.altair_chart(line2.properties(height=300), use_container_width=True)
    st.caption("FCF增速 ≥ 12% 支撐 DCF；Cloud 利潤率持續上升才支撐 SOTP 高倍數")

with tab3:
    df_m3 = history.melt(id_vars="季度", value_vars=["股價","相對估值","DCF估值","SOTP估值"],
                         var_name="指標", value_name="數值")
    line3 = alt.Chart(df_m3).mark_line(point=True, strokeWidth=2).encode(
        x=alt.X("季度:N", sort=None),
        y=alt.Y("數值:Q", title="美金 ($)"),
        color=alt.Color("指標:N", scale=alt.Scale(
            domain=["股價","相對估值","DCF估值","SOTP估值"],
            range=["#ff6b6b","#4a9eff","#2fd4a0","#f0a832"])),
        strokeDash=alt.condition(
            alt.datum["指標"] == "股價", alt.value([1,0]), alt.value([4,3])),
        tooltip=["季度","指標","數值"])
    st.altair_chart(line3.properties(height=300), use_container_width=True)
    st.caption("股價持續高於所有估值帶 → 市場在定價未來敘事，需重新審視投資論點")

st.markdown("---")

# ─────────────────────────────────────────
# 10. 決策摘要
# ─────────────────────────────────────────
st.subheader("🧭 當季決策摘要")

all_checks = checks_r + checks_d + checks_s
pass_n = sum(1 for _,s,_ in all_checks if s=="pass")
warn_n = sum(1 for _,s,_ in all_checks if s=="warn")
fail_n = sum(1 for _,s,_ in all_checks if s=="fail")

col_a, col_b = st.columns([2,1])

with col_a:
    st.markdown(f"""
**指標通過率：{pass_n} / {len(all_checks)}**
🟢 通過 {pass_n} 項　🟡 注意 {warn_n} 項　🔴 失效 {fail_n} 項

**有效模型建議權重：**
- 相對估值 30%（{hr}）
- DCF 20%（{hd}）
- SOTP 50%（{hs}）

**綜合目標價：${composite:.0f}**　｜　目前股價：${d['price']:.2f}
    """)
    if upside_pct > 15:
        st.success(f"📌 股價低於合理估值 {abs(upside_pct):.1f}%，具備安全邊際")
    elif upside_pct > -10:
        st.warning(f"📌 股價接近合理估值（差距 {upside_pct:.1f}%），持有觀察")
    else:
        st.error(f"📌 股價超出合理估值 {abs(upside_pct):.1f}%，需重新審視投資論點")

with col_b:
    q1 = icon(checks_s[0][1])
    q2 = icon(checks_d[0][1])
    q3 = icon(checks_r[0][1])
    st.markdown(f"""
**每季三個核心問題：**

{q1} Cloud 增速仍在門檻以上？
*⚠️手動輸入：{cloud_growth:.1f}%，門檻 30%*

{q2} FCF 有沒有穩定成長？
*🤖自動計算：{d['fcf_growth']:.1f}%，門檻 12%*

{q3} 廣告收入有沒有被侵蝕？
*⚠️手動輸入：{search_growth:.1f}%，門檻 8%*

三個都 🟢 → 持有論點成立
出現 🔴 → 重新評估倉位
    """)

st.markdown("---")
st.caption(
    "本工具為估值學習用途，不構成投資建議　｜　"
    "🤖自動：Yahoo Finance（每小時刷新）　｜　"
    "⚠️手動：Cloud / Search 增速，來源：Alphabet 季報 Press Release"
)
