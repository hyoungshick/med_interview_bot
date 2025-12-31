# 의대 면접 연습 챗봇 (Medical Interview Bot)

Streamlit으로 제작된 간단한 의대 면접 연습용 챗봇 프로토타입입니다.

## 기능
- **사이드바 설정**: 면접관의 성격(압박형, 친절형, 논리형)을 선택할 수 있습니다.
- **채팅 인터페이스**: 실제 채팅처럼 대화 기록이 남으며 연습할 수 있습니다.
- **대화 초기화**: 언제든 대화를 처음부터 다시 시작할 수 있습니다.

## 설치 및 실행 방법

1. **가상환경 생성 (권장)**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Mac/Linux
   # source venv/bin/activate
   ```

2. **라이브러리 설치**
   ```bash
   pip install -r requirements.txt
   ```

3. **앱 실행**
   ```bash
   streamlit run app.py
   ```

## 실행 결과
브라우저가 자동으로 열리며 `http://localhost:8501` 주소로 접속됩니다.
