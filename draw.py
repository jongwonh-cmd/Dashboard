import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io

# 1. 페이지 기본 설정 (태블릿 화면에 맞춤)
st.set_page_config(
    page_title="🎨 알록달록 스케치북",
    page_icon="🎨",
    layout="wide"  # 태블릿 화면을 넓게 쓰기 위해 wide 모드로 설정
)

# 2. 세션 상태 초기화 (그리기 도구 상태 저장용)
if "canvas_key" not in st.session_state:
    st.session_state.canvas_key = 0
if "stroke_color" not in st.session_state:
    st.session_state.stroke_color = "#000000"  # 기본 검은색

# 타이틀 및 안내
st.title("🎨 알록달록 스케치북 🖌️")
st.write("태블릿에서 손가락이나 터치펜으로 예쁘게 그림을 그려보세요!")

# 왼쪽 도구 상자(1), 오른쪽 도화지(3) 비율로 분할
col_tools, col_canvas = st.columns([1, 3])

with col_tools:
    st.subheader("🛠️ 그리기 도구")
    
    # 그리기 모드 선택
    tool = st.radio(
        "무엇으로 그릴까요?",
        ["✏️ 자유롭게 그리기", "📏 반듯한 선", "🟥 네모 그리기", "🟡 동그라미 그리기", "🧹 지우개"],
        index=0
    )
    
    mode_map = {
        "✏️ 자유롭게 그리기": "freedraw",
        "📏 반듯한 선": "line",
        "🟥 네모 그리기": "rect",
        "🟡 동그라미 그리기": "circle",
        "🧹 지우개": "freedraw"
    }
    drawing_mode = mode_map[tool]
    
    # 브러시/선 두께 조절
    stroke_width = st.slider("두께 (크기):", min_value=1, max_value=50, value=8)
    
    # 아이가 터치하기 쉬운 큰 색상 버튼 제공
    st.write("🌈 색깔 선택:")
    color_presets = {
        "🔴 빨강": "#FF0000",
        "🟠 주황": "#FF9800",
        "🟡 노랑": "#FFEB3B",
        "🟢 초록": "#4CAF50",
        "🔵 파랑": "#2196F3",
        "🟣 보라": "#9C27B0",
        "🌸 분홍": "#E91E63",
        "🟤 갈색": "#795548",
        "⚫ 검정": "#000000",
        "⚪ 하양": "#FFFFFF"
    }
    
    # 5열로 나누어 색상 단추 배치
    c_cols = st.columns(5)
    for idx, (name, val) in enumerate(color_presets.items()):
        if c_cols[idx % 5].button(name):
            st.session_state.stroke_color = val
            
    # 정교한 색칠을 원할 때 사용할 수 있는 상세 색상 선택기
    custom_color = st.color_picker("다른 색 고르기", value=st.session_state.stroke_color)
    if custom_color != st.session_state.stroke_color:
        st.session_state.stroke_color = custom_color
        
    st.markdown("---")
    
    # 도화지 배경색 선택
    bg_choice = st.selectbox(
        "도화지 색깔 바꾸기:",
        ["하얀색 도화지", "연노랑색 도화지", "연초록색 도화지", "연하늘색 도화지", "검은색 칠판"]
    )
    bg_colors = {
        "하얀색 도화지": "#FFFFFF",
        "연노랑색 도화지": "#FFFDE7",
        "연초록색 도화지": "#E8F5E9",
        "연하늘색 도화지": "#E1F5FE",
        "검은색 칠판": "#1E1E1E"
    }
    bg_color = bg_colors[bg_choice]

    # 지우개를 선택했을 때는 선 색상을 배경색과 동일하게 맞춤
    if tool == "🧹 지우개":
        current_stroke = bg_color
    else:
        current_stroke = st.session_state.stroke_color

    # 새 도화지 만들기 버튼
    if st.button("🗑️ 처음부터 다시 그리기", use_container_width=True):
        st.session_state.canvas_key += 1
        st.rerun()

with col_canvas:
    # 캔버스 배치 (태블릿 가로 모드에 적합한 가로 750, 세로 550 크기)
    canvas_result = st_canvas(
        fill_color="rgba(0, 0, 0, 0)",  # 도형 안쪽은 채우지 않고 비워둠 (아이가 안쪽을 색칠할 수 있도록)
        stroke_width=stroke_width,
        stroke_color=current_stroke,
        background_color=bg_color,
        height=550,
        width=750,
        drawing_mode=drawing_mode,
        display_toolbar=True,  # 캔버스 자체의 되돌리기(Undo), 다시실행(Redo) 기능 활성화
        key=f"canvas_{st.session_state.canvas_key}"
    )
    
    st.caption("💡 팁: 도화지 왼쪽 위의 화살표(↩)를 눌러 방금 그린 선을 하나씩 취소할 수 있어요.")
    
    # 그림 다운로드 기능
    if canvas_result.image_data is not None:
        img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        
        st.download_button(
            label="💾 내가 그린 멋진 그림 저장하기 (PNG)",
            data=img_bytes,
            file_name="내그림.png",
            mime="image/png",
            use_container_width=True
        )
