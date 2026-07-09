import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# 페이지 레이아웃 설정
st.set_page_config(layout="wide", page_title="한/미 주가 대시보드")
st.title("📊 한/미 주요 기업 주가 대시보드")
st.caption("yfinance 라이브러리를 통해 수집한 데이터를 시각화합니다.")

# 대상 종목 사전 정의
stocks = {
    "미국 주식": {
        "Apple (AAPL)": "AAPL",
        "Microsoft (MSFT)": "MSFT",
        "NVIDIA (NVDA)": "NVDA",
        "Tesla (TSLA)": "TSLA"
    },
    "한국 주식": {
        "삼성전자 (005930)": "005930.KS",
        "SK하이닉스 (000660)": "000660.KS",
        "NAVER (035420)": "035420.KS",
        "현대차 (005380)": "005380.KS"
    }
}

# 사이드바 구성
st.sidebar.header("설정 변경")
market = st.sidebar.selectbox("시장 선택", list(stocks.keys()))
selected_stock_name = st.sidebar.selectbox("종목 선택", list(stocks[market].keys()))
ticker_symbol = stocks[market][selected_stock_name]

period = st.sidebar.selectbox("조회 기간", ["1d", "5d", "1mo", "3mo", "1y", "2y"])

# 데이터 간격 설정 (조회 기간에 맞춤)
interval_mapping = {
    "1d": "1m",
    "5d": "5m",
    "1mo": "1d",
    "3mo": "1d",
    "1y": "1d",
    "2y": "1d"
}
interval = interval_mapping[period]

# 데이터 호출 함수 (일정 시간 동안 캐시 적용)
@st.cache_data(ttl=60)
def fetch_stock_data(ticker, p, i):
    data = yf.download(ticker, period=p, interval=i)
    return data

try:
    df = fetch_stock_data(ticker_symbol, period, interval)

    if not df.empty:
        # 데이터프레임이 Multi-Index 컬럼 구조일 경우를 대비해 단일 컬럼으로 정규화
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        # 최신 및 직전 가격 산출
        current_price = float(df['Close'].iloc[-1])
        prev_price = float(df['Close'].iloc[-2]) if len(df) > 1 else current_price
        price_diff = current_price - prev_price
        pct_change = (price_diff / prev_price) * 100

        # 지표 표시
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label=f"{selected_stock_name} 현재가",
                value=f"{current_price:,.2f}",
                delta=f"{price_diff:+,.2f} ({pct_change:+.2f}%)"
            )
        with col2:
            st.metric("기간 중 고가", f"{df['High'].max():,.2f}")
        with col3:
            st.metric("기간 중 저가", f"{df['Low'].min():,.2f}")

        # 차트 시각화
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name="주가"
        ))
        fig.update_layout(
            title=f"{selected_stock_name} 차트 (기간: {period}, 주기: {interval})",
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

        # 세부 데이터 표 제공
        st.subheader("최근 거래 데이터")
        st.dataframe(df.tail(10).sort_index(ascending=False))
        
    else:
        st.warning("데이터를 가져오는 과정에서 누락이 발생했습니다. 다시 시도해 주세요.")

except Exception as e:
    st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
