
import os
import sys

# Try to find API Key from environment or secrets
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    # Try loading from secrets.toml if streamlit is installed
    try:
        import toml
        secrets_path = os.path.join(".streamlit", "secrets.toml")
        if os.path.exists(secrets_path):
            with open(secrets_path, "r", encoding="utf-8") as f:
                secrets = toml.load(f)
                api_key = secrets.get("OPENAI_API_KEY")
    except ImportError:
        pass

if not api_key:
    print("Error: OPENAI_API_KEY not found in environment or .streamlit/secrets.toml")
    print("Please set the environment variable or ensure secrets.toml exists.")
    sys.exit(1)

from llm_manager import generate_dynamic_question

def test_generation():
    topic = "의료 소송과 방어 진료"
    print(f"Generating question for topic: {topic}...")
    print("This may take 30-60 seconds...")
    
    result = generate_dynamic_question(api_key, topic)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print("\n" + "="*50)
    print(f"TITLE: {result.get('title')}")
    print("="*50)
    
    context = result.get('context', '')
    print(f"\nCONTEXT LENGTH: {len(context)} chars")
    print("-" * 20)
    print(context[:500] + "\n... (omitted) ...\n" + context[-200:])
    print("-" * 20)
    
    print("\nQUESTIONS:")
    for q in result.get('questions', []):
        print(f" - {q}")
        
    print("\nKEY POINTS:")
    for k in result.get('key_points', []):
        print(f" - {k}")

    if len(context) > 800:
        print("\n✅ PASS: Context length is sufficient (> 800 chars).")
    else:
        print("\n⚠️ WARNING: Context length might be too short.")

if __name__ == "__main__":
    test_generation()
