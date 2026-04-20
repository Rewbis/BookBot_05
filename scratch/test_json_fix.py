import json
import re

def _try_parse(json_str: str):
    """Helper to try parsing and repairing a candidate JSON string."""
    try:
        # Stage 1: Normalize braces and quotes
        json_str = json_str.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
        
        # Stage 2: Fixed trailing commas in objects and arrays
        json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
        
        # Stage 3: Initial Parse
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Stage 4: Targeted Repair (Single to Double Quotes for Keys)
            repaired = re.sub(r"'([^']*)'\s*:", r'"\1":', json_str)
            repaired = repaired.replace('True', 'true').replace('False', 'false').replace('None', 'null')
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                return None
    except Exception:
        return None

def clean_json(text: str):
    if not text:
        return {"error": "Empty response"}

    # 1. Aggressive Noise Removal
    text = re.sub(r'<(think|thought|reasoning|thinking)>.*?</\1>', '', text, flags=re.DOTALL | re.IGNORECASE)
    if "</think>" in text: text = text.split("</think>", 1)[1]
    if "</thought>" in text: text = text.split("</thought>", 1)[1]
    if "</reasoning>" in text: text = text.split("</reasoning>", 1)[1]
    
    # 2. Try Markdown blocks
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        candidate = match.group(1)
        parsed = _try_parse(candidate)
        if parsed: return parsed

    # 3. Smart Search (Reverse order)
    potential_starts = [m.start() for m in re.finditer(r'\{', text)]
    for start in reversed(potential_starts):
        if re.match(r'\{\s*(?:"|\})', text[start:]):
            end = text.rfind('}')
            if end > start:
                candidate = text[start:end+1]
                parsed = _try_parse(candidate)
                if parsed: return parsed

    # 4. Final Hail Mary
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end > start:
        candidate = text[start:end+1]
        parsed = _try_parse(candidate)
        if parsed: return parsed

    return {"error": "No valid JSON found"}

# --- TEST CASES FROM DEBUG LOG ---

test_cases = [
    {
        "name": "Unpaired </think> and conversational braces",
        "text": """
Okay, let's start by understanding the user's query. They want a 10-chapter skeleton...
Check for the required keys: chapter_number, title, summary. Make sure the JSON starts with { and ends with }, proper commas, etc.
</think>

{
  "chapters": [
    {"chapter_number": 1, "title": "A New Home in London", "summary": "Description..."}
  ]
}
"""
    },
    {
        "name": "Multiple JSON blocks and </think> garbage",
        "text": """
, the JSON output is:

{
  "title": "Block 1"
}

</think>

{
  "title": "Block 2"
}
"""
    },
    {
        "name": "Conversational commentary with braces",
        "text": "The response should be { \"key\": \"val\" } and not anything else."
    }
]

for tc in test_cases:
    print(f"--- Testing: {tc['name']} ---")
    result = clean_json(tc['text'])
    print(f"Result: {result}")
    if "error" in result:
        print(f"FAILED: {result['error']}")
    else:
        print("SUCCESS")
    print("-" * 40)
