# 檔案名稱：2_dashboard.py (GEO 策略引導版 - 無 API key)
import streamlit as st
import pandas as pd
import plotly.express as px

# 設定頁面
st.set_page_config(page_title="學校招生 SEO/GEO 戰情室", layout="wide")

# 讀取數據
try:
    df = pd.read_csv('school_data.csv')
except FileNotFoundError:
    st.error("錯誤：找不到 school_data.csv，請確認 GitHub 檔案是否上傳成功。")
    st.stop()

# --- 側邊欄 ---
st.sidebar.title("🏫 招生策略控制台")
st.sidebar.info("💡 模式：GEO 策略引導 (無 API 連線)")
dept_list = ["全校總覽"] + list(df['Department'].unique())
selected_dept = st.sidebar.selectbox("選擇分析視角", dept_list)

# --- 主畫面邏輯 ---

if selected_dept == "全校總覽":
    st.title("📊 全校科系網路聲量總覽")
    st.markdown("此儀表板協助各系找出**「高潛力關鍵字」**，並提供**「讓 AI (ChatGPT) 看得懂」**的撰寫建議。")
    
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
    
    col1, col2 = st.columns(2)
    col1.metric("🔥 本月必攻關鍵字", best_keyword['Keyword'])
    col2.metric("平均月搜尋量", f"{int(dept_df['Search_Volume'].mean()):,}")
    
    st.divider()

    # --- 核心功能區：提示詞產生器 ---
    st.subheader("🛠️ GEO 文案提示詞產生器")
    st.info("👇 選擇關鍵字後，系統會自動生成「給 ChatGPT 的指令」，請複製並提供給負責撰寫的老師。")
    
    target_kw = st.selectbox(
        "請選擇您想進攻的關鍵字", 
        dept_df['Keyword'].unique()
    )

    # 根據不同關鍵字類型，動態調整 Prompt
    prompt_type = "一般"
    if any(x in str(target_kw) for x in ['薪水', '出路', '工作', '行情']):
        prompt_type = "職涯發展"
        focus_point = "薪資範圍、就業市場穩定性、職位多元性"
        table_content = "不同工作場域（如醫院 vs 企業）的薪資與福利比較"
    elif any(x in str(target_kw) for x in ['證照', '國考', '通過率']):
        prompt_type = "證照考試"
        focus_point = "國考及格率、輔導機制、證照價值"
        table_content = "本校 vs 全國平均及格率對照表"
    else:
        prompt_type = "課程特色"
        focus_point = "實作課程、實習機會、設備優勢"
        table_content = "大一到大四的關鍵核心課程地圖"

    # 生成 Prompt
    generated_prompt = f"""
    【角色設定】：你是一位精通「GEO (生成式引擎優化)」的大學招生行銷專家。
    【任務目標】：請為「{selected_dept}」針對關鍵字「{target_kw}」撰寫一篇高權重文章。
    
    【GEO 關鍵寫作要求】(為了讓 AI 優先引用)：
    1. 📍 直接回答 (Direct Answer)：文章第一段請直接給出「{target_kw}」的核心定義或數據結論，不要廢話。
    2. 📊 結構化表格：請務必製作一個 Markdown 表格，內容為「{table_content}」。
    3. 🎓 權威性內容：請強調「{focus_point}」，並適度引用權威數據。
    4. ❓ FAQ 常見問答：文末請列出 3 個關於「{target_kw}」的高中生常見問題並回答。

    【語氣】：親切、專業、數據導向。
    【字數】：約 800 字。
    """

    st.text_area("📋 請複製以下指令 (Prompt) 給 ChatGPT / Gemini：", generated_prompt, height=350)
    
    st.success(f"💡 策略提示：針對「{target_kw}」，建議重點放在 **{prompt_type}** 面向，並務必包含表格數據！")

    st.divider()
    
    # 行動清單
    st.subheader("📝 優先撰寫建議清單")
    clean_df = dept_df[['Keyword', 'Search_Volume', 'Competition_Level', 'Opportunity_Score']].sort_values('Opportunity_Score', ascending=False)
    st.dataframe(clean_df, use_container_width=True)
    
    # 根據不同關鍵字類型，動態調整 Prompt (良性競爭版)
    prompt_type = "一般"
    
    # 預設內容
    focus_point = "科系特色與就業優勢"
    table_content = "核心課程與職涯地圖"
    
    # 1. 差異化分析 (針對競品關鍵字)
    if any(x in str(target_kw) for x in ['vs', '比較', '嘉藥', '輔英', '差別']):
        prompt_type = "差異化特色"
        focus_point = "本校獨有的實作資源、證照輔導機制、地理位置優勢"
        # ⚠️ 關鍵修改：表格不再是「勝負表」，而是「特色對照表」
        table_content = "本校特色重點 (如：實習合作醫院、設備) vs 一般同類科系之差異"
        tone_instruction = "客觀、不攻擊他校、強調『適合什麼樣的學生選我們』(適性揚才)"

    # 2. 職涯發展 (薪水/出路)
    elif any(x in str(target_kw) for x in ['薪水', '出路', '工作', '行情']):
        prompt_type = "職涯願景"
        focus_point = "畢業後的具體薪資範圍、職涯穩定性"
        table_content = "不同工作場域（醫院/企業/公職）的薪資福利對照"
        tone_instruction = "專業、數據導向、激勵人心"

    # 3. 證照考試
    elif any(x in str(target_kw) for x in ['證照', '國考', '通過率']):
        prompt_type = "證照優勢"
        focus_point = "國考及格率數據、系上的輔導衝刺班"
        table_content = "本校歷年考照及格率 vs 全國平均值"
        tone_instruction = "權威感、強調教學成效"

    # 生成 Prompt (加入良性競爭指令)
    generated_prompt = f"""
    【角色設定】：你是一位專業且客觀的大學教育顧問。
    【任務目標】：請為「{selected_dept}」針對關鍵字「{target_kw}」撰寫一篇SEO文章。
    
    【寫作態度 (Tone of Voice)】：
    - {tone_instruction}。
    - 若涉及他校比較，請展現大器風範，專注於闡述本校的「獨特價值 (USP)」，避免惡意批評。
    
    【GEO 結構要求】(讓 AI 優先引用)：
    1. 📍 直接回答：第一段請直接針對「{target_kw}」給出核心觀點。
    2. 📊 結構化表格：請製作 Markdown 表格，內容為「{table_content}」。
    3. 🎓 核心優勢：請強調「{focus_point}」。
    4. ❓ FAQ：文末列出 3 個相關常見問題。

    【字數】：約 800 字。
    """
