import openai
import os
from questions import QUESTIONS

# [공통] 문제 생성 시스템 프롬프트 (기본 설정)
BASE_SYSTEM_PROMPT = """
당신은 대한민국 최상위권 의과대학(연세대, 서울대 등)의 입시 면접 문제 출제 위원입니다.
지원자의 '비판적 사고력', '논리적 추론 능력', '심층적 분석력'을 평가하기 위한 **최고 난이도의 면접 문제**를 출제합니다.

**[핵심 원칙: 추론형 문제 (Inferential Logic)]**
- **정답을 제시문에 직접 쓰지 마십시오.**
- 대신, 정답을 유추할 수 있는 **'현상', '실험 데이터', '사례', '관련 이론의 파편'**들만 제시하십시오.
- 지원자가 이 파편들을 조합하고 논리적으로 연결해야만 답안을 구성할 수 있어야 합니다.
- 제시문은 설명문이 아니라 **Raw Data(날것의 자료)**에 가까워야 합니다.

**[출제 지침]**
1. **Context(제시문) 구성**:
   - 분량: 최소 **1000자 이상**.
   - 구조: [가], [나], [다] 등 3개 이상의 단락으로 구성하며, 각 단락은 서로 다른 관점이나 데이터를 제공해야 합니다.
   - 단락 간 줄바꿈(2번) 필수.

2. **출력 형식**:
   - 파싱을 위해 구분자('---') 또는 헤더(TITLE:, CONTEXT: 등)를 명확히 사용.

출력 포맷:
TITLE: [고난도] 제목
CONTEXT: 
### [제시문 가]
(상세 내용...)

### [제시문 나]
(상세 내용...)

### [제시문 다]
(상세 내용...)

QUESTION_LIST:
- [질문 1]
- [질문 2]

KEY_POINTS:
- [평가 포인트 1]
- [평가 포인트 2]
"""

# [Mode 1] 인성/시사/윤리 (Part 1 style)
GEN_SYSTEM_PROMPT_ETHICS = BASE_SYSTEM_PROMPT + """
**[Mode: 인성 및 가치관 (Ethics & Values)]**
- **주제**: 의료 윤리, 사회적 딜레마, 의사소통 갈등, 의료 정책.
- **작성 요령**:
  - 명확한 선악이 없는 복잡한 딜레마 상황을 부여하세요.
  - 한 쪽의 입장만 옹호하기 어려운, 양립 불가능한 가치들이 충돌하게 만드세요.
  - 예: "환자의 자율성 vs 의사의 선의의 간섭주의", "공리주의적 자원 배분 vs 소수자 보호"
"""

# [Mode 2] 과학적 사고력 (Part 2 style)
GEN_SYSTEM_PROMPT_SCIENCE = BASE_SYSTEM_PROMPT + """
**[Mode: 과학적 사고력 (Scientific Reasoning)]**
- **주제**: 생명과학(Biology), 화학(Chemistry), 물리(Physics) 원리의 의학적 응용.
- **작성 요령**:
  - **반드시 실험 결과, 연구 데이터, 그래프 해석(텍스트 묘사)을 포함하세요.**
  - 현상을 설명하는 과학적 원리(예: 효소 반응 속도, 유체 역학, 압력 차이)를 직접 설명하지 말고, **실험 조건과 결과만** 제시하세요.
  - 지원자가 제시된 결과를 보고 원리를 '역추적'하거나, 새로운 상황에 '적용'하는 질문을 던지세요.
  - 예: "약물 A 투여 시 그래프 변화가 [가]와 같다. 제시문 [나]의 세포 기작을 바탕으로 그 원인을 추론하시오."
"""

def generate_dynamic_question(api_key, topic, mode="ethics"):
    client = openai.OpenAI(api_key=api_key)
    
    # 모드에 따른 프롬프트 선택
    if mode == "science":
        system_prompt = GEN_SYSTEM_PROMPT_SCIENCE
        prompt_instruction = f"""
        주제 '{topic}'에 대해 **과학적 추론 능력**을 평가하는 문제를 출제하세요.
        생명과학/화학/물리 지식을 기반으로 한 **실험 데이터나 도표 해석(텍스트로 묘사)**을 반드시 제시문에 포함하세요.
        """
    else:
        system_prompt = GEN_SYSTEM_PROMPT_ETHICS
        prompt_instruction = f"""
        주제 '{topic}'에 대해 **윤리적 딜레마/가치관**을 평가하는 심층면접 문제를 출제하세요.
        상반된 입장의 근거들을 제시문 [가], [나], [다]에 분산 배치하세요.
        """
    
    # 예시 데이터 가져오기 (Few-shot)
    example_key = list(QUESTIONS.keys())[0] 
    example = QUESTIONS[example_key]
    
    prompt = f"""
    [참고할 기출 문제 스타일]
    제목: {example['title']}
    내용: {example['context']} 
    질문: {example['questions']}
    
    위 예시와 같이 **호흡이 길고 깊이 있는** 문제를 출제하세요.
    
    [요청 사항]
    {prompt_instruction}
    
    **중요: '답'을 직접 알려주지 말고, '단서'만 제시하세요. 지원자가 스스로 연결해야 합니다.**
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7 
        )
        content = response.choices[0].message.content
        return parse_generated_content(content)
    except Exception as e:
        return {"error": str(e)}

def parse_generated_content(text):
    data = {"title": "AI 생성 문제", "context": "", "questions": [], "key_points": []}
    try:
        lines = text.split("\n")
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("TITLE:"):
                data["title"] = line.replace("TITLE:", "").strip()
                current_section = None
            elif line.startswith("CONTEXT:"):
                current_section = "context"
                content = line.replace("CONTEXT:", "").strip()
                if content: data["context"] = content
            elif line.startswith("QUESTION_LIST:") or line.startswith("QUESTION:"):
                current_section = "questions"
            elif line.startswith("KEY_POINTS:"):
                current_section = "keypoints"
            else:
                if current_section == "context":
                    data["context"] += "\n" + line
                elif current_section == "questions":
                    # 불릿 포인트나 번호 제거 후 저장
                    clean_line = line.lstrip("-").lstrip("*").lstrip("0123456789.")
                    data["questions"].append(clean_line.strip())
                elif current_section == "keypoints":
                     data["key_points"].append(line.replace("-", "").strip())
        
        # 후처리: Context 줄바꿈 정리
        data["context"] = data["context"].strip()
        
        return data
    except Exception as e:
        return {"title": "파싱 에러", "context": text, "questions": ["질문 생성 중 오류가 발생했습니다."], "key_points": [], "error": str(e)}

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

def text_to_speech(api_key, text, voice="onyx"):
    client = openai.OpenAI(api_key=api_key)
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
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
    - **총점 (Total Score)**: ?/100
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
    - **총점 (Total Score)**: ?/100
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
       
       
    3. **종합 총평 및 고득점을 위한 조언 (Punchline Advice)**
       - 강점과 약점 분석
       - **[고득점 전략 Punchline 예제]**: "이 질문에 대한 답변에 반드시 포함되었으면 좋았을 결정적 한 문장(Golden Sentence)"을 예시로 작성해주세요. 추상적인 조언 대신 **구체적인 멘트**를 적어주세요. (예: "제시문 [가]의 입장에서 볼 때, 중입자 치료의 정밀성은 환자의 삶의 질을 높이는 핵심적인 윤리적 가치라고 생각합니다.")
       
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

