import openai
import os
from questions import QUESTIONS

# 문제 생성 프롬프트
GEN_SYSTEM_PROMPT = """
당신은 의대 입시 면접 문제 출제 위원입니다.
제공된 예시 문제(problem.md 스타일)와 유사한 수준, 형식의 '새로운 면접 문제'를 하나 출제해야 합니다.
형식은 JSON처럼 파싱하기 쉽게 '---' 로 구분하여 [제목/상황], [제시문], [질문] 순서로 출력하세요.
주제는 {topic} 관련이어야 합니다.
난이도는 고등학생 수준에서 논리적 사고력과 윤리적 판단력을 요하는 수준이어야 합니다.
"""

def generate_dynamic_question(api_key, topic):
    client = openai.OpenAI(api_key=api_key)
    
    # 예시 데이터 가져오기 (Few-shot)
    example_key = list(QUESTIONS.keys())[0] 
    example = QUESTIONS[example_key]
    
    prompt = f"""
    [예시 문제 스타일]
    제목: {example['title']}
    내용: {example['context'][:500]}... (생략)
    질문: {example['questions']}
    
    위 스타일을 참고하여, '{topic}'에 관한 새로운 문제를 만들어주세요.
    출력 형식:
    TITLE: [제목]
    CONTEXT: [제시문 내용 (300자 이상)]
    QUESTION: [질문 내용]
    KEY_POINTS: [평가 핵심 포인트 (3가지)]
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # 또는 gpt-3.5-turbo
            messages=[
                {"role": "system", "content": GEN_SYSTEM_PROMPT.format(topic=topic)},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content
        return parse_generated_content(content)
    except Exception as e:
        return {"error": str(e)}

def parse_generated_content(text):
    # 간단한 파싱 로직 (실제로는 더 견고해야 함)
    data = {"title": "AI 생성 문제", "context": "", "questions": [], "key_points": []}
    try:
        lines = text.split("\n")
        current_section = None
        for line in lines:
            if "TITLE:" in line:
                data["title"] = line.replace("TITLE:", "").strip()
            elif "CONTEXT:" in line:
                current_section = "context"
                data["context"] = line.replace("CONTEXT:", "").strip()
            elif "QUESTION:" in line:
                current_section = "question"
                data["questions"].append(line.replace("QUESTION:", "").strip())
            elif "KEY_POINTS:" in line:
                current_section = "keypoints"
                data["key_points"].append(line.replace("KEY_POINTS:", "").strip())
            else:
                if current_section == "context":
                    data["context"] += "\n" + line
                elif current_section == "question" and line.strip():
                    data["questions"].append(line.strip())
                elif current_section == "keypoints" and line.strip():
                    data["key_points"].append(line.strip())
        
        return data
    except:
        return {"title": "파싱 에러", "context": text, "questions": ["내용을 확인해주세요."], "key_points": []}

def get_ai_response(api_key, messages, personality, question_data, is_last_question=False):
    client = openai.OpenAI(api_key=api_key)
    
    # 마지막 질문 여부에 따른 지시사항 분기
    if is_last_question:
        instruction_text = """
        1. 이것이 **마지막 질문**이었습니다.
        2. 답변에 대해 "잘 들었습니다"라고 짧게 인사하고, "면접이 모두 종료되었습니다."라고 마무리하세요.
        3. 절대 "다음 질문을 드리겠습니다"라고 말하지 마세요.
        4. "잠시 후 평가 결과가 제공됩니다"라고 안내하세요.
        """
    else:
        instruction_text = """
        1. 사용자의 답변에 대해 **절대 꼬리 질문이나 추가 질문을 하지 마세요.**
        2. 답변 내용을 간단히 확인하고 격려하는 말만 짧게 건네세요. (예: "잘 들었습니다.", "답변 감사합니다.")
        3. 더 이상 아무 말도 하지 말고 기다리세요. 사용자가 알아서 넘어갑니다.
        """

    system_prompt = f"""
    당신은 의대 면접관입니다. 성격은 '{personality}'입니다.
    
    [현재 면접 문제]
    {question_data.get('context', '')}
    {question_data.get('questions', '')}
    
    [지시사항]
    {instruction_text}
    """
    
    # 메시지 포맷 변환 (streamlit history -> openai messages)
    gpt_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        gpt_messages.append({"role": msg["role"], "content": msg["content"]})
        
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=gpt_messages
    )
    return response.choices[0].message.content

def transcribe_audio(api_key, audio_bytes):
    client = openai.OpenAI(api_key=api_key)
    # 메모리 상의 오디오 데이터를 임시 파일로 저장하거나 바로 전송해야 함.
    # streamlit-audiorecorder는 bytes를 반환함.
    # API는 파일 객체를 원하므로, io.BytesIO와 name 속성을 사용.
    import io
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "input.wav"
    
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="ko"
    )
    return transcript.text

def text_to_speech(api_key, text):
    client = openai.OpenAI(api_key=api_key)
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx", # calm and professional male voice. funny options: alloy, echo, fable, onyx, nova, shimmer
        input=text
    )
    # 스트림 대신 바로 바이트로 반환
    return response.content

def evaluate_interview(api_key, messages, question_data):
    client = openai.OpenAI(api_key=api_key)
    
    # 메시지 정제 (오디오 데이터 제외하고 텍스트만 추출)
    # messages가 [{'role': 'user', 'content': '...', 'audio': b'...'}, ...] 형태일 수 있음.
    filtered_messages = []
    for msg in messages:
        filtered_messages.append(f"{msg['role']}: {msg['content']}")
    
    conversation_text = "\n".join(filtered_messages)

    # 평가 프롬프트
    questions_text = "\n".join(question_data.get('questions', []))
    
    
    # 문제 유형에 따른 평가 항목 및 기준 설정
    title = question_data.get('title', '')
    is_science_question = "Part 2" in title or "과학" in title
    
    if is_science_question:
        criteria_text = """
    [평가 기준 (과학적 사고력/지식 면접)]
    이 문제는 학생의 생명과학/화학/물리 지식과 그 응용력을 평가하는 것입니다. 억지로 윤리적 가치관을 끼워 맞추지 말고, 과학적 원리의 이해도와 논리적 추론 과정을 중점적으로 평가하세요.
    
    1. **과학적 지식 및 이해도 (Scientific Knowledge)** (30점)
       - 제시문의 핵심 개념(예: DNA, 현미경 원리 등)을 정확히 파악하고 있는가?
       
    2. **논리적 추론 및 분석 (Logical Reasoning)** (30점)
       - 주어진 조건에서 타당한 결론을 도출하는가? (수리적/과학적 근거)
       
    3. **응용력 및 통합적 사고 (Application & Synthesis)** (20점)
       - 지식을 새로운 상황(의료 현장, 실험 해석)에 적절히 적용하는가?
       
    4. **의사소통능력 (Communication)** (20점)
       - 복잡한 과학적 개념을 명확하고 알기 쉽게 설명하는가?
    """
        score_fields = """
    - 과학적 지식 및 이해도: ?/30
    - 논리적 추론 및 분석: ?/30
    - 응용력 및 통합적 사고: ?/20
    - 의사소통능력: ?/20
    """
    else:
        criteria_text = """
    [평가 기준 (인성/윤리/딜레마 면접)]
    이 문제는 학생의 가치관, 윤리적 판단력, 소통 능력을 평가하는 것입니다. 정답이 없는 문제이므로 논리의 일관성과 태도가 중요합니다.
    
    1. **윤리 및 가치관 (Ethics & Values)** (30점)
       - 의료 윤리 원칙(생명 존중, 정의 등)을 이해하고 인간 존중의 태도를 보이는가?
       
    2. **논리적 사고력 (Logical Thinking)** (30점)
       - 자신의 주장을 뒷받침하는 근거가 타당하고 일관적인가?
       
    3. **의사소통능력 (Communication)** (20점)
       - 용어가 적절하고 전달력이 좋은가?
       
    4. **상황 대처 및 유연성 (Responsiveness)** (20점)
       - 반론이나 딜레마 상황에서 균형 잡힌 시각을 보여주는가?
    """
        score_fields = """
    - 윤리 및 가치관: ?/30
    - 논리적 사고력: ?/30
    - 의사소통능력: ?/20
    - 상황 대처 및 유연성: ?/20
    """

    prompt = f"""
    당신은 의대 면접 평가관입니다.
    지원자와 면접관의 대화 내용을 바탕으로 지원자를 평가해주세요.
    
    [문제 정보]
    제목: {question_data.get('title')}
    제시문: {question_data.get('context')}
    질문 목록:
    {questions_text}
    
    핵심 평가 요소(Key Points - 참고용): {question_data.get('key_points')}
    
    [대화 내용]
    {conversation_text}
    
    {criteria_text}
    
    ***중요: 평가를 매우 냉정하게 하세요.***
    - 답변이 비어있거나, 질문과 무관하거나, 내용이 거의 없는 경우(예: ".", "모르겠습니다") 해당 항목에 **0점**을 부여하세요.
    - 단순히 참여했다고해서 기본 점수를 주지 마세요.
    - 과학적 사고력 문제에서 윤리적 잣대(예: 환자 공감)를 무리하게 적용하지 마세요.
    
    [평가 양식]
    1. **질문별 상세 분석**
       - 질문 1: [핵심 내용 요약 및 분석]
       - 질문 2: [핵심 내용 요약 및 분석]
       
    2. **항목별 점수 (100점 만점 환산)**
    {score_fields}
       
    3. **종합 총평 및 고득점을 위한 조언**
       - 단순히 정답을 맞추는 것이 아니라, 차별화된 고득점 포인트(통찰력, 연결성 등)를 중심으로 조언해주세요.
       
    4. **최종 합격 여부 (Pass/Fail)**
       - 판단: [Pass / Fail / Borderline]
       - 이유: 한 줄 요약
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a professional grader."}, 
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"평가 생성 중 오류가 발생했습니다: {str(e)}"

