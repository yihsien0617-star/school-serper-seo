# 檔案名稱：2_dashboard.py (Serper 真實數據版)
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json

# ==========================================
# 🔑 請將你在 serper.dev 申請的 API Key 貼在下方
SERPER_API_KEY = "6dcb4225919e50e501bbddfab3411337b99c0547" 
# ==========================================

st.set_page_config(page_title="學校招生 SEO 戰情室 (真實數據版)", layout="wide")

# 讀取數據
try:
    df = pd.read_csv('school_data.csv')
except FileNotFoundError:
    st.error("錯誤：找不到 school_data.csv，請確認有將 csv 檔上傳到 GitHub。")
    st.stop()

st.sidebar.title("🏫 招生策略控制台")
st.sidebar.caption("資料來源：Google (via Serper)")
dept_list = ["全校總覽"] + list(df['Department'].unique())
selected_dept = st.sidebar.selectbox("選擇分析視角", dept_list)

# --- 核心功能：Serper API 搜尋 (業界標準) ---
def get_google_results(keyword):
    """
    透過 Serper API 取得 100% 真實的 Google 搜尋結果。
    這是目前最穩定、最不會被擋的雲端解決方案。
    """
    url = "https://google.serper.dev/search"
    
    # 設定搜尋參數：地區(tw), 語言(zh-tw)
    payload = json.dumps({
        "q": keyword,
        "gl": "tw",
        "hl": "zh-tw",
        "num": 3 # 只抓前 3 名
    })
    
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        
        # 檢查 API Key 是否正確
        if response.status_code == 403:
            return [], "❌ API Key 錯誤或額度不足，請檢查 serper.dev"
            
        data = response.json()
        
        # 解析回傳的 JSON 資料
        if "organic" in data:
            results = []
            for item in data["organic"]:
                results.append({
                    "title": item.get("title"),
                    "href": item.get("link"),
                    "snippet": item.get("snippet", "無預覽文字")
                })
            return results, "🟢 Google 真實數據 (Live)"
        else:
            return [], "⚠️ Google 查無資料"
            
    except Exception as e:
        return [], f"連線錯誤: {str(e)}"

# --- 主畫面顯示 ---

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
    best_keyword = dept_df.sort_values('Opportunity_Score', ascending=False).iloc[0]
    
    col1, col2 = st.columns(2)
    col1.metric("🔥 必寫文章主題", best_keyword['Keyword'])
    col2.metric("平均月搜尋量", f"{int(dept_df['Search_Volume'].mean()):,}")
    
    st.divider()

    # --- 真實搜尋區 ---
    st.subheader("🕵️ 競爭對手分析 (Google 真實排名)")
    st.info("此功能串接 Serper SEO 資料庫，顯示當下真實的 Google 排名。")
    
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        target_kw = st.selectbox("選擇關鍵字：", dept_df['Keyword'].unique())
    with col_s2:
        st.write("") 
        st.write("") 
        btn = st.button("開始分析", type="primary")

    if btn:
        # 檢查使用者有沒有忘記填 Key
        if "這裡貼上" in SERPER_API_KEY:
            st.error("⚠️ 請先在程式碼中填入 Serper API Key！")
        else:
            with st.spinner(f"正在向 Google 請求「{target_kw}」的真實數據..."):
                results, status = get_google_results(target_kw)
                
                if "錯誤" in status:
                    st.error(status)
                else:
                    st.success(f"✅ 分析完成！來源：{status}")

                    for i, res in enumerate(results):
                        title = res.get('title', '無標題')
                        url = res.get('href', '#')
                        snippet = res.get('snippet', '')
                        
                        # 智慧分類標籤
                        icon = "🔗"
                        tag = "一般網站"
                        
                        if "dcard" in url: 
                            icon = "💬"; tag = "Dcard"
                        elif "ptt" in url: 
                            icon = "💬"; tag = "PTT"
                        elif "104" in url or "1111" in url: 
                            icon = "💼"; tag = "人力銀行"
                        elif "hwai" in url: 
                            icon = "🏆"; tag = "本校官網"
                        elif "edu.tw" in url: 
                            icon = "⚔️"; tag = "他校競爭者"

                        with st.expander(f"第 {i+1} 名：{icon} {tag} - {title}", expanded=True):
                            st.markdown(f"**連結：** [{url}]({url})")
                            st.caption(f"📝 內文摘要：{snippet}")
                            
                            # 給系主任的建議
                            if tag == "Dcard" or tag == "PTT":
                                st.info("💡 建議：此為社群討論，請密切關注學生評價，必要時安排回文。")
                            elif tag == "他校競爭者":
                                st.error("💡 建議：競爭對手排名在我們前面！請分析對方網頁內容，優化我們的關鍵字。")

    st.divider()
    
    st.subheader("📝 優先撰寫建議")
    st.dataframe(
        dept_df[['Keyword', 'Search_Volume', 'Opportunity_Score']]
        .sort_values('Opportunity_Score', ascending=False)
        .style.background_gradient(subset=['Opportunity_Score'], cmap="Greens"),
        width="stretch"
    )
# 這只是一個概念範例
import google.generativeai as genai

def generate_article(keyword):
    prompt = f"""
    你是一位資深的大學招生行銷專家。
    請針對關鍵字「{keyword}」，為中華醫事科技大學醫學檢驗生物技術系，
    撰寫一篇 500 字的部落格文章。
    
    文章要求：
    1. 語氣親切，針對高中生與家長。
    2. 必須提到本系的優勢（如：國考通過率高、設備新）。
    3. 包含 3 個常見問答 (FAQ)。
    """
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text
