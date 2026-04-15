import requests
import json

class OllamaClient:
    def __init__(self, model="richardyoung/qwen3-14b-abliterated:Q5_K_M", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = f"{base_url}/api/generate"

    def prompt(self, system_prompt: str, user_prompt: str):
        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }
        try:
            response = requests.post(self.base_url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json().get("response", "Error: No response content")
        except Exception as e:
            return f"Error connecting to Ollama: {str(e)}"

    def prompt_structured(self, system_prompt: str, user_prompt: str):
        """Helper to encourage key-value pair output if needed."""
        # Add hint for key-value structure
        user_prompt += "\n\nPlease format your response as a clear list of [KEY]: Value pairs."
        return self.prompt(system_prompt, user_prompt)
