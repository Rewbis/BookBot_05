import json
import re

def clean_json_v1(text: str):
    """The current buggy version."""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = text.split("</think>")[-1]
    try:
        candidates = re.findall(r'(\{.*?\})', text, re.DOTALL)
        for cand in reversed(candidates):
            try:
                return json.loads(cand)
            except:
                continue
        match = re.search(r'(\{.*\})', text, re.dotall) # Note: search is greedy by default if not ?
        if match:
            return json.loads(match.group(0))
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}

def clean_json_v2(text: str):
    """The proposed fix."""
    # Remove thinking tags
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # Try greedy matching for the outermost braces
    # Using [^{]* to find first { and [^}]* to find last } is risky if text around is complex
    # Better: find the first '{' and the last '}'
    start = text.find('{')
    end = text.rfind('}')
    
    if start != -1 and end != -1 and end > start:
        json_str = text[start:end+1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # If greedy failed, maybe there's extra stuff, try to fix common issues
            pass
            
    # Fallback: existing logic but improved
    try:
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(text)
    except Exception as e:
        return {"error": f"JSON Parse Error: {str(e)}", "raw": text}

# Test Cases
test_nested = """
Here is the result:
{
  "chapters": [
    {"num": 1, "title": "A"},
    {"num": 2, "title": "B"}
  ]
}
"""

print("--- Testing Nested JSON ---")
v1_res = clean_json_v1(test_nested)
print(f"V1 (Buggy) detected: {v1_res.get('num', 'FULL LIST' if 'chapters' in v1_res else 'FAILED')}")

v2_res = clean_json_v2(test_nested)
print(f"V2 (Fixed) detected chapters count: {len(v2_res.get('chapters', []))}")
print(f"V2 result: {v2_res}")

test_with_garbage = """
Some thinking here <think> blabla </think>
{ "ok": true }
Footer stuff
"""
print("\n--- Testing Garbage ---")
print(f"V2 result: {clean_json_v2(test_with_garbage)}")
