import os
from pypdf import PdfReader

def extract_questions(filename):
    print(f"--- Processing: {filename} ---")
    try:
        reader = PdfReader(filename)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            # 의예과 면접 관련 키워드가 있는 페이지만 출력 (너무 많으므로)
            if "의예과" in text and "면접" in text:
                print(f"[Page {i+1}]")
                print(text)
                print("-" * 50)
            # 제시문, 문항 등의 키워드도 확인
            elif "제시문" in text and ("가]" in text or "나]" in text):
                 if "의학" in text or "실험" in text or "도표" in text:
                    print(f"[Page {i+1} - Potential Question]")
                    print(text[:500]) # 앞부분만 일단 출력
                    print("-" * 50)

    except Exception as e:
        print(f"Error reading {filename}: {e}")

files = [
    "2024학년도 연세대학교 대학별고사 선행학습 영향평가 결과보고서 별책(기출문제).pdf",
    "2025학년도 연세대학교 대학별고사 선행학습 영향평가 결과보고서(별책).pdf"
]

for f in files:
    if os.path.exists(f):
        extract_questions(f)
    else:
        print(f"File not found: {f}")
