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

def get_ai_response(api_key, messages, personality, question_data):
    client = openai.OpenAI(api_key=api_key)
    
    system_prompt = f"""
    당신은 의대 면접관입니다. 성격은 '{personality}'입니다.
    
    [현재 면접 문제]
    {question_data.get('context', '')}
    {question_data.get('questions', '')}
    
    [지시사항]
    1. 사용자의 답변을 듣고, 논리적 허점이나 추가 설명이 필요한 부분을 파고드세요 (꼬리 질문).
    2. 절대 정답을 먼저 말해주지 마세요.
    3. 한 번에 하나의 질문만 하세요.
    4. 실제 면접처럼 대화하듯 짧게(~3문장) 반응하세요.
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
