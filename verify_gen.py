
import os
import sys

# Try to find API Key from environment or secrets
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    # Try loading from secrets.toml
    try:
        import tomllib # Python 3.11+
        with open(os.path.join(".streamlit", "secrets.toml"), "rb") as f:
            secrets = tomllib.load(f)
            api_key = secrets.get("OPENAI_API_KEY")
    except ImportError:
        try:
            import toml
            with open(os.path.join(".streamlit", "secrets.toml"), "r", encoding="utf-8") as f:
                secrets = toml.load(f)
                api_key = secrets.get("OPENAI_API_KEY")
        except ImportError:
            pass
    except FileNotFoundError:
        pass

if not api_key:
    print("Error: OPENAI_API_KEY not found in environment or .streamlit/secrets.toml")
    print("Please set the environment variable or ensure secrets.toml exists.")
    sys.exit(1)

from llm_manager import generate_dynamic_question

def test_generation():
    # Test 1: Science Mode
    topic_science = "CRISPR 유전자 가위의 부작용"
    print(f"\n[Test 1] Generating SCIENCE question for: {topic_science}...")
    result_science = generate_dynamic_question(api_key, topic_science, mode="science")
    print_result(result_science)

    # Test 2: Ethics Mode
    topic_ethics = "안락사 허용 논란"
    print(f"\n[Test 2] Generating ETHICS question for: {topic_ethics}...")
    result_ethics = generate_dynamic_question(api_key, topic_ethics, mode="ethics")
    print_result(result_ethics)

def print_result(result):
    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print("\n" + "="*50)
    print(f"TITLE: {result.get('title')}")
    print("="*50)
    
    context = result.get('context', '')
    print(f"\nCONTEXT LENGTH: {len(context)} chars")
    print("-" * 20)
    print(context[:300] + "\n... (omitted) ...\n" + context[-300:])
    print("-" * 20)
    
    print("\nQUESTIONS:")
    for q in result.get('questions', []):
        print(f" - {q}")
        
    if len(context) > 800:
        print("\n✅ PASS: Context length is sufficient.")
    else:
        print("\n⚠️ WARNING: Context length might be too short.")

if __name__ == "__main__":
    test_generation()
