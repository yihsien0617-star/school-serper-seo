# 檔案名稱：2_dashboard.py (自我診斷版)
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

st.sidebar.title("🏫 招生策略控制台")
st.sidebar.caption("系統核心：Gemini (自動偵測)")
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

# --- 函數 2: Gemini AI 寫文章 (含自動診斷) ---
def generate_ai_article(keyword, department):
    prompt = f"""
    你是一位資深的大學招生行銷專家。
    請針對關鍵字「{keyword}」，為「{department}」撰寫一篇部落格文章草稿。
    字數：約 600 字。
    """
    
    try:
        # 1. 先嘗試最新的 Flash 模型
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        error_msg = str(e)
        
        # 2. 如果失敗，嘗試列出所有可用模型 (Debug 模式)
        if "404" in error_msg or "not found" in error_msg:
            try:
                available_models = []
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        available_models.append(m.name)
                
                # 回傳診斷訊息
                return f"""
                ❌ AI 模型名稱錯誤 (404)。
                
                🔍 **系統自我診斷：**
                您的 API Key 目前可用的模型只有這些：
                {', '.join(available_models)}
                
                👉 請記下上面以 'models/' 開頭的名稱 (例如 models/gemini-pro)，
                然後告訴工程師修改程式碼。
                """
            except Exception as debug_e:
                return f"❌ 嚴重錯誤：連列出模型都失敗。原因：{str(debug_e)}\n原始錯誤：{error_msg}"
        
        return f"❌ AI 生成失敗: {error_msg}"

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
    st.title(f"🔍 {selected_dept}：招生關鍵字分析")
    dept_df = df[df['Department'] == selected_dept]
    if dept_df.empty: st.stop()
    best_keyword = dept_df.sort_values('Opportunity_Score', ascending=False).iloc[0]
    
    col1, col2 = st.columns(2)
    col1.metric("🔥 必寫文章主題", best_keyword['Keyword'])
    col2.metric("平均月搜尋量", f"{int(dept_df['Search_Volume'].mean()):,}")
    st.divider()

    st.subheader("🕵️ 競爭對手偵查 & ✨ AI 文案生成")
    target_kw = st.selectbox("👇 第一步：請選擇您想進攻的關鍵字", dept_df['Keyword'].unique())
    st.write("") 
    btn = st.button("🚀 第二步：點我開始分析 + 生成文章", type="primary", use_container_width=True)

    if btn:
        if "你的" in GEMINI_API_KEY or "你的" in SERPER_API_KEY:
             st.error("⚠️ 請先在程式碼中填入正確的 API Key！")
        else:
            with st.spinner(f"正在分析「{target_kw}」的 Google 排名..."):
                results, status = get_google_results(target_kw)
                if "錯誤" in status: st.error(status)
                else:
                    st.success(f"✅ 搜尋完成！({status})")
                    with st.expander("🔻 競爭對手列表", expanded=True):
                        for i, res in enumerate(results):
                            st.markdown(f"**{i+1}. [{res.get('title')}]({res.get('link')})**")

            st.markdown("---")
            st.subheader(f"✨ AI 為您生成的「{target_kw}」文章草稿")
            
            with st.spinner("🤖 AI 正在嘗試寫作 (若失敗將啟動自我診斷)..."):
                ai_article = generate_ai_article(target_kw, selected_dept)
                
                # 如果是診斷訊息，顯示為黃色警告
                if "❌" in ai_article:
                    st.warning(ai_article)
                else:
                    st.markdown(ai_article)
                    st.download_button("📥 下載文章 (.txt)", ai_article, f"{target_kw}.txt")

    st.divider()
    clean_df = dept_df[['Keyword', 'Search_Volume', 'Competition_Level', 'Opportunity_Score']].sort_values('Opportunity_Score', ascending=False)
    st.dataframe(clean_df, use_container_width=True)
