import librosa
import numpy as np
from openai import OpenAI
import streamlit as st
import os
import io
import wave
import struct

# ──────────────────────────────────────────────
# [버그수정 1] st.secrets.get() → KeyError 방지
#   원본: st.secrets.get("OPENAI_API_KEY") 는
#         secrets 자체가 없으면 AttributeError 발생
# ──────────────────────────────────────────────
def get_client():
    """Streamlit Secrets 또는 환경 변수에서 API 키를 가져와 OpenAI 클라이언트 생성"""
    api_key = None
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass

    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        st.error("❌ OpenAI API 키가 설정되지 않았습니다.\n\n"
                 "로컬 실행 시 환경 변수 `OPENAI_API_KEY`를 설정하거나,\n"
                 "Streamlit Cloud → Settings → Secrets에 등록해주세요.")
        st.stop()

    return OpenAI(api_key=api_key)


# ──────────────────────────────────────────────
# [버그수정 2] transcribe_audio 에러 반환값 문제
#   원본: except 에서 "Error: ..." 문자열 반환 →
#         이후 analyze_presentation 에서 text.split() 시
#         'Error: ...' 가 단어로 카운트돼 WPM 오류
#   수정: Exception 을 다시 raise 해서 app.py 의
#         try/except 블록이 잡도록 함
# ──────────────────────────────────────────────
def transcribe_audio(audio_path: str) -> str:
    """OpenAI Whisper API로 음성 → 텍스트 변환"""
    client = get_client()
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="ko",          # [추가] 한국어 명시 → 인식 정확도 향상
        )
    return transcript.text


# ──────────────────────────────────────────────
# [버그수정 3] analyze_presentation 끝 침묵 감지 오류
#   원본: len(y) - last_end 로 계산하나,
#         intervals 가 비어있을 경우 last_end=0 이어서
#         전체 길이가 침묵으로 잘못 카운트됨
#   수정: intervals 가 비어있을 때 별도 처리 추가
#
# [추가 기능] 구간별 속도 변화 분석 (시각화용)
# ──────────────────────────────────────────────
def analyze_presentation(audio_path: str, text: str) -> dict:
    """음성 분석: WPM, 침묵 구간, 구간별 에너지(시각화용)"""
    y, sr = librosa.load(audio_path, sr=None)   # [수정] sr=None → 원본 샘플레이트 유지
    duration = librosa.get_duration(y=y, sr=sr)

    # 한국어는 어절 기준 단어 수 계산
    words = [w for w in text.split() if w.strip()]
    word_count = len(words)
    wpm = round((word_count / duration) * 60, 1) if duration > 0 else 0

    # 침묵 구간 감지
    silent_count = 0
    silent_positions = []

    if len(y) == 0 or duration == 0:
        intervals = np.array([]).reshape(0, 2)
    else:
        intervals = librosa.effects.split(y, top_db=30)

    if len(intervals) == 0:
        # 전체가 침묵인 경우
        silent_count = 1
        silent_positions = [0.0]
    else:
        last_end = 0
        for start, end in intervals:
            gap = (start - last_end) / sr
            if gap >= 1.0:
                silent_count += 1
                silent_positions.append(round(last_end / sr, 1))
            last_end = end

        # 마지막 음성 이후 끝까지 침묵 체크
        trailing_silence = (len(y) - last_end) / sr
        if trailing_silence >= 1.0:
            silent_count += 1
            silent_positions.append(round(last_end / sr, 1))

    # [추가] 구간별(3초 윈도우) RMS 에너지 → 말하기 활성도 그래프용
    hop_length = sr * 3  # 3초 단위
    energy_frames = []
    for i in range(0, len(y), hop_length):
        chunk = y[i:i + hop_length]
        rms = float(np.sqrt(np.mean(chunk ** 2))) if len(chunk) > 0 else 0.0
        energy_frames.append(round(rms, 4))

    return {
        "duration": duration,
        "word_count": word_count,
        "wpm": wpm,
        "silent_count": silent_count,
        "silent_positions": silent_positions,
        "energy_frames": energy_frames,   # 추가됨
    }


# ──────────────────────────────────────────────
# [업그레이드] get_feedback
#   원본: WPM / 침묵 두 가지 조건만 체크
#   추가: ① 발표 길이 피드백
#         ② 단어 수 피드백
#         ③ 침묵 위치 힌트
#         ④ 종합 점수(100점 만점)
# ──────────────────────────────────────────────
def get_feedback(analysis: dict) -> dict:
    """분석 결과 → 항목별 피드백 + 종합 점수"""
    wpm = analysis["wpm"]
    silent_count = analysis["silent_count"]
    duration = analysis["duration"]
    word_count = analysis["word_count"]
    silent_positions = analysis.get("silent_positions", [])

    messages = []
    score = 100

    # ① WPM 피드백
    if wpm > 180:
        messages.append(("speed", "🚀 말하기 속도가 너무 빠릅니다.", "분당 180단어 이하로 천천히 말해보세요.", "danger"))
        score -= 20
    elif wpm > 160:
        messages.append(("speed", "⚡ 말하기 속도가 약간 빠릅니다.", "조금만 더 여유 있게 발표해보세요.", "warning"))
        score -= 10
    elif wpm < 60:
        messages.append(("speed", "🐢 말하기 속도가 너무 느립니다.", "분당 80단어 이상으로 활기차게 말해보세요.", "danger"))
        score -= 20
    elif wpm < 80:
        messages.append(("speed", "🔵 말하기 속도가 약간 느립니다.", "조금 더 자신감 있게 말해보세요.", "warning"))
        score -= 10
    else:
        messages.append(("speed", "✅ 말하기 속도가 적절합니다!", f"{wpm} WPM — 딱 좋은 속도예요.", "success"))

    # ② 침묵 피드백
    if silent_count > 7:
        messages.append(("silence", f"⚠️ 침묵 구간이 {silent_count}회로 많습니다.",
                         "발표 흐름이 자주 끊기고 있어요. 전환 표현을 준비해보세요.", "danger"))
        score -= 20
    elif silent_count > 4:
        messages.append(("silence", f"🔇 침묵 구간이 {silent_count}회 있습니다.",
                         "일부 구간에서 흐름이 끊겼어요. 연결 표현을 활용해보세요.", "warning"))
        score -= 10
    else:
        messages.append(("silence", "✨ 발표 흐름이 매끄럽습니다!", f"침묵 구간 {silent_count}회 — 잘 이어가고 있어요.", "success"))

    # ③ 발표 시간 피드백
    if duration < 30:
        messages.append(("duration", "⏱️ 발표 시간이 짧습니다.",
                         "30초 이상 발표해야 평가가 더 정확합니다.", "warning"))
        score -= 10
    elif duration > 300:
        messages.append(("duration", "⏰ 발표 시간이 깁니다.",
                         "핵심 내용만 선별해 3분 이내로 압축해보세요.", "warning"))
        score -= 5
    else:
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        label = f"{minutes}분 {seconds}초" if minutes > 0 else f"{seconds}초"
        messages.append(("duration", f"⏱️ 발표 시간 {label}", "적절한 발표 길이예요.", "success"))

    score = max(0, score)
    return {"messages": messages, "score": score}
