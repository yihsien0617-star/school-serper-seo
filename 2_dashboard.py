# 檔案名稱：2_dashboard.py (最終修復版：強制使用 gemini-1.5-flash)
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import google.generativeai as genai

# ==========================================
# 🔑 設定區 (請在此填入您的 API Key)
# ==========================================
SERPER_API_KEY = "6dcb4225919e50e501bbddfab3411337b99c0547"
GEMINI_API_KEY = "AIzaSyCU62-XBvqOsH3Dq3jvote9jd6jMew79Qk"
# ==========================================

# 設定 AI
if "你的" not in GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="學校招生 SEO 戰情室", layout="wide")

# 讀取數據
try:
    df = pd.read_csv('school_data.csv')
except FileNotFoundError:
    st.error("錯誤：找不到 school_data.csv。")
    st.stop()

# --- 側邊欄 ---
st.sidebar.title("🏫 招生策略控制台")
st.sidebar.caption("核心：Gemini 1.5 Flash + Serper")
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
    """呼叫 Gemini 1.5 Flash 撰寫招生文案"""
    
    prompt = f"""
    你是一位資深的大學招生行銷專家。
    目標對象：台灣的高中生 (17-18歲) 及其家長。
    請針對關鍵字「{keyword}」，為「{department}」撰寫一篇部落格文章草稿。
    
    文章結構要求：
    1. **吸睛標題**：要包含關鍵字。
    2. **前言 (Hook)**：從高中生的煩惱切入。
    3. **核心價值**：介紹這領域的優勢（如薪資、未來趨勢），並帶入本系特色。
    4. **常見問答 (FAQ)**：列出 3 個學生常問的問題並回答。
    5. **行動呼籲 (CTA)**：鼓勵瀏覽官網。
    
    語氣：親切、專業。字數：約 600 字。
    """
    
    try:
        # ✅ 使用 gemini-1.5-flash (需搭配 requirements.txt >= 0.8.3)
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ AI 生成失敗: {str(e)}"

# --- 主畫面邏輯 ---

if selected_dept == "全校總覽":
    st.title("📊 全校科系網路聲量總覽")
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
    # === 單一科系視角 ===
    st.title(f"🔍 {selected_dept}：招生關鍵字分析")
    dept_df = df[df['Department'] == selected_dept]
    
    if dept_df.empty:
        st.warning("⚠️ 此科系無數據。")
        st.stop()

    best_keyword = dept_df.sort_values('Opportunity_Score', ascending=False).iloc[0]
    
    col1, col2 = st.columns(2)
    col1.metric("🔥 必寫文章主題", best_keyword['Keyword'])
    col2.metric("平均月搜尋量", f"{int(dept_df['Search_Volume'].mean()):,}")
    
    st.divider()

    # --- 核心功能區 ---
    st.subheader("🕵️ 競爭對手偵查 & ✨ AI 文案生成")
    
    # 1. 選單
    target_kw = st.selectbox(
        "👇 第一步：請選擇您想進攻的關鍵字", 
        dept_df['Keyword'].unique()
    )

    st.write("") 

    # 2. 按鈕 (最大化顯示)
    btn = st.button(
        "🚀 第二步：點我開始分析 + 生成文章", 
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
                    st.success(f"✅ 搜尋完成！({status})")
                    with st.expander("🔻 點擊查看目前的競爭對手", expanded=True):
                        if not results:
                            st.info("此關鍵字目前沒有顯著的競爭對手。")
                        for i, res in enumerate(results):
                            st.markdown(f"**{i+1}. [{res.get('title')}]({res.get('link')})**")
                            st.caption(res.get('snippet'))

            # B. AI 寫作
            st.markdown("---")
            st.subheader(f"✨ AI 為您生成的「{target_kw}」文章草稿")
            
            with st.spinner("🤖 AI 正在撰寫文章中，請稍候..."):
                ai_article = generate_ai_article(target_kw, selected_dept)
                st.markdown(ai_article)
                st.download_button(
                    label="📥 下載這篇文章 (.txt)",
                    data=ai_article,
                    file_name=f"{selected_dept}_{target_kw}_文章草稿.txt",
                    mime="text/plain"
                )

    st.divider()
    
    # 行動清單表格
    st.subheader("📝 優先撰寫建議")
    clean_df = dept_df[['Keyword', 'Search_Volume', 'Competition_Level', 'Opportunity_Score']].sort_values('Opportunity_Score', ascending=False)
    st.dataframe(clean_df, use_container_width=True)
