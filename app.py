import streamlit as st
import time
import random
import os
from questions import QUESTIONS

# LLM 모듈 임포트
try:
    from llm_manager import generate_dynamic_question, get_ai_response, transcribe_audio, text_to_speech
    HAS_LLM = True
except ImportError as e:
    HAS_LLM = False
    st.error(f"LLM Module Import Error: {e}")

# 음성 녹음기 라이브러리
try:
    from streamlit_mic_recorder import mic_recorder
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False

# 페이지 기본 설정
st.set_page_config(
    page_title="의대 면접 연습 챗봇 (AI)",
    page_icon="🩺",
    layout="wide"
)

# --- 사이드바: 설정 ---
with st.sidebar:
    st.header("🤖 면접관 설정")
    
    # 0. API 키 설정
    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
        api_key = st.secrets["OPENAI_API_KEY"]
        st.success("✅ API Key가 설정되었습니다.")
    else:
        api_key = st.text_input("OpenAI API Key:", type="password", placeholder="sk-...")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

    # 1. 성격 선택
    personality = st.radio(
        "면접관 성격:",
        ("냉철하고 압박하는 스타일", "친절하고 격려하는 스타일", "논리적이고 사실 중심 스타일"),
        index=0
    )
    
    st.markdown("---")
    
    # 2. 문제 선택
    st.header("📚 기출 문제 / AI 생성")
    
    tab1, tab2 = st.tabs(["기출 문제", "AI 문제 생성"])
    
    # 세션 상태 초기화 함수
    def reset_session(new_question=None):
        st.session_state.messages = []
        st.session_state.intro_done = False # 자기소개 완료 여부
        if new_question:
            st.session_state.current_question = new_question
    
    with tab1:
        question_category = st.selectbox(
            "기출 문제 주제:",
            list(QUESTIONS.keys())
        )
        if st.button("기출 문제로 시작"):
            reset_session(QUESTIONS[question_category])
            st.rerun()
            
    with tab2:
        new_topic = st.text_input("생성할 문제 주제:", placeholder="예: 의료 인공지능, 안락사 등")
        if st.button("새로운 문제 생성 (AI)"):
            if not api_key:
                st.error("API Key를 먼저 입력해주세요.")
            else:
                with st.spinner("AI가 기출 문제를 분석하여 새로운 문제를 출제 중입니다..."):
                    generated_q = generate_dynamic_question(api_key, new_topic)
                    if "error" in generated_q:
                        st.error(f"생성 실패: {generated_q['error']}")
                    else:
                        reset_session(generated_q)
                        st.rerun()

    st.markdown("---")
    if st.button("대화 초기화"):
        reset_session()
        st.rerun()

# --- 메인 화면 ---
st.title("🩺 의대 면접 시뮬레이션")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.intro_done = False
    # 초기: 기출 첫번째
    st.session_state.current_question = QUESTIONS[list(QUESTIONS.keys())[0]]

q_data = st.session_state.current_question

# [1] 제시문 및 문제 영역 (자기소개 전에는 숨길 수도 있지만, 미리 보여주는 게 나을 수 있음)
# 일단 항상 보여줌
with st.expander("📄 제시문 및 문제 보기", expanded=True):
    st.subheader(q_data.get("title", "제목 없음"))
    st.markdown(q_data.get("context", ""))
    st.markdown("---")
    st.markdown("**질문 목록**")
    questions = q_data.get("questions", [])
    if isinstance(questions, list):
        for q in questions:
            st.markdown(f"- {q}")
    else:
        st.write(questions)

# [2] 첫인사 (자기소개 요청)
if not st.session_state.messages:
    welcome_msg = "반갑습니다. 면접을 시작하기에 앞서, 간단하게 자기소개를 부탁드립니다."
    msg_data = {"role": "assistant", "content": welcome_msg}
    
    # TTS 생성 (첫 인사도 음성으로)
    if HAS_LLM and api_key:
        try:
            # 매번 생성하면 느리거나 비용이 드니 세션에 캐싱하면 좋으나,
            # 여기선 간단히 항상 생성 (또는 이미 생성된 걸 확인 가능하면 좋음)
            audio_bytes = text_to_speech(api_key, welcome_msg)
            msg_data["audio"] = audio_bytes
        except Exception:
            pass # API 키 오류 등으로 생성 못해도 텍스트는 보여줌
            
    st.session_state.messages.append(msg_data)

# [3] 대화 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "audio" in message:
            st.audio(message["audio"], format="audio/mp3")

# --- 입력 처리 (텍스트 OR 오디오) ---
# 채팅 입력창 바로 위에 오디오 버튼 배치
st.markdown("### 💬 답변하기")

audio_bytes = None
user_input_content = None

if HAS_AUDIO:
    # mic_recorder는 버튼 형태로 렌더링됨
    c1, c2 = st.columns([2, 8])
    with c1:
        st.write("마이크를 켜고 말씀하세요:")
    with c2:
        # 녹음 버튼
        audio_data = mic_recorder(
            start_prompt="🎤 녹음 시작",
            stop_prompt="⏹️ 말하기 완료 (클릭 시 전송)",
            key='recorder',
            format="wav",
             use_container_width=False
        )
        if audio_data:
            audio_bytes = audio_data['bytes']

# 텍스트 입력 (화면 하단 고정)
prompt = st.chat_input("텍스트로 답변을 입력하세요...")

# 로직: 오디오가 들어오면 STT -> user_input_content에 할당
if HAS_AUDIO and audio_bytes:
    with st.spinner("음성을 텍스트로 변환 중입니다..."):
        if api_key:
            try:
                user_input_content = transcribe_audio(api_key, audio_bytes)
            except Exception as e:
                st.error(f"STT Error: {e}")
        else:
             user_input_content = "[Mock] API Key가 없어서 음성 인식이 불가능합니다."

if prompt:
    user_input_content = prompt

# --- 봇 응답 생성 및 처리 ---
if user_input_content:
    # 1. 사용자 메시지 저장
    st.session_state.messages.append({"role": "user", "content": user_input_content})
    st.chat_message("user").write(user_input_content)
    
    # 2. 봇 응답 로직 결정
    response_content = ""
    response_audio = None
    
    with st.chat_message("assistant"):
        with st.spinner("면접관이 생각 중입니다..."):
            if HAS_LLM and api_key:
                # 시나리오 분기
                if not st.session_state.intro_done:
                    # 자기소개 단계
                    # AI가 자기소개를 받고 -> 메인 문제로 넘어가도록 유도
                    # 간단한 시스템 프롬프트 포장
                    t_msg = [
                        {"role": "system", "content": f"당신은 의대 면접관입니다. 성격: {personality}. 방금 지원자가 자기소개를 했습니다. 이에 대해 짧게 인사를 건네고, 바로 제시된 문제에 대한 본인의 생각을 말해보라고 지시하세요."},
                        {"role": "user", "content": user_input_content}
                    ]
                    # 직접 호출 (get_ai_response는 문제 문맥을 너무 강하게 넣으므로 별도 처리 혹은 get_ai_response 수정)
                    # 여기서는 간단히 직접 호출 구현
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key)
                    completion = client.chat.completions.create(
                        model="gpt-4o",
                        messages=t_msg
                    )
                    response_content = completion.choices[0].message.content
                    st.session_state.intro_done = True
                else:
                    # 메인 질문 단계
                    response_content = get_ai_response(
                        api_key, 
                        st.session_state.messages, 
                        personality, 
                        q_data
                    )
                
                # 2-2. TTS
                try:
                    with st.spinner("면접관이 답변을 말하는 중입니다..."):
                        response_audio = text_to_speech(api_key, response_content)
                except Exception as e:
                    st.error(f"TTS Error: {e}")
            else:
                time.sleep(1)
                response_content = f"[Mock] API Key가 없습니다. ('{user_input_content}' 수신)"
                if not st.session_state.intro_done:
                    st.session_state.intro_done = True
            
            # 텍스트 표시
            st.write(response_content)
            # 오디오 플레이
            if response_audio:
                st.audio(response_audio, format="audio/mp3", autoplay=True)
    
    # 메시지 저장 (오디오 포함)
    msg_data = {"role": "assistant", "content": response_content}
    if response_audio:
        msg_data["audio"] = response_audio
    st.session_state.messages.append(msg_data)
