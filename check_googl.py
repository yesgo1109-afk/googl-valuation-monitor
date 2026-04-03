import yfinance as yf

def run_valuation():
    print(f"正在抓取最新市場數據...\n")
    
    # 1. 抓取即時數據 (GOOGL, META, MSFT 用於比較)
    googl = yf.Ticker("GOOGL")
    meta = yf.Ticker("META")
    msft = yf.Ticker("MSFT")
    
    current_price = googl.history(period="1d")['Close'].iloc[-1]
    googl_pe = googl.info.get('trailingPE', 0)
    meta_pe = meta.info.get('trailingPE', 0)
    msft_pe = msft.info.get('trailingPE', 0)
    
    # 2. 模擬財報數據 (這些數字通常每季更新一次，目前先設定為你提供的財報數值)
    cloud_growth = 48  # % (假設值)
    ad_growth = 17     # % (假設值)
    fcf_growth = 0.7   # % (假設值)
    
    print(f"===== Alphabet (GOOGL) 指標監控儀表板 =====")
    print(f"當前股價: ${current_price:.2f} | P/E: {googl_pe:.1f}x")
    print("-" * 45)

    # --- 模型一：相對估值檢驗 ---
    print("[模型一：相對估值]")
    # 判斷廣告增速是否 > 8% 且 P/E 是否低於同業
    if ad_growth > 8 and googl_pe < meta_pe:
        status_rel = "✅ 成立 (廣告成長穩健且具折現空間)"
    else:
        status_rel = "❌ 失效 (成長放緩或估值已過高)"
    print(f" > 狀態: {status_rel}")
    print(f" > 廣告增速: {ad_growth}% (門檻 8%)")
    print(f" > 同業比較: GOOGL({googl_pe:.1f}x) vs META({meta_pe:.1f}x)")

    # --- 模型二：DCF 檢驗 ---
    print("\n[模型二：DCF 現金流]")
    # 判斷自由現金流增速是否 > 12%
    if fcf_growth > 12:
        status_dcf = "✅ 成立 (現金流強勁)"
    else:
        status_dcf = "⚠️ 警示 (FCF 增速僅 {fcf_growth}%，低於門檻 12%)"
    print(f" > 狀態: {status_dcf}")

    # --- 模型三：SOTP 檢驗 ---
    print("\n[模型三：SOTP 分部加總]")
    # 判斷 Cloud 增速是否 > 30%
    if cloud_growth > 30:
        status_sotp = "✅ 主導 (Cloud 高速成長，適用分部估值)"
    else:
        status_sotp = "❌ 回歸 (Cloud 成長趨緩，回歸廣告估值框架)"
    print(f" > 狀態: {status_sotp}")
    print(f" > Cloud 增速: {cloud_growth}% (門檻 30%)")
    
    print("-" * 45)
    
    # 3. 綜合結論邏輯
    if cloud_growth > 30:
        target_price = 216 # SOTP 框架目標價
        print(f"核心策略：目前由 [SOTP 模型] 主導。")
    else:
        target_price = 180 # 傳統估值目標價
        print(f"核心策略：Cloud 成長一般，採保守估值。")
        
    print(f"建議目標價: ${target_price}")
    
run_valuation()