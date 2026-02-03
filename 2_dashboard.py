# 檔案名稱：2_dashboard.py (真實數據 + AI 寫手版)
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import google.generativeai as genai # 引入 AI 大腦

# ==========================================
# 🔑 設定區 (請填入你的金鑰)
# ==========================================
SERPER_API_KEY = "6dcb4225919e50e501bbddfab3411337b99c0547"       # 用來查真實排名
GEMINI_API_KEY = "AIzaSyCU62-XBvqOsH3Dq3jvote9jd6jMew79Qk"       # 用來寫文章
# ==========================================

# 設定 AI
if "你的" not in GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="學校招生 SEO 戰情室 (AI 賦能版)", layout="wide")

# 讀取數據
try:
    df = pd.read_csv('school_data.csv')
except FileNotFoundError:
    st.error("錯誤：找不到 school_data.csv，請確認 GitHub 檔案。")
    st.stop()

st.sidebar.title("🏫 招生策略控制台")
st.sidebar.caption("功能：真實搜尋 + AI 文案生成")
dept_list = ["全校總覽"] + list(df['Department'].unique())
selected_dept = st.sidebar.selectbox("選擇分析視角", dept_list)

# --- 函數 1: Serper 真實搜尋 ---
def get_google_results(keyword):
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

# --- 函數 2: Gemini AI 寫文章 ---
def generate_ai_article(keyword, department):
    """
    呼叫 Gemini 為特定關鍵字撰寫招生文案
    """
    if "你的" in GEMINI_API_KEY:
        return "⚠️ 請先設定 Gemini API Key 才能使用寫作功能。"

    # 這是給 AI 的指令 (Prompt Engineering)
    prompt = f"""
    你是一位資深的大學招生行銷專家。
    目標對象：台灣的高中生 (17-18歲) 及其家長。
    請針對關鍵字「{keyword}」，為「{department}」撰寫一篇吸引人的部落格文章草稿。
    
    文章結構要求：
    1. **吸睛標題**：要包含關鍵字，且能引起好奇心。
    2. **前言 (Hook)**：從高中生的煩惱或對未來的迷惘切入。
    3. **核心價值**：介紹這個領域的優勢（如薪資、穩定性、未來趨勢），並帶入本系特色。
    4. **常見問答 (FAQ)**：列出 3 個學生最常問的問題並回答。
    5. **行動呼籲 (CTA)**：鼓勵學生參加體驗營或瀏覽官網。
    
    語氣：親切、專業、充滿希望。
    字數：約 600 字。
    """
    
    try:
        # 使用最新的 Gemini 1.5 Flash 模型 (速度快、免費額度高)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ AI 生成失敗: {str(e)}"

# --- 主畫面 ---

if selected_dept == "全校總覽":
    st.title("📊 全校科系網路聲量總覽")
    total = df['Search_Volume'].sum()
    top = df.groupby('Department')['Search_Volume'].sum().idxmax()
    col1, col2 = st.columns(2)
    col1.metric("全校總潛在搜尋流量", f"{total:,}")
    col2.metric("網路聲量冠軍", top)
    st.markdown("---")
    
    # 這裡如果不支援 matplotlib 就只顯示簡單圖表
    dept_traffic = df.groupby('Department')['Search_Volume'].sum().reset_index().sort_values('Search_Volume', ascending=False)
    fig_bar = px.bar(dept_traffic, x='Department', y='Search_Volume', color='Department')
    st.plotly_chart(fig_bar, width="stretch")

else:
    st.title(f"🔍 {selected_dept}：招生關鍵字分析")
    dept_df = df[df['Department'] == selected_dept]
    best_keyword = dept_df.sort_values('Opportunity_Score', ascending=False).iloc[0]
    
    col1, col2 = st.columns(2)
    col1.metric("🔥 必寫文章主題", best_keyword['Keyword'])
    col2.metric("平均月搜尋量", f"{int(dept_df['Search_Volume'].mean()):,}")
    
    st.divider()

    # --- 核心功能區：搜尋 + AI ---
    st.subheader("🕵️ 競爭對手偵查 & ✨ AI 文案生成")
    
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        target_kw = st.selectbox("選擇關鍵字：", dept_df['Keyword'].unique())
    with col_s2:
        st.write("") 
        st.write("") 
        btn = st.button("開始分析與生成", type="primary")

    if btn:
        # 1. 執行搜尋分析
        with st.spinner(f"正在分析「{target_kw}」的競爭對手..."):
            results, status = get_google_results(target_kw)
            
            if "錯誤" in status:
                st.error(status)
            else:
                st.success(f"✅ 分析完成！來源：{status}")
                
                # 顯示競爭對手 (用折疊選單節省空間)
                with st.expander("🔻 點擊查看目前的競爭對手排名 (Google 前 3 名)"):
                    for i, res in enumerate(results):
                        st.markdown(f"**{i+1}. [{res.get('title')}]({res.get('link')})**")
                        st.caption(res.get('snippet'))

        # 2. 執行 AI 寫作
        st.markdown("---")
        st.subheader(f"✨ AI 為您生成的「{target_kw}」招生草稿")
        
        with st.spinner("🤖 AI 正在撰寫文章中，請稍候... (約需 5-10 秒)"):
            ai_article = generate_ai_article(target_kw, selected_dept)
            
            # 顯示文章
            st.markdown(ai_article)
            
            # 提供下載按鈕
            st.download_button(
                label="📥 下載這篇文章 (.txt)",
                data=ai_article,
                file_name=f"{selected_dept}_{target_kw}_文章草稿.txt",
                mime="text/plain"
            )

    st.divider()
    
    # 行動清單 (確保不報錯的安全版)
    st.subheader("📝 優先撰寫建議")
    clean_df = dept_df[['Keyword', 'Search_Volume', 'Competition_Level', 'Opportunity_Score']].sort_values('Opportunity_Score', ascending=False)
    st.dataframe(clean_df, width=1000)
