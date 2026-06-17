import librosa
import numpy as np
from openai import OpenAI
import os

# OpenAI 클라이언트 초기화 (환경 변수 사용)
client = OpenAI()

def transcribe_audio(audio_path):
    """OpenAI Whisper를 사용하여 음성을 텍스트로 변환"""
    try:
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        return f"Error: {str(e)}"

def analyze_presentation(audio_path, text):
    """음성 데이터 분석: 말하기 속도, 침묵 구간 감지"""
    # 오디오 로드
    y, sr = librosa.load(audio_path)
    duration = librosa.get_duration(y=y, sr=sr)
    
    # 단어 수 계산 (공백 기준)
    word_count = len(text.split())
    # 분당 단어 수 (WPM)
    wpm = (word_count / duration) * 60 if duration > 0 else 0
    
    # 비침묵 구간 감지 (top_db=30: 30dB 이하를 침묵으로 간주)
    intervals = librosa.effects.split(y, top_db=30)
    
    # 침묵 구간 계산 (구간 사이의 간격이 1초 이상인 경우)
    silent_count = 0
    last_end = 0
    silent_positions = []
    
    for start, end in intervals:
        # 이전 구간 끝과 현재 구간 시작 사이의 시간 차이
        gap = (start - last_end) / sr
        if gap >= 1.0:
            silent_count += 1
            silent_positions.append(last_end / sr)
        last_end = end
    
    # 마지막 비침묵 구간 이후부터 파일 끝까지의 침묵 체크
    if (len(y) - last_end) / sr >= 1.0:
        silent_count += 1
        silent_positions.append(last_end / sr)

    return {
        "duration": duration,
        "word_count": word_count,
        "wpm": round(wpm, 1),
        "silent_count": silent_count,
        "silent_positions": [round(p, 1) for p in silent_positions]
    }

def get_feedback(analysis):
    """분석 결과에 따른 피드백 생성"""
    wpm = analysis['wpm']
    silent_count = analysis['silent_count']
    
    feedback = []
    
    # 속도 피드백 (한국어 기준 일반적인 발표 속도 100-140 WPM 가정)
    if wpm > 160:
        feedback.append("🚀 **말하기 속도가 빠릅니다.** 조금 더 천천히 말하면 청중이 내용을 이해하기 훨씬 쉬워집니다.")
    elif wpm < 80:
        feedback.append("🐢 **말하기 속도가 조금 느립니다.** 조금 더 활기찬 속도로 발표를 진행해보세요.")
    else:
        feedback.append("✅ **적절한 말하기 속도입니다.** 지금처럼 안정적인 속도를 유지하세요.")
        
    # 침묵 피드백
    if silent_count > 5:
        feedback.append(f"⚠️ **침묵 구간이 {silent_count}회 발견되었습니다.** 불필요한 멈춤이 없는지 확인하고 연습해보세요.")
    else:
        feedback.append("✨ **침묵 구간이 적절합니다.** 발표의 흐름이 매우 매끄럽습니다.")
        
    return feedback
