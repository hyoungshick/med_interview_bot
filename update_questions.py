
import re
import os

def parse_markdown(file_path):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return {}
        
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    questions_db = {}
    
    current_year = ""
    current_part = ""
    current_problem_title = ""
    current_context = []
    current_questions = []
    
    # Regex patterns
    year_pattern = re.compile(r'^##\s+(.*)')
    part_pattern = re.compile(r'^###\s+(.*)')
    
    # Check for question line: * **질문 1**: or * **질문**:
    question_line_pattern = re.compile(r'^\*\s+\*\*질문(?:.*?)\*\*:\s*(.*)')

    def save_current_problem():
        nonlocal current_problem_title, current_context, current_questions
        if current_problem_title:
            # Create a unique key
            # Example: 2025 Part 1 - 문제 1 감염병...
            # Simplify Part string
            part_str = current_part.split(":")[0].replace("[", "").replace("]", "").strip()
            if not part_str: part_str = "General"
            
            # Clean title
            title_clean = current_problem_title.replace("**", "").strip()
            # Extract number from title if possible like [문제 1]
            # stored title usually is "[문제 1] Title"
            
            key = f"{current_year} {part_str} - {title_clean}"
            
            # context cleanup: remove > and spaces
            cleaned_context = []
            for line in current_context:
                if line.strip().startswith(">"):
                    cleaned_context.append(line.strip().lstrip("> ").strip())
                elif line.strip():
                    cleaned_context.append(line.strip())
            
            questions_db[key] = {
                "title": f"{current_year} {current_part} - {title_clean}",
                "context": "\n".join(cleaned_context).strip(),
                "questions": list(current_questions),
                "key_points": [
                    "문제의 핵심 쟁점 파악 능력",
                    "논리적 사고 및 근거 제시 능력",
                    "윤리적 판단 및 가치관의 일관성",
                    "의사소통 능력 및 태도"
                ] 
            }

    for line in lines:
        line_stripped = line.strip()
        
        # Check Year
        m_year = year_pattern.match(line)
        if m_year:
            save_current_problem()
            current_year = m_year.group(1).strip()
            current_part = ""
            current_problem_title = ""
            current_context = []
            current_questions = []
            continue

        # Check Part
        m_part = part_pattern.match(line)
        if m_part:
            # Usually part changes before problem, so save previous problem
            save_current_problem()
            current_part = m_part.group(1).strip()
            current_problem_title = ""
            current_context = []
            current_questions = []
            continue

        # Check Problem Title
        # Format: **[문제 1] ...**
        if line_stripped.startswith("**[문제") and line_stripped.endswith("**"):
            save_current_problem()
            # Extract content
            current_problem_title = line_stripped.strip("*")
            current_context = []
            current_questions = []
            continue
            
        # Check Questions
        m_q = question_line_pattern.match(line)
        if m_q:
            # Found a question
            q_text = m_q.group(1).strip()
            # In case the regex didn't capture full line if it's complex, mainly we want the text
            # But wait, looking at file content: * **질문 1**: ...
            # The regex ^\*\s+\*\*질문 should match.
            current_questions.append(line_stripped.replace("* **", "").replace("**:", ":").lstrip("* "))
            continue
            
        # Context (lines starting with >)
        if line_stripped.startswith(">"):
            current_context.append(line) # keep line for now, clean later
        elif current_problem_title:
            # If we are in a problem block, non-empty lines might be context continuations 
            # or spaces. If it's a list item not matched by question pattern?
            # looking at file, questions are bullets.
            pass

    # Save last
    save_current_problem()

    return questions_db

def write_questions_py(db, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("QUESTIONS = {\n")
        for key, data in db.items():
            # Use repr for safe string encoding/escaping
            f.write(f'    "{key}": {{\n')
            f.write(f'        "title": {repr(data["title"])},\n')
            f.write(f'        "context": """{data["context"]}""",\n')
            f.write(f'        "questions": [\n')
            for q in data["questions"]:
                f.write(f'            {repr(q)},\n')
            f.write(f'        ],\n')
            f.write(f'        "key_points": [\n')
            for kp in data["key_points"]:
                f.write(f'            {repr(kp)},\n')
            f.write(f'        ]\n')
            f.write(f'    }},\n')
        f.write("}\n")

if __name__ == "__main__":
    base_dir = r"c:\Users\hyoun\Projects\med_interview_bot"
    md_path = os.path.join(base_dir, "problem.md")
    py_path = os.path.join(base_dir, "questions.py")
    
    db = parse_markdown(md_path)
    if db:
        write_questions_py(db, py_path)
        print(f"Successfully updated questions.py with {len(db)} problems.")
    else:
        print("No questions found or error parsing.")
