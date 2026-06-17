# 🎤 발표 능력 및 학습 습관 개선 도우미

## 🚀 프로젝트 소개

이 프로젝트는 학생들의 발표 능력과 학습 습관을 개선하기 위해 개발된 웹 기반 도우미 애플리케이션입니다. 사용자의 음성 발표를 녹음하고, OpenAI Whisper를 활용하여 텍스트로 변환한 후, 말하기 속도와 침묵 구간을 분석하여 맞춤형 피드백을 제공합니다. 이를 통해 학생들은 자신의 발표 습관을 객관적으로 파악하고 개선하는 데 도움을 받을 수 있습니다.

## ✨ 주요 기능

- **음성 녹음 및 텍스트 변환 (STT)**: 마이크를 통해 사용자의 음성을 녹음하고, OpenAI Whisper API를 사용하여 높은 정확도로 텍스트로 변환합니다.
- **말하기 속도 분석 (WPM)**: 변환된 텍스트의 단어 수와 발표 시간을 기반으로 분당 단어 수(Words Per Minute, WPM)를 계산하여 말하기 속도를 분석합니다.
- **침묵 구간 감지**: 발표 중 1초 이상 지속되는 침묵 구간의 횟수와 위치를 감지하여 발표의 흐름을 파악합니다.
- **맞춤형 피드백**: 분석된 말하기 속도와 침묵 구간 데이터를 바탕으로 개인화된 개선 피드백을 제공합니다.

## 🛠️ 기술 스택

- **Frontend & Backend**: Streamlit (Python)
- **Speech-to-Text (STT)**: OpenAI Whisper API
- **Audio Processing**: `pydub`, `librosa`
- **Recording**: `streamlit-mic-recorder`

## 📋 설치 및 실행 방법

### 1. 환경 설정

Python 3.8 이상이 설치되어 있어야 합니다.

```bash
# 프로젝트 저장소 클론
git clone https://github.com/YOUR_USERNAME/presentation-helper.git
cd presentation-helper

# 가상 환경 생성 및 활성화 (권장)
python -m venv venv
source venv/bin/activate  # Linux/macOS
venc\Scripts\activate  # Windows

# 필요한 라이브러리 설치
pip install -r requirements.txt
```

### 2. OpenAI API 키 설정

OpenAI Whisper API를 사용하기 위해서는 OpenAI API 키가 필요합니다. `OPENAI_API_KEY` 환경 변수에 API 키를 설정해주세요.

```bash
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"  # Linux/macOS
# 또는
set OPENAI_API_KEY="YOUR_OPENAI_API_KEY"  # Windows (CMD)
# 또는
$env:OPENAI_API_KEY="YOUR_OPENAI_API_KEY"  # Windows (PowerShell)
```

### 3. 애플리케이션 실행

```bash
streamlit run app.py
```

위 명령어를 실행하면 웹 브라우저에 애플리케이션이 자동으로 열립니다.

## ☁️ Streamlit Cloud 배포 (선택 사항)

이 프로젝트는 Streamlit Cloud에 쉽게 배포할 수 있습니다. 다음 단계를 따르세요:

1. 이 저장소를 GitHub에 푸시합니다.
2. [Streamlit Cloud](https://share.streamlit.io/)에 접속하여 로그인합니다.
3. "New app" 버튼을 클릭하고, GitHub 저장소를 연결한 후 `main` 브랜치와 `app.py` 파일을 선택합니다.
4. `OPENAI_API_KEY`를 Streamlit Cloud의 Secrets 설정에 추가합니다.
5. "Deploy!" 버튼을 클릭하여 배포를 시작합니다.

## 💡 개선 및 확장 아이디어

- **정확도 향상**: 음성 인식 시스템의 정확도를 더욱 높여 더 정교한 분석 결과를 제공합니다.
- **추가 분석 기능**: 발표 내용의 키워드 추출, 감정 분석, 발음 정확도 평가 등 다양한 분석 기능을 추가합니다.
- **시각화 강화**: 발표 시간 흐름에 따른 말하기 속도 변화, 침묵 구간 시각화 등 더욱 풍부한 데이터 시각화를 제공합니다.
- **학습 패턴 분석**: 장기적인 학습 데이터를 기록하고 분석하여 개인별 학습 패턴 및 개선점을 제시합니다.
- **유사도 검사**: 작성한 글의 유사도를 확인할 수 있는 기능을 추가하여 독창적인 글쓰기를 돕습니다.

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 🧑‍💻 기여자

- Manus AI
