import streamlit as st
import yfinance as yf
import pandas as pd

# 설정
st.set_page_config(layout="wide", page_title="Custom 주가 대시보드")
st.title("📈 한/미 주가 등락 모니터링 대시보드")

# 기본 20개 종목 리스트 정의 (yfinance 티커 형식)
default_tickers = (
    "005930.KS, 000660.KS, 035420.KS, 035720.KS, 005380.KS, "
    "000270.KS, 068270.KS, 051910.KS, 207940.KS, 005490.KS, "
    "AAPL, MSFT, NVDA, TSLA, AMZN, GOOGL, META, NFLX, AMD, AVGO"
)

# 사이드바 설정 영역
st.sidebar.header("종목 커스텀 설정")
st.sidebar.write("조회할 종목 티커를 쉼표(,)로 구분하여 수정할 수 있습니다.")
user_input = st.sidebar.text_area("종목 티커 목록", value=default_tickers, height=150)

# 입력값 파싱
tickers = [t.strip() for t in user_input.split(",") if t.strip()]

if st.sidebar.button("데이터 동기화 (새로고침)") or 'df_result' not in st.session_state:
    if tickers:
        with st.spinner("금융 데이터를 수집하고 있습니다..."):
            try:
                # 최근 5일 데이터를 조회하여 주말 및 시차 대응
                df = yf.download(tickers, period="5d")
                
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
                            # 전일 종가 구하기 (데이터가 2개 이상 있을 시)
                            prev_close = series.iloc[-2] if len(series) >= 2 else current
                            diff = current - prev_close
                            pct = (diff / prev_close) * 100 if prev_close else 0.0
                            
                            results.append({
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

    # 1. 그리드 뷰 (상위 카드 형태 4열 배치)
    st.subheader("📌 종목별 현황 요약")
    cols = st.columns(4)
    for index, row in df_disp.iterrows():
        col_idx = index % 4
        with cols[col_idx]:
            sign = "+" if row["대비 변동"] > 0 else ""
            st.metric(
                label=row["티커"],
                value=f"{row['현재가']:,.2f}",
                delta=f"{sign}{row['대비 변동']:,.2f} ({row['등락률(%)']:+.2f}%)"
            )
            st.write("---")

    # 2. 상세 표 제공 및 정렬 기능
    st.subheader("📋 상세 데이터 시트")
    # 등락률 기준으로 내림차순 정렬하여 기본 제공
    df_sorted = df_disp.sort_values(by="등락률(%)", ascending=False).reset_index(drop=True)
    
    st.dataframe(
        df_sorted.style.map(color_change, subset=["대비 변동", "등락률(%)"]),
        use_container_width=True
    )
else:
    st.info("사이드바에서 설정한 후 '데이터 동기화' 버튼을 눌러 대시보드를 구동해 주세요.")
