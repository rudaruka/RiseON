import streamlit as st
from streamlit_mic_recorder import mic_recorder
import os
from utils import transcribe_audio, analyze_presentation, get_feedback
import tempfile

# 페이지 설정
st.set_page_config(page_title="발표 도우미 AI", page_icon="🎤", layout="centered")

# 스타일 설정
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #4CAF50;
        color: white;
    }
    .reportview-container .main .block-container {
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎤 발표 능력 및 학습 습관 개선 도우미")
st.markdown("""
이 앱은 여러분의 발표 습관을 분석하여 더 나은 학습과 발표를 돕습니다.
녹음 버튼을 눌러 발표 연습을 시작해보세요!
""")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 프로젝트 정보")
    st.write("**주제:** 발표 능력 및 학습 습관 개선을 위한 웹 기반 도우미")
    st.write("**주요 기능:**")
    st.write("- 음성 녹음 및 텍스트 변환(STT)")
    st.write("- 말하기 속도(WPM) 분석")
    st.write("- 침묵 구간 감지")
    st.write("- 맞춤형 피드백 제공")
    st.divider()
    st.info("💡 OpenAI Whisper API를 사용하여 정확한 음성 인식을 수행합니다.")

# 세션 상태 초기화
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'results' not in st.session_state:
    st.session_state.results = None

# 음성 녹음 섹션
st.subheader("1. 발표 녹음하기")
st.write("아래 버튼을 눌러 녹음을 시작하고, 발표가 끝나면 중지 버튼을 눌러주세요.")

audio_data = mic_recorder(
    start_prompt="⏺️ 녹음 시작",
    stop_prompt="⏹️ 녹음 중지",
    just_once=True,
    use_container_width=True,
    key='recorder'
)

if audio_data:
    st.audio(audio_data['bytes'])
    
    if st.button("🚀 분석 시작하기"):
        with st.spinner("음성을 분석 중입니다... 잠시만 기다려주세요."):
            # 임시 파일 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_data['bytes'])
                tmp_path = tmp_file.name

            try:
                # 1. STT (텍스트 변환)
                transcript = transcribe_audio(tmp_path)
                
                # 2. 분석 수행
                analysis = analyze_presentation(tmp_path, transcript)
                
                # 3. 피드백 생성
                feedback = get_feedback(analysis)
                
                # 결과 저장
                st.session_state.results = {
                    "transcript": transcript,
                    "analysis": analysis,
                    "feedback": feedback
                }
                st.session_state.analysis_done = True
                
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {e}")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

# 결과 출력 섹션
if st.session_state.analysis_done and st.session_state.results:
    res = st.session_state.results
    
    st.divider()
    st.subheader("2. 분석 결과 요약")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("⏱️ 총 발표 시간", f"{int(res['analysis']['duration'])}초")
    col2.metric("📊 말하기 속도", f"{res['analysis']['wpm']} WPM")
    col3.metric("🔇 침묵 구간", f"{res['analysis']['silent_count']}회")
    
    with st.expander("📝 변환된 텍스트 확인"):
        st.write(res['transcript'])
    
    st.subheader("3. 💡 AI 맞춤 피드백")
    for f in res['feedback']:
        st.markdown(f)
        
    st.success("분석이 완료되었습니다! 피드백을 바탕으로 다시 연습해보세요.")
    
    if st.button("🔄 다시 하기"):
        st.session_state.analysis_done = False
        st.session_state.results = None
        st.rerun()

st.divider()
st.caption("© 2024 발표 도우미 AI - 학생들의 학습과 성장을 응원합니다.")
