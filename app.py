import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import urllib.parse
import json
import time
import textwrap
from openai import OpenAI

# ------------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------------
st.set_page_config(
    page_title="AX Intelligence Hub",
    page_icon="🟥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize dark mode state
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# ------------------------------------------------------------------
# Design System & Colors (LG Brand Guide Applied)
# ------------------------------------------------------------------
is_dark = st.session_state.dark_mode

MAIN_MAGENTA = "#A50034"  # LG 매젠타
SUB_GRAY = "#6B6B6B"      # LG 그레이

# Theme variables
bg_color = "#121212" if is_dark else "#FFFFFF"
sidebar_bg = "#1A1A1A" if is_dark else "#F5F5F7"
text_color = "#E5E5E7" if is_dark else "#1D1D1F"
card_bg = "#1E1E1E" if is_dark else "#FAFAFB"
card_border = "#2C2C2C" if is_dark else "#E5E5E7"
shadow_color = "rgba(0,0,0,0.4)" if is_dark else "rgba(165,0,52,0.06)"
muted_text = "#9A9A9A" if is_dark else "#6B6B6B"
table_hdr_bg = "#252525" if is_dark else "#F1F1F3"

# ------------------------------------------------------------------
# Safe HTML Rendering Helper (Removes Indentation formatting errors)
# ------------------------------------------------------------------
def render_html(html_str):
    """들여쓰기로 인한 마크다운 코드 블록 오작동을 차단합니다."""
    cleaned = textwrap.dedent(html_str).strip()
    st.markdown(cleaned, unsafe_allow_html=True)

# ------------------------------------------------------------------
# Core Custom CSS Injection (Executive Report Style)
# ------------------------------------------------------------------
css_code = f"""
    <style>
    /* Global Font & Color Overrides (System Sans-Serif) */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif !important;
    }}
    
    /* Sidebar Overrides */
    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
        border-right: 1px solid {card_border} !important;
    }}
    [data-testid="stSidebar"] * {{
        color: {text_color} !important;
        font-family: -apple-system, "Apple SD Gothic Neo", sans-serif !important;
    }}
    
    /* Elements Typography */
    h1, h2, h3, h4, h5, h6, p, label, span {{
        color: {text_color} !important;
    }}
    
    /* Premium Hover Action: Search & Trigger Buttons */
    div.stButton > button {{
        background-color: {MAIN_MAGENTA} !important;
        color: #FFFFFF !important;
        border: 1px solid {MAIN_MAGENTA} !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.35s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }}
    div.stButton > button:hover {{
        background-color: #820028 !important;
        border-color: #820028 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px {shadow_color} !important;
    }}
    
    /* Minimalist Round Theme Toggle Style */
    .theme-toggle-container div.stButton > button {{
        background-color: transparent !important;
        color: {text_color} !important;
        border: 1px solid {card_border} !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    .theme-toggle-container div.stButton > button:hover {{
        background-color: {card_bg} !important;
        border-color: {MAIN_MAGENTA} !important;
        transform: scale(1.05) !important;
        box-shadow: none !important;
    }}

    /* Custom Responsive KPI Card Design with shadows */
    .kpi-card {{
        background-color: {card_bg};
        border-left: 4px solid {MAIN_MAGENTA};
        border-right: 1px solid {card_border};
        border-top: 1px solid {card_border};
        border-bottom: 1px solid {card_border};
        border-radius: 6px;
        padding: 18px 20px;
        box-shadow: 0 4px 10px {shadow_color};
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 12px;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(165,0,52,0.12);
    }}
    .kpi-icon {{
        font-size: 26px;
        color: {MAIN_MAGENTA};
    }}
    .kpi-title {{
        font-size: 11.5px;
        font-weight: 600;
        color: {muted_text};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .kpi-val {{
        font-size: 20px;
        font-weight: 700;
        color: {text_color};
        margin-top: 2px;
    }}
    
    /* Responsive custom table wrapper for horizontal scroll */
    .table-responsive-container {{
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        margin: 15px 0;
        border-radius: 6px;
        border: 1px solid {card_border};
    }}
    .executive-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        text-align: left;
        background-color: {card_bg};
        white-space: nowrap; /* Forces horizontal scroll on mobile */
    }}
    .executive-table th {{
        background-color: {table_hdr_bg};
        color: {text_color};
        font-weight: 600;
        padding: 12px 16px;
        border-bottom: 2px solid {MAIN_MAGENTA};
    }}
    .executive-table td {{
        padding: 12px 16px;
        border-bottom: 1px solid {card_border};
        color: {text_color};
    }}
    .executive-table tr:hover {{
        background-color: {"#252525" if is_dark else "#F9FAFB"};
    }}
    
    /* Badge styling */
    .badge {{
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
    }}
    .badge-high {{ background-color: #FFE3E3 !important; color: #B01A1A !important; }}
    .badge-mid {{ background-color: #FFF4E6 !important; color: #D9480F !important; }}
    .badge-low {{ background-color: #EBFBEE !important; color: #2B8A3E !important; }}
    .badge-pos {{ background-color: #E6FCF5 !important; color: #0CA678 !important; }}
    .badge-neg {{ background-color: #FFF5F5 !important; color: #FA5252 !important; }}
    .badge-neu {{ background-color: #F1F3F5 !important; color: #495057 !important; }}
    
    /* Skeleton Animation UI */
    @keyframes skeleton-pulse {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}
    .skeleton-box {{
        background: linear-gradient(-90deg, {card_bg} 0%, {"#2C2C2C" if is_dark else "#EAEAEA"} 50%, {card_bg} 100%);
        background-size: 300% 300%;
        animation: skeleton-pulse 1.4s ease infinite;
        border-radius: 6px;
        margin-bottom: 10px;
    }}
    
    /* Footer Style */
    .lg-footer {{
        margin-top: 60px;
        text-align: center;
        padding: 20px;
        border-top: 1px solid {card_border};
        color: {muted_text};
        font-size: 12px;
        font-weight: 500;
        letter-spacing: 0.5px;
    }}
    </style>
"""
render_html(css_code)

# ------------------------------------------------------------------
# Data Processing & API Logics
# ------------------------------------------------------------------

def search_google_news(query, num_results=5):
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return []
        root = ET.fromstring(response.content)
        articles = []
        for item in root.findall('.//item')[:num_results]:
            title_full = item.find('title').text if item.find('title') is not None else ""
            if " - " in title_full:
                parts = title_full.rsplit(" - ", 1)
                title, source = parts[0], parts[1]
            else:
                title = title_full
                source = item.find('source').text if item.find('source') is not None else "Google News"
                
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            if pub_date:
                try:
                    pub_date = pd.to_datetime(pub_date).strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            articles.append({"title": title, "link": link, "date": pub_date, "source": source})
        return articles
    except Exception as e:
        st.sidebar.error(f"뉴스 수집 실패: {str(e)}")
        return []

def generate_fallback_analysis(title):
    category = "비즈니스"
    importance = "중"
    sentiment = "중립"
    
    if any(w in title for w in ["기술", "개발", "AI", "모델", "칩", "플랫폼", "시스템", "LLM", "아키텍처", "반도체"]):
        category = "기술"
    elif any(w in title for w in ["법", "규제", "정부", "가이드라인", "소송", "제재", "의회", "법안"]):
        category = "규제"
        
    if any(w in title for w in ["최초", "세계", "돌파", "인수", "합병", "M&A", "투자", "경고", "위기"]):
        importance = "상"
    elif any(w in title for w in ["출시", "공개", "협력", "MOU"]):
        importance = "중"
    else:
        importance = "하"
        
    pos_keywords = ["출시", "성공", "돌파", "성장", "최초", "협력", "상승", "투자", "유치", "수주", "개발", "혁신", "세계 1위"]
    neg_keywords = ["우려", "하락", "위기", "규제", "피소", "경고", "제재", "소송", "논란", "갈등", "부진", "실패", "감소"]
    
    if any(w in title for w in neg_keywords):
        sentiment = "부정"
    elif any(w in title for w in pos_keywords):
        sentiment = "긍정"
        
    summary = [
        f"1. 본 조사는 '{title}'에 관한 업계 동향 파악을 기반으로 하고 있습니다.",
        "2. 경쟁사 조치 사항 및 기술 이정표가 당사 비즈니스 환경에 미치는 시사점 검토가 권장됩니다.",
        "3. 해당 타겟 이슈에 관한 세부 모니터링 체계를 확보해 나갈 예정입니다."
    ]
    return {"summary": "\n".join(summary), "category": category, "importance": importance, "sentiment": sentiment}

def analyze_news_item(api_key, title, date, source):
    if not api_key:
        return generate_fallback_analysis(title)
    client = OpenAI(api_key=api_key)
    prompt = f"""
    당신은 기업의 경쟁사 정보 및 산업 동향을 수집하고 분석하는 전문 리서처입니다.
    다음 뉴스의 제목을 보고 요약, 분류 및 감성 분류를 처리해주세요.
    
    뉴스 제목: {title}
    발행일: {date}
    출처: {source}
    
    반드시 하단 JSON 형식으로만 응답해주세요:
    {{
        "summary": "1. 첫 번째 줄 요약 내용\\n2. 두 번째 줄 요약 내용\\n3. 세 번째 줄 요약 내용",
        "category": "기술" 또는 "비즈니스" 또는 "규제",
        "importance": "상" 또는 "중" 또는 "하",
        "sentiment": "긍정" 또는 "부정" 또는 "중립"
    }}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
            timeout=8.0
        )
        data = json.loads(response.choices[0].message.content)
        return {
            "summary": data.get("summary", "분석 실패"),
            "category": data.get("category", "비즈니스"),
            "importance": data.get("importance", "중"),
            "sentiment": data.get("sentiment", "중립")
        }
    except:
        return generate_fallback_analysis(title)

# ------------------------------------------------------------------
# Header Section (AX Intelligence Hub Style)
# ------------------------------------------------------------------
header_col, toggle_col = st.columns([6, 1])

with header_col:
    header_html = f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-top: 10px;">
            <div style="width: 24px; height: 24px; background-color: {MAIN_MAGENTA}; border-radius: 50%;"></div>
            <h1 style="font-size: 26px; font-weight: 800; letter-spacing: -0.5px; margin:0; padding:0;">
                AX Intelligence Hub
            </h1>
        </div>
        <p style='color: {muted_text}; font-size: 13px; margin-top: 5px;'>경쟁사 동향 및 최신 기술 인사이트 실시간 브리핑 리포트</p>
    """
    render_html(header_html)

with toggle_col:
    st.markdown('<div class="theme-toggle-container" style="display: flex; justify-content: flex-end; margin-top: 15px;">', unsafe_allow_html=True)
    if st.button("🌙" if not is_dark else "☀️", key="theme_toggle"):
        st.session_state.dark_mode = not is_dark
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<hr style='border: none; border-top: 1px solid " + card_border + "; margin: 15px 0;'>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Sidebar Controls
# ------------------------------------------------------------------
st.sidebar.markdown(
    f"""
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 20px;">
        <div style="width: 14px; height: 14px; background-color: {MAIN_MAGENTA}; border-radius: 2px;"></div>
        <span style="font-weight: 700; font-size: 15px;">LG AX Dashboard</span>
    </div>
    """, unsafe_allow_html=True
)

api_key = st.sidebar.text_input("OpenAI API Key (선택 사항)", type="password")

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 동향 모니터링 필터")

filter_category = st.sidebar.multiselect(
    "카테고리 구분",
    options=["기술", "비즈니스", "규제"],
    default=["기술", "비즈니스", "규제"]
)

filter_importance = st.sidebar.multiselect(
    "중요도 등급",
    options=["상", "중", "하"],
    default=["상", "중", "하"]
)

filter_sentiment = st.sidebar.multiselect(
    "기사 감성 지표",
    options=["긍정", "중립", "부정"],
    default=["긍정", "중립", "부정"]
)

# ------------------------------------------------------------------
# Main Panel: Research Query Inputs
# ------------------------------------------------------------------
st.markdown("<h4 style='font-size: 15px; font-weight: 700; margin-bottom:10px;'>📋 전용 프리셋 검색 키워드</h4>", unsafe_allow_html=True)
p_col1, p_col2, p_col3 = st.columns(3)
selected_preset = None

if p_col1.button("🏢 LG AI 전환", use_container_width=True):
    selected_preset = "LG AI 전환"
if p_col2.button("📈 산업별 AI 전략 2026", use_container_width=True):
    selected_preset = "산업별 AI 전략 2026"
if p_col3.button("👥 AI 경쟁 동향", use_container_width=True):
    selected_preset = "AI 경쟁 동향"

default_query = selected_preset if selected_preset else "LG AI 전환"
search_query = st.text_input("검색 질의어 입력", value=default_query, label_visibility="collapsed")

# Start Extraction Button
btn_trigger = st.button("수집 및 분석 시작", type="primary", use_container_width=True)

# ------------------------------------------------------------------
# Logic Execution (Progress Bar & Live Updates)
# ------------------------------------------------------------------
if btn_trigger:
    with st.status("🔍 실시간 뉴스 수집 및 AX 분석 엔진 구동 중...", expanded=True) as status:
        status.write("1. 구글 실시간 뉴스 데이터 수집 중...")
        raw_news = search_google_news(search_query, num_results=5)
        
        if not raw_news:
            status.update(label="수집 실패", state="error")
            st.error("데이터 수집 도중 연결 오류가 발생했거나 검색 결과가 없습니다.")
        else:
            analyzed_data = []
            status.write("2. AI 동향 분석 및 감성 분류 시작...")
            
            progress_bar = st.progress(0.0)
            
            for idx, item in enumerate(raw_news):
                status.write(f"👉 [{idx+1}/{len(raw_news)}] 분석 진행 중: '{item['title'][:18]}...'")
                analysis = analyze_news_item(api_key, item['title'], item['date'], item['source'])
                item.update(analysis)
                analyzed_data.append(item)
                progress_bar.progress((idx + 1) / len(raw_news))
                
            st.session_state['processed_data'] = pd.DataFrame(analyzed_data)
            status.update(label="분석 성공 및 리포팅 로드 완료", state="complete", expanded=False)
            st.rerun()

# ------------------------------------------------------------------
# Report View Block
# ------------------------------------------------------------------
if 'processed_data' in st.session_state and not st.session_state['processed_data'].empty:
    df_full = st.session_state['processed_data']
    
    df_filtered = df_full[
        df_full['category'].isin(filter_category) & 
        df_full['importance'].isin(filter_importance) &
        df_full['sentiment'].isin(filter_sentiment)
    ]
    
    # 1. Premium KPI Display Block (With subtle shadows and symbols)
    st.markdown("<h4 style='font-size: 16px; font-weight: 700; margin: 25px 0 15px 0;'>📊 수집 현황 지표</h4>", unsafe_allow_html=True)
    k_col1, k_col2, k_col3, k_col4 = st.columns(4)
    
    k1_html = f"""
        <div class="kpi-card">
            <div class="kpi-icon">📋</div>
            <div class="kpi-content">
                <div class="kpi-title">전체 동향 정보</div>
                <div class="kpi-val">{len(df_filtered)}건</div>
            </div>
        </div>
    """
    with k_col1:
        render_html(k1_html)
        
    k2_html = f"""
        <div class="kpi-card">
            <div class="kpi-icon" style="color: #0CA678;">🟢</div>
            <div class="kpi-content">
                <div class="kpi-title">긍정적 시그널</div>
                <div class="kpi-val">{len(df_filtered[df_filtered['sentiment'] == "긍정"])}건</div>
            </div>
        </div>
    """
    with k_col2:
        render_html(k2_html)
        
    k3_html = f"""
        <div class="kpi-card">
            <div class="kpi-icon" style="color: #6B6B6B;">⚪</div>
            <div class="kpi-content">
                <div class="kpi-title">중립 정보</div>
                <div class="kpi-val">{len(df_filtered[df_filtered['sentiment'] == "중립"])}건</div>
            </div>
        </div>
    """
    with k_col3:
        render_html(k3_html)
        
    k4_html = f"""
        <div class="kpi-card">
            <div class="kpi-icon" style="color: #FA5252;">🔴</div>
            <div class="kpi-content">
                <div class="kpi-title">부정/위험 시그널</div>
                <div class="kpi-val">{len(df_filtered[df_filtered['sentiment'] == "부정"])}건</div>
            </div>
        </div>
    """
    with k_col4:
        render_html(k4_html)
    
    # 2. Executive Responsive Custom Table (Horizontal scroll support)
    st.markdown("<h4 style='font-size: 16px; font-weight: 700; margin-top: 25px;'>📋 핵심 브리핑 목록</h4>", unsafe_allow_html=True)
    
    if df_filtered.empty:
        st.info("선택하신 필터 조건에 부합하는 데이터가 존재하지 않습니다. 사이드바 필터를 조정해 주세요.")
    else:
        # Build individual rows in dedented format to prevent markdown processing
        table_rows = []
        for _, row in df_filtered.iterrows():
            imp_class = "badge-high" if row['importance'] == "상" else ("badge-mid" if row['importance'] == "중" else "badge-low")
            sent_class = "badge-pos" if row['sentiment'] == "긍정" else ("badge-neg" if row['sentiment'] == "부정" else "badge-neu")
            
            row_html = f"""
                <tr>
                    <td><span class="badge {imp_class}">중요도: {row['importance']}</span></td>
                    <td><b>{row['category']}</b></td>
                    <td><span class="badge {sent_class}">{row['sentiment']}</span></td>
                    <td style="white-space: normal; font-weight: 500;">{row['title']}</td>
                    <td>{row['source']}</td>
                    <td>{row['date']}</td>
                </tr>
            """
            table_rows.append(textwrap.dedent(row_html).strip())
            
        joined_rows = "\n".join(table_rows)
        
        # Assemble overall table structure
        table_html = f"""
            <div class="table-responsive-container">
                <table class="executive-table">
                    <thead>
                        <tr>
                            <th>중요도</th>
                            <th>카테고리</th>
                            <th>감성</th>
                            <th>뉴스 제목</th>
                            <th>출처</th>
                            <th>발행일시</th>
                        </tr>
                    </thead>
                    <tbody>
                        {joined_rows}
                    </tbody>
                </table>
            </div>
        """
        render_html(table_html)
        
        # 3. Comprehensive Expandable Report Cards (Executive Deep-dive)
        st.markdown("<h4 style='font-size: 16px; font-weight: 700; margin-top: 25px;'>🔍 동향 상세 요약서</h4>", unsafe_allow_html=True)
        for index, row in df_filtered.iterrows():
            imp_html = f'<span class="badge badge-high">중요도: 상</span>' if row['importance'] == "상" else (f'<span class="badge badge-mid">중요도: 중</span>' if row['importance'] == "중" else f'<span class="badge badge-low">중요도: 하</span>')
            sent_html = f'<span class="badge badge-pos">🟢 긍정</span>' if row['sentiment'] == "긍정" else (f'<span class="badge badge-neg">🔴 부정</span>' if row['sentiment'] == "부정" else f'<span class="badge badge-neu">⚪ 중립</span>')
            
            with st.expander(f"[{row['category']}] {row['title']}"):
                col_a, col_b = st.columns([4, 2])
                with col_a:
                    st.markdown(f"**출처:** {row['source']} &nbsp;|&nbsp; **발행일시:** {row['date']}")
                with col_b:
                    st.markdown(f"<div style='text-align: right;'>{imp_html} &nbsp; {sent_html}</div>", unsafe_allow_html=True)
                    
                st.markdown("<div style='margin-top: 10px; font-size: 13.5px; line-height: 1.6;'>", unsafe_allow_html=True)
                st.markdown("**📌 분석 요약 리포트 (3줄 요약)**")
                for line in row['summary'].split("\n"):
                    st.write(line)
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown(f"[🔗 뉴스 기사 외부링크 바로가기]({row['link']})")
                
        # 4. Excel-compatible Export Button
        st.markdown("---")
        csv_data = df_filtered.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSV 보고서 내보내기 (Excel 한글 호환)",
            data=csv_data,
            file_name=f"AX_Intel_Report_{search_query.replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True
        )
else:
    st.info("상단 프리셋 키워드 클릭 후, '수집 및 분석 시작'을 통해 리포트를 최초 가동시켜 주십시오.")

# Footer Layout
footer_html = f"""
    <div class="lg-footer">
        Powered by Google AI Studio · LG AX 교육 <br>
        <span style="font-size: 10.5px; opacity: 0.7;">Copyright © 2026 AX Intelligence Hub. All rights reserved.</span>
    </div>
"""
render_html(footer_html)