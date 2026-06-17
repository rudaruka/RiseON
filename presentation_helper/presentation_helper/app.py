import streamlit as st
from streamlit_mic_recorder import mic_recorder
import os
import tempfile
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from utils import transcribe_audio, analyze_presentation, get_feedback

# ──────────────────────────────────────────────
# 페이지 기본 설정
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="RiseOn | AI 발표 도우미",
    page_icon="🎤",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# [버그수정] 원본의 .reportview-container 셀렉터는
#   Streamlit 1.x 이상에서 더 이상 작동하지 않음
#   → .block-container 로 교체
# [업그레이드] 전체 UI 스타일 개선
# ──────────────────────────────────────────────
st.markdown("""
<style>
/* 배경 */
.stApp { background-color: #f1d1d2; }

/* 메인 컨테이너 패딩 */
.block-container { padding-top: 2rem; padding-bottom: 2rem; }

/* 버튼 */
.stButton > button {
    width: 100%;
    border-radius: 8px;
    height: 3em;
    background-color: #4361ee;
    color: white;
    font-weight: 600;
    border: none;
    transition: background-color 0.2s;
}
.stButton > button:hover { background-color: #3a0ca3; }

/* 메트릭 카드 */
[data-testid="metric-container"] {
    background-color: white;
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

/* 점수 배지 */
.score-badge {
    font-size: 3rem;
    font-weight: 700;
    text-align: center;
    padding: 1rem;
    border-radius: 50%;
    width: 110px;
    height: 110px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 1rem;
}
.score-high  { background: #d1fae5; color: #065f46; }
.score-mid   { background: #fef3c7; color: #92400e; }
.score-low   { background: #fee2e2; color: #991b1b; }

/* 피드백 카드 */
.fb-card {
    border-radius: 10px;
    padding: 0.8rem 1.1rem;
    margin-bottom: 0.6rem;
    font-size: 0.95rem;
    line-height: 1.6;
}
.fb-success { background: #ecfdf5; border-left: 4px solid #10b981; }
.fb-warning { background: #fffbeb; border-left: 4px solid #f59e0b; }
.fb-danger  { background: #fef2f2; border-left: 4px solid #ef4444; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 프로젝트 정보")
    st.write("**주제:** 발표 능력 및 학습 습관 개선 웹 기반 도우미")
    st.divider()
    st.write("**주요 기능**")
    st.write("🎙️ 음성 녹음 & 텍스트 변환 (STT)")
    st.write("📊 말하기 속도(WPM) 분석")
    st.write("🔇 침묵 구간 감지")
    st.write("💡 맞춤형 피드백 + 종합 점수")
    st.write("📈 활성도 그래프 시각화")  # [추가]
    st.divider()
    st.info("OpenAI Whisper API로 한국어 음성을 정확하게 인식합니다.")

    # [추가] WPM 기준 안내
    with st.expander("📌 WPM 기준 안내"):
        st.write("- **60 이하** : 너무 느림")
        st.write("- **60–80** : 약간 느림")
        st.write("- **80–160** : 적절 ✅")
        st.write("- **160–180** : 약간 빠름")
        st.write("- **180 이상** : 너무 빠름")

# ──────────────────────────────────────────────
# 타이틀
# ──────────────────────────────────────────────
st.title("🎤 발표 도우미 AI")
st.markdown("발표를 녹음하면 **말하기 속도·침묵 구간·종합 점수**를 자동으로 분석해 드립니다.")

# ──────────────────────────────────────────────
# 세션 상태 초기화
# ──────────────────────────────────────────────
for key, default in [("analysis_done", False), ("results", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

# ──────────────────────────────────────────────
# STEP 1 — 녹음
# ──────────────────────────────────────────────
st.subheader("① 발표 녹음하기")
st.write("아래 버튼을 눌러 녹음을 시작하고, 발표가 끝나면 중지 버튼을 눌러주세요.")

audio_data = mic_recorder(
    start_prompt="⏺️ 녹음 시작",
    stop_prompt="⏹️ 녹음 중지",
    just_once=True,
    use_container_width=True,
    key="recorder",
)

if audio_data:
    st.audio(audio_data["bytes"])
    st.caption(f"녹음 완료 — {len(audio_data['bytes']) / 1024:.1f} KB")

    if st.button("🚀 분석 시작하기"):
        # [버그수정] 이전 결과 초기화 후 분석 시작
        st.session_state.analysis_done = False
        st.session_state.results = None

        with st.spinner("음성을 분석 중입니다… 잠시만 기다려주세요."):
            tmp_path = None
            try:
                # 임시 파일 저장
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(audio_data["bytes"])
                    tmp_path = tmp_file.name

                transcript = transcribe_audio(tmp_path)

                # [버그수정] STT 결과가 에러 문자열인 경우 조기 중단
                if not transcript or transcript.startswith("Error:"):
                    st.error(f"음성 인식에 실패했습니다: {transcript}")
                    st.stop()

                analysis = analyze_presentation(tmp_path, transcript)
                feedback = get_feedback(analysis)

                st.session_state.results = {
                    "transcript": transcript,
                    "analysis": analysis,
                    "feedback": feedback,
                }
                st.session_state.analysis_done = True

            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {e}")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)

# ──────────────────────────────────────────────
# STEP 2 — 결과 출력
# ──────────────────────────────────────────────
if st.session_state.analysis_done and st.session_state.results:
    res = st.session_state.results
    analysis = res["analysis"]
    feedback = res["feedback"]

    st.divider()
    st.subheader("② 분석 결과 요약")

    # 주요 지표 메트릭
    col1, col2, col3 = st.columns(3)
    minutes = int(analysis["duration"] // 60)
    seconds = int(analysis["duration"] % 60)
    duration_str = f"{minutes}분 {seconds}초" if minutes > 0 else f"{seconds}초"

    col1.metric("⏱️ 총 발표 시간", duration_str)
    col2.metric("📊 말하기 속도", f"{analysis['wpm']} WPM")
    col3.metric("🔇 침묵 구간", f"{analysis['silent_count']}회")

    # [추가] 종합 점수
    score = feedback["score"]
    if score >= 80:
        badge_cls = "score-high"
        grade = "우수"
    elif score >= 60:
        badge_cls = "score-mid"
        grade = "보통"
    else:
        badge_cls = "score-low"
        grade = "개선 필요"

    st.markdown(
        f'<div class="score-badge {badge_cls}">{score}</div>'
        f'<p style="text-align:center;font-weight:600;margin-top:0;">종합 점수 — {grade}</p>',
        unsafe_allow_html=True,
    )

    # [추가] 활성도 그래프
    energy = analysis.get("energy_frames", [])
    if energy:
        st.subheader("📈 발표 활성도 그래프")
        fig, ax = plt.subplots(figsize=(7, 2.5))
        x = np.arange(len(energy)) * 3  # 3초 단위
        ax.fill_between(x, energy, color="#4361ee", alpha=0.4)
        ax.plot(x, energy, color="#4361ee", linewidth=1.5)
        ax.set_xlabel("시간 (초)", fontsize=10)
        ax.set_ylabel("음성 세기", fontsize=10)
        ax.set_title("구간별 발표 활성도", fontsize=11, fontweight="bold")
        ax.set_ylim(bottom=0)

        # 침묵 위치 표시
        for pos in analysis.get("silent_positions", []):
            ax.axvline(x=pos, color="#ef4444", linestyle="--", alpha=0.6, linewidth=1)

        ax.legend(
            handles=[
                plt.Line2D([0], [0], color="#4361ee", linewidth=2, label="음성 활성도"),
                plt.Line2D([0], [0], color="#ef4444", linestyle="--", linewidth=1, label="침묵 구간"),
            ],
            fontsize=9,
        )
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # [추가] 침묵 위치 상세 안내
    if analysis["silent_positions"]:
        with st.expander("🔇 침묵 구간 상세 위치"):
            for i, pos in enumerate(analysis["silent_positions"], 1):
                m, s = divmod(int(pos), 60)
                label = f"{m}분 {s}초" if m > 0 else f"{s}초"
                st.write(f"  {i}번째 침묵 — {label} 부근")

    # 변환 텍스트
    with st.expander("📝 변환된 텍스트 확인"):
        st.write(res["transcript"])
        st.caption(f"총 {analysis['word_count']}어절")

    # 피드백 카드
    st.subheader("③ 💡 맞춤 피드백")
    for item in feedback["messages"]:
        _, title, detail, level = item
        cls = f"fb-{level}"
        st.markdown(
            f'<div class="fb-card {cls}"><strong>{title}</strong><br>{detail}</div>',
            unsafe_allow_html=True,
        )

    st.success("분석 완료! 피드백을 참고해 다시 연습해보세요. 💪")

    if st.button("🔄 처음부터 다시 하기"):
        st.session_state.analysis_done = False
        st.session_state.results = None
        st.rerun()

# ──────────────────────────────────────────────
# 푸터
# ──────────────────────────────────────────────
st.divider()
st.caption("© 2026 발표 도우미 AI — 학생들의 학습과 성장을 응원합니다.")
