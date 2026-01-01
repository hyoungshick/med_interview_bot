import streamlit as st
import time
import random
import os
from questions import QUESTIONS

# LLM 모듈 임포트
try:
    # evaluate_interview 임포트 추가
    from llm_manager import generate_dynamic_question, get_ai_response, transcribe_audio, text_to_speech, evaluate_interview
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

# --- 상태 초기화 (사이드바 렌더링 전) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.evaluation = None
    st.session_state.current_question_index = 0
    
    # 초기: 기출 문제 중 무작위 선택
    random_key = random.choice(list(QUESTIONS.keys()))
    st.session_state.current_question = QUESTIONS[random_key]
    
    # 성격 무작위 선택 (0, 1, 2 중 하나)
    st.session_state.personality_index = random.randint(0, 2)

# 안전장치: 기존 세션에 personality_index가 없을 경우 추가
if "personality_index" not in st.session_state:
    st.session_state.personality_index = random.randint(0, 2)

q_data = st.session_state.current_question

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
    personality_map = {
        0: "냉철하고 압박하는 스타일",
        1: "친절하고 격려하는 스타일",
        2: "논리적이고 사실 중심 스타일"
    }

    voice_map = {
        0: "onyx",
        1: "shimmer",
        2: "alloy"
    }
    
    selected_p_index = st.radio(
        "면접관 성격:",
        [0, 1, 2],
        format_func=lambda x: personality_map[x],
        index=st.session_state.personality_index
    )
    
    st.session_state.personality_index = selected_p_index
    personality = personality_map[selected_p_index]
    current_voice = voice_map[selected_p_index]
    
    st.markdown("---")
    
    # 2. 문제 선택
    st.header("📚 기출 문제 / AI 생성")
    
    tab1, tab2 = st.tabs(["기출 문제", "AI 문제 생성"])
    
    # 세션 상태 초기화 함수
    def reset_session(new_question=None):
        st.session_state.messages = []
        st.session_state.evaluation = None # 평가 결과 초기화
        st.session_state.current_question_index = 0
        
        # 성격도 다시 랜덤 (원한다면) - UX상 리셋시 모든게 바뀌는게 자연스러움
        st.session_state.personality_index = random.randint(0, 2)
        
        if new_question:
            st.session_state.current_question = new_question
        else:
             # 기출 문제 중 무작위 재선택
            random_key = random.choice(list(QUESTIONS.keys()))
            st.session_state.current_question = QUESTIONS[random_key]
    
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
    
    # 3. 평가 및 초기화
    if st.button("🏁 면접 종료 및 평가받기"):
        if not st.session_state.messages:
             st.warning("대화 내용이 없습니다.")
        elif not api_key:
             st.error("API Key가 필요합니다.")
        else:
            with st.spinner("면접관이 평가서를 작성하고 있습니다... (약 10초 소요)"):
                # 평가 로직 실행
                eval_result = evaluate_interview(
                    api_key, 
                    st.session_state.messages, 
                    st.session_state.current_question
                )
                st.session_state.evaluation = eval_result
                st.rerun() # 리런해서 메인 화면에 뿌림

    if st.button("🔄 대화 초기화"):
        reset_session()
        st.rerun()

# --- 메인 화면 ---
st.title("🩺 의대 면접 시뮬레이션")

# Evaluation used to be displayed here, now moved to bottom
st.markdown("---")

# [1] 제시문 및 문제 영역 (자기소개 전에는 숨길 수도 있지만, 미리 보여주는 게 나을 수 있음)
# 일단 항상 보여줌
with st.expander("📄 제시문 및 문제 보기", expanded=True):
    st.subheader(q_data.get("title", "제목 없음"))
    st.markdown(q_data.get("context", ""))
    st.markdown("---")
    st.markdown("**질문 목록**")
    questions = q_data.get("questions", [])
    if isinstance(questions, list):
        # 현재 질문 하이라이트
        current_idx = st.session_state.current_question_index
        for idx, q in enumerate(questions):
            if idx == current_idx:
                st.markdown(f"**👉 {q}**")
            else:
                st.markdown(f"- {q}")
    else:
        st.write(questions)

# [2] 첫인사 (첫 번째 질문 제시)
if not st.session_state.messages:
    first_q = q_data['questions'][0]
    welcome_msg = f"반갑습니다. 면접을 시작하겠습니다. 첫 번째 질문입니다.\n\n{first_q}"
    msg_data = {"role": "assistant", "content": welcome_msg}
    
    # TTS 생성 (첫 인사도 음성으로)
    if HAS_LLM and api_key:
        try:
            # 매번 생성하면 느리거나 비용이 드니 세션에 캐싱하면 좋으나,
            # 여기선 간단히 항상 생성 (또는 이미 생성된 걸 확인 가능하면 좋음)
            audio_bytes = text_to_speech(api_key, welcome_msg, voice=current_voice)
            msg_data["audio"] = audio_bytes
        except Exception:
            pass # API 키 오류 등으로 생성 못해도 텍스트는 보여줌
            
    st.session_state.messages.append(msg_data)

# Sidebar nav removed

# [3] 대화 표시
# [3] 대화 표시
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "audio" in message:
            # 가장 최근 메시지만 자동 재생 (autoplay=True)
            is_last = (idx == len(st.session_state.messages) - 1)
            st.audio(message["audio"], format="audio/mp3", autoplay=is_last)

# --- 입력 처리 (텍스트 OR 오디오) ---
# 평가가 완료되었으면 입력창을 숨김 (면접 종료)
# 평가가 완료되었으면 입력창을 숨김 (면접 종료)
# Dynamic Container for Input Area

# Dynamic Container for Input Area or Next Button
input_container = st.empty()

if not st.session_state.get("evaluation"):
    # Determine state: Can we move to next question?
    # Logic: If last message is assistant (ack) and we are not at end, show Next Button.
    # Otherwise, show Input.
    
    current_idx = st.session_state.current_question_index
    total_q = len(q_data['questions'])
    
    show_next_button = False
    
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
         # Only show if the PREVIOUS message was from user (meaning this assistant message is a response/ack)
         # Start of interview: [Assistant(Welcome)] -> Len 1. [-2] Index Error.
         if len(st.session_state.messages) > 1 and st.session_state.messages[-2]["role"] == "user":
             if current_idx < total_q - 1:
                 show_next_button = True
    
    with input_container.container():
        # Initialize variables to avoid NameError
        audio_bytes = None
        user_input_content = None

        if show_next_button:
            # [CASE 1] Auto-Advance to Next Question (No Button)
            st.info("⏳ 답변이 완료되었습니다. 잠시 후 다음 질문으로 넘어갑니다...")
            
            # Give user time to read/hear the acknowledgement
            time.sleep(3)
            
            st.session_state.current_question_index += 1
            next_q = q_data['questions'][st.session_state.current_question_index]
            
            # 다음 질문 메시지 생성
            next_msg_text = f"다음 질문 드리겠습니다.\n\n{next_q}"
            msg_data = {"role": "assistant", "content": next_msg_text}
            
            if HAS_LLM and api_key:
                try:
                    audio_bytes = text_to_speech(api_key, next_msg_text, voice=current_voice)
                    msg_data["audio"] = audio_bytes
                except Exception:
                    pass
            
            st.session_state.messages.append(msg_data)
            st.rerun()
        
        else:
            # [CASE 2] Show Input Controls (Audio/Text)
            # 채팅 입력창 바로 위에 오디오 버튼 배치
            st.markdown("### 💬 답변하기")
            
            # audio_bytes = None # Removed redundancy
            # user_input_content = None # Removed redundancy

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
else:
    # 면접 종료 시 안내 (Evaluation block will show result below)
    # Clear the input container just in case
    input_container.empty()
    st.info("✅ 면접이 종료되었습니다. 아래 평가 결과를 확인해주세요.")
    
    audio_bytes = None
    prompt = None
    user_input_content = None

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
# user_input_content가 있을 때만 실행 (평가 완료 시에는 prompt/audio가 None이므로 실행 안 됨)
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
                # 마지막 질문 여부 확인
                is_last = (st.session_state.current_question_index == len(q_data.get('questions', [])) - 1)
                
                # 시나리오 분기
                response_content = get_ai_response(
                    api_key, 
                    st.session_state.messages, 
                    personality, 
                    q_data,
                    is_last_question=is_last
                )
                
                # 2-2. TTS
                try:
                    with st.spinner("면접관이 답변을 말하는 중입니다..."):
                        response_audio = text_to_speech(api_key, response_content, voice=current_voice)
                except Exception as e:
                    st.error(f"TTS Error: {e}")
            else:
                time.sleep(1)
                response_content = f"[Mock] API Key가 없습니다. ('{user_input_content}' 수신)"
            
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
    
    # Force UI update to show "Next Question" button if applicable
    # If not the last question, rerun to update the input container state (Input -> Next Button)
    if current_idx < len(q_data.get('questions', [])) - 1:
         st.rerun()

    # [Auto-Evaluation] 마지막 질문에 대한 답변까지 완료되었는지 확인
    total_q = len(q_data.get('questions', []))
    current_idx = st.session_state.current_question_index
    
    # 지금 Index가 마지막 질문이고, 방금 봇이 다소곳이(ack) 대답했으므로 인터뷰 종료로 간주
    if current_idx == total_q - 1:
        # 자동 평가 실행
        if HAS_LLM and api_key:
            with st.spinner("모든 질문이 완료되었습니다. 면접관이 평가서를 작성 중입니다... (약 10초 소요)"):
                try:
                    eval_result = evaluate_interview(
                        api_key, 
                        st.session_state.messages, 
                        st.session_state.current_question
                    )
                    st.session_state.evaluation = eval_result
                    
                    # Force clear the input area immediately so user can't input more
                    input_container.empty() 
                    
                    # DO NOT rerun here to allow audio to finish playing
                    # st.rerun()
                except Exception as e:
                    st.error(f"Evaluation Error: {e}")

# --- 평가 결과 표시 (대화 아래로 이동) ---
if st.session_state.get("evaluation"):
    st.markdown("---")
    st.info("📊 면접 평가 결과가 도착했습니다!")
    with st.container(border=True):
        st.markdown(st.session_state.evaluation)
    # 닫기 버튼은 굳이 필요 없을 수도 있지만, 재시험 등을 위해 남겨둘 수 있음.
    # 하지만 아래에 배치되므로 '닫기'보다는 그냥 보여주는 게 나음.
