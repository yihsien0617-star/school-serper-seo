# 檔案名稱：2_dashboard.py (GEO 終極整合版：針對 AI 搜尋優化)
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import google.generativeai as genai
import time

# ==========================================
# 🔑 設定區 (請在此填入您的 API Key)
# ==========================================
SERPER_API_KEY = "你的_SERPER_API_KEY"       # 用來查真實排名
GEMINI_API_KEY = "你的_GEMINI_API_KEY"       # 用來寫 GEO 文案
# ==========================================

# 設定 AI
if "你的" not in GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="學校招生 SEO/GEO 戰情室", layout="wide")

# 讀取數據
try:
    df = pd.read_csv('school_data.csv')
except FileNotFoundError:
    st.error("錯誤：找不到 school_data.csv，請確認 GitHub 檔案是否上傳成功。")
    st.stop()

# --- 側邊欄 ---
st.sidebar.title("🏫 招生策略控制台")
st.sidebar.caption("核心：Gemini 2.0 + GEO (AI 搜尋優化)")
dept_list = ["全校總覽"] + list(df['Department'].unique())
selected_dept = st.sidebar.selectbox("選擇分析視角", dept_list)

# --- 函數 1: Serper 真實搜尋 (快取 1 小時) ---
@st.cache_data(ttl=3600)
def get_google_results(keyword):
    """透過 Serper API 取得真實 Google 排名"""
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": keyword, "gl": "tw", "hl": "zh-tw", "num": 3})
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, data=payload)
        data = response.json()
        if "organic" in data:
            return data["organic"], "🟢 Google 真實數據"
        else:
            return [], "⚠️ 查無資料"
    except Exception as e:
        return [], f"連線錯誤: {str(e)}"

# --- 函數 2: Gemini AI 寫文章 (GEO 優化版 + 自動重試) ---
@st.cache_data(show_spinner=False)
def generate_ai_article(keyword, department):
    """
    呼叫 Gemini 2.0 Flash 撰寫符合 GEO (Generative Engine Optimization) 的文案
    目標：讓 AI (ChatGPT, Gemini) 容易理解並引用。
    """
    
    # 🔥 GEO 專用提示詞工程 (Prompt Engineering)
    prompt = f"""
    你是一位精通「GEO (生成式引擎優化)」的大學招生行銷專家。
    目標對象：台灣高中生 (17-18歲) 與家長。
    任務：為「{department}」針對關鍵字「{keyword}」撰寫一篇高權重、易被 AI 搜尋引用的部落格文章。

    ⚠️ 為了讓 AI 搜尋引擎 (Google SGE, ChatGPT) 優先引用，請嚴格遵守以下結構：
    
    1. **直接回答段落 (Direct Answer)**：
       - 文章第一段必須直接給出定義或核心結論（例如薪資範圍、錄取分數、核心優勢）。
       - 這是為了搶佔 Google 的 "精選摘要 (Featured Snippet)"。
    
    2. **結構化數據 (必須包含表格)**：
       - 請製作一個 Markdown 表格。
       - 內容可以是：薪資比較、課程地圖、證照列表、或本校 vs 他校優勢比較。
       - AI 非常喜歡引用表格數據。
    
    3. **權威性內容 (E-E-A-T)**：
       - 提到該領域的具體職稱、具體醫院或企業名稱、考照率數據（請用 [數據]% 表示）。
    
    4. **FAQ 結構化問答 (必備)**：
       - 文章最後必須有 "關於 {keyword} 的常見問題"。
       - 列出 3 個高中生最常問的問題，並給出簡短精準的回答。

    5. **行動呼籲 (CTA)**：
       - 邀請參加體驗營或瀏覽系網。

    語氣：專業、數據導向、但充滿熱情。
    字數：約 800 字。
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) or "Resource exhausted" in str(e):
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 5)
                    continue
                else:
                    return "⏳ 系統忙碌 (Google 請求限速)，請休 1 分鐘後再試。"
            return f"❌ AI 生成失敗: {str(e)}"

# --- 主畫面邏輯 ---

if selected_dept == "全校總覽":
    st.title("📊 全校科系網路聲量總覽")
    st.info("💡 提示：請從左側選單選擇特定科系，以啟動「AI 搜尋優化 (GEO)」文案生成功能。")
    
    total = df['Search_Volume'].sum()
    top = df.groupby('Department')['Search_Volume'].sum().idxmax()
    col1, col2 = st.columns(2)
    col1.metric("全校總潛在搜尋流量", f"{total:,}")
    col2.metric("網路聲量冠軍", top)
    st.markdown("---")
    
    dept_traffic = df.groupby('Department')['Search_Volume'].sum().reset_index().sort_values('Search_Volume', ascending=False)
    fig_bar = px.bar(dept_traffic, x='Department', y='Search_Volume', color='Department')
    st.plotly_chart(fig_bar, width="stretch")

else:
    # === 單一科系視角 (GEO 戰情室) ===
    st.title(f"🔍 {selected_dept}：AI 搜尋優化戰情室")
    dept_df = df[df['Department'] == selected_dept]
    
    if dept_df.empty:
        st.warning("⚠️ 此科系無數據。")
        st.stop()

    best_keyword = dept_df.sort_values('Opportunity_Score', ascending=False).iloc[0]
    
    # 頂部數據
    col1, col2 = st.columns(2)
    col1.metric("🔥 本月必攻關鍵字", best_keyword['Keyword'], help="綜合搜尋量與競爭度計算出的最佳機會")
    col2.metric("平均月搜尋量", f"{int(dept_df['Search_Volume'].mean()):,}")
    
    st.divider()

    # --- 🤖 GEO 戰略指導區 (新增功能) ---
    with st.expander("💡 給系主任的 SEO/GEO 撰寫指南 (如何讓 AI 引用我們？)", expanded=True):
        st.markdown("""
        **現在的趨勢不只是讓「人」搜尋到，還要讓「AI」看得懂！**
        
        若希望 ChatGPT 或 Google Gemini 在回答「哪間學校好？」時引用本系，請注意：
        1.  **結構化數據**：AI 最愛看**表格**。請多整理「薪資表」、「課程表」、「證照表」。
        2.  **直接回答**：文章開頭不要廢話，直接給定義（例如：醫檢師起薪約 4.5 萬）。
        3.  **FAQ 格式**：將學生常問的問題寫成 Q&A，這是 AI 抓取答案的主要來源。
        4.  **權威性**：多引用國考數據、具體合作醫院名稱。
        """)

    st.write("") 

    # --- 核心功能區 ---
    st.subheader("🕵️ 競爭對手偵查 & ✨ 生成 GEO 優化文案")
    
    target_kw = st.selectbox(
        "👇 第一步：請選擇您想進攻的關鍵字", 
        dept_df['Keyword'].unique()
    )

    st.write("") 
    btn = st.button(
        "🚀 第二步：啟動 AI 分析與寫作 (GEO 模式)", 
        type="primary", 
        use_container_width=True
    )

    if btn:
        if "你的" in GEMINI_API_KEY or "你的" in SERPER_API_KEY:
             st.error("⚠️ 請先在程式碼中填入正確的 API Key！")
        else:
            # A. Google 搜尋
            with st.spinner(f"正在分析「{target_kw}」的 Google 排名..."):
                results, status = get_google_results(target_kw)
                
                if "錯誤" in status:
                    st.error(status)
                else:
                    st.success(f"✅ 競爭對手分析完成！")
                    with st.expander("🔻 查看目前的競爭對手 (他們寫了什麼？)", expanded=True):
                        if not results:
                            st.info("此關鍵字目前沒有顯著的競爭對手。")
                        for i, res in enumerate(results):
                            st.markdown(f"**{i+1}. [{res.get('title')}]({res.get('link')})**")
                            st.caption(res.get('snippet'))

            # B. AI 寫作 (GEO 版)
            st.markdown("---")
            st.subheader(f"✨ AI 為您生成的「{target_kw}」GEO 優化草稿")
            st.caption("此草稿已包含：表格、直接回答段落、FAQ 結構，以利 AI 搜尋引用。")
            
            with st.spinner("🤖 AI (Gemini 2.0) 正在撰寫高權重文章中..."):
                ai_article = generate_ai_article(target_kw, selected_dept)
                
                if "⏳" in ai_article:
                    st.warning(ai_article)
                elif "❌" in ai_article:
                    st.error(ai_article)
                else:
                    st.markdown(ai_article)
                    st.download_button(
                        label="📥 下載這篇 GEO 優化文章 (.txt)",
                        data=ai_article,
                        file_name=f"{selected_dept}_{target_kw}_GEO草稿.txt",
                        mime="text/plain"
                    )

    st.divider()
    
    # 行動清單
    st.subheader("📝 優先撰寫建議清單")
    clean_df = dept_df[['Keyword', 'Search_Volume', 'Competition_Level', 'Opportunity_Score']].sort_values('Opportunity_Score', ascending=False)
    st.dataframe(clean_df, use_container_width=True)
