import streamlit as st
import yfinance as yf
import pandas as pd

# 설정
st.set_page_config(layout="wide", page_title="Custom 주가 대시보드")
st.title("📈 한/미 주가 등락 모니터링 대시보드")

# 기본 20개 종목의 한글/영문 정식 명칭 매핑 사전
DEFAULT_NAMES = {
    "005930.KS": "삼성전자",
    "000660.KS": "SK하이닉스",
    "066570.KS": "LG전자",
    "035720.KS": "카카오",
    "005380.KS": "현대자동차",
    "000270.KS": "기아",
    "068270.KS": "셀트리온",
    "051910.KS": "LG화학",
    "207940.KS": "삼성바이오로직스",
    "005490.KS": "POSCO홀딩스",
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "NVDA": "NVIDIA Corporation",
    "TSLA": "Tesla, Inc.",
    "AMZN": "Amazon.com, Inc.",
    "GOOGL": "Alphabet Inc. (Google)",
    "META": "Meta Platforms, Inc.",
    "NFLX": "Netflix, Inc.",
    "AMD": "Advanced Micro Devices",
    "AVGO": "Broadcom Inc."
}

# 기본 20개 종목 리스트 정의 (yfinance 티커 형식)
default_tickers = (
    "005930.KS, 000660.KS, 066570.KS, 035720.KS, 005380.KS, "
    "000270.KS, 068270.KS, 051910.KS, 207940.KS, 005490.KS, "
    "AAPL, MSFT, NVDA, TSLA, AMZN, GOOGL, META, NFLX, AMD, AVGO"
)

# [사이드바 상단] 종목 목록 편집 영역
st.sidebar.header("종목 커스텀 설정")
st.sidebar.write("조회할 종목 티커를 쉼표(,)로 구분하여 수정할 수 있습니다.")
user_input = st.sidebar.text_area("종목 티커 목록", value=default_tickers, height=150)

# 입력값 파싱
tickers = [t.strip() for t in user_input.split(",") if t.strip()]

# [사이드바 하단] 종목 티커 검색 기능 추가
st.sidebar.markdown("---")
st.sidebar.header("🔍 종목 티커 검색기")
st.sidebar.write("회사명이나 브랜드를 한글 또는 영어로 검색해 보세요.")
search_query = st.sidebar.text_input("검색어 입력", placeholder="예: 삼성전자, Apple, Nvidia")

# 검색어가 입력되었을 때 실행
if search_query:
    try:
        # 야후 파이낸스 검색 API 호출
        search_results = yf.Search(search_query, max_results=5).quotes
        if search_results:
            st.sidebar.write("**검색 결과** (우측 아이콘을 클릭하여 복사):")
            for quote in search_results:
                symbol = quote.get('symbol')
                name = quote.get('shortname') or quote.get('longname') or '이름 없음'
                exch = quote.get('exchDisp') or quote.get('exchange') or ''
                
                # 티커 복사가 용이하도록 코드 블록 스타일로 출력
                st.sidebar.code(symbol, language="text")
                st.sidebar.caption(f"{name} | {exch}")
        else:
            st.sidebar.info("일치하는 검색 결과가 없습니다.")
    except Exception as e:
        st.sidebar.error("검색 중 오류가 발생했습니다.")

# 회사 이름을 가져오는 캐시 함수 (새로운 커스텀 티커 입력 시 실시간 조회)
@st.cache_data(ttl=86400) # 24시간 동안 캐시 유지
def get_company_name(ticker):
    if ticker in DEFAULT_NAMES:
        return DEFAULT_NAMES[ticker]
    try:
        t = yf.Ticker(ticker)
        name = t.info.get('shortName') or t.info.get('longName') or ticker
        return name
    except Exception:
        return ticker

# 데이터 호출 함수
@st.cache_data(ttl=60) # 1분 동안 캐시 유지
def fetch_stock_data(ticker_list):
    df = yf.download(ticker_list, period="5d")
    return df

# 동기화 처리
if st.sidebar.button("데이터 동기화 (새로고침)") or 'df_result' not in st.session_state:
    if tickers:
        with st.spinner("금융 데이터 및 회사명을 수집하고 있습니다..."):
            try:
                df = fetch_stock_data(tickers)
                
                # 단일 종목 예외 처리 및 컬럼 정리
                if isinstance(df.columns, pd.MultiIndex):
                    close_df = df['Close']
                else:
                    close_df = pd.DataFrame(df['Close'])
                    close_df.columns = tickers

                results = []
                for ticker in tickers:
                    if ticker in close_df.columns:
                        series = close_df[ticker].dropna()
                        if len(series) >= 1:
                            current = series.iloc[-1]
                            prev_close = series.iloc[-2] if len(series) >= 2 else current
                            diff = current - prev_close
                            pct = (diff / prev_close) * 100 if prev_close else 0.0
                            
                            # 정식 회사 이름 획득
                            company_name = get_company_name(ticker)
                            
                            results.append({
                                "종목명": company_name,
                                "티커": ticker,
                                "현재가": round(current, 2),
                                "전일 종가": round(prev_close, 2),
                                "대비 변동": round(diff, 2),
                                "등락률(%)": round(pct, 2)
                            })
                
                st.session_state.df_result = pd.DataFrame(results)
            except Exception as e:
                st.error(f"데이터를 가져오는 도중 오류가 발생했습니다: {e}")
    else:
        st.warning("입력된 티커가 존재하지 않습니다.")

# 결과 출력
if 'df_result' in st.session_state and not st.session_state.df_result.empty:
    df_disp = st.session_state.df_result.copy()
    
    # 등락에 따른 스타일링 적용 함수
    def color_change(val):
        color = 'red' if val > 0 else 'blue' if val < 0 else 'white'
        return f'color: {color}; font-weight: bold;'

    # 1. 그리드 뷰
    st.subheader("📌 종목별 현황 요약")
    cols = st.columns(4)
    for index, row in df_disp.iterrows():
        col_idx = index % 4
        with cols[col_idx]:
            sign = "+" if row["대비 변동"] > 0 else ""
            st.metric(
                label=row["종목명"],
                value=f"{row['현재가']:,.0f}",
                delta=f"{sign}{row['대비 변동']:,.0f} ({row['등락률(%)']:+.1f}%)"
            )
            st.write("---")

    # 2. 상세 표 제공 및 정렬 기능
    st.subheader("📋 상세 데이터 시트")
    df_sorted = df_disp.sort_values(by="등락률(%)", ascending=False).reset_index(drop=True)
    
    st.dataframe(
        df_sorted.style.map(color_change, subset=["대비 변동", "등락률(%)"]),
        use_container_width=True
    )
else:
    st.info("사이드바에서 설정한 후 '데이터 동기화' 버튼을 눌러 대시보드를 구동해 주세요.")
